
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# -------------------------
# Configuration
# -------------------------

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])

TIMEZONE = ZoneInfo("Asia/Kolkata")
LOCATION_FILE = Path("location.json")

CALCULATION_METHOD = os.getenv("CALCULATION_METHOD", "1")
ASR_SCHOOL = os.getenv("ASR_SCHOOL", "0")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
ALADHAN_API = "https://api.aladhan.com/v1/timingsByCity"


# -------------------------
# HTTP session with retries
# -------------------------

def create_aladhan_session():
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


aladhan_session = create_aladhan_session()


# -------------------------
# Location state
# -------------------------

def load_state():
    if LOCATION_FILE.exists():
        with LOCATION_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    return {
        "city": os.getenv("CITY", "Uppala"),
        "state": os.getenv("STATE", "Kerala"),
        "country": os.getenv("COUNTRY", "India"),
        "last_update_id": None,
    }


def save_state(state):
    with LOCATION_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, ensure_ascii=False)
        file.write("\n")


# -------------------------
# Telegram helpers
# -------------------------

def telegram_request(method, payload=None):
    response = requests.post(
        f"{TELEGRAM_API}/{method}",
        json=payload or {},
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {result.get('description', 'Unknown error')}"
        )

    return result["result"]


def send_message(text):
    telegram_request(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        },
    )


def get_pending_updates(last_update_id):
    payload = {
        "timeout": 0,
        "allowed_updates": ["message"],
    }

    if last_update_id is not None:
        payload["offset"] = int(last_update_id) + 1

    return telegram_request("getUpdates", payload)


# -------------------------
# Prayer timings
# -------------------------

def fetch_prayer_data(location, target_date):
    date_string = target_date.strftime("%d-%m-%Y")

    params = {
        "city": location["city"],
        "state": location["state"],
        "country": location["country"],
        "method": CALCULATION_METHOD,
        "school": ASR_SCHOOL,
    }

    print(
        f"Fetching prayer timings for "
        f"{location['city']}, {location['state']}, "
        f"{location['country']} on {date_string}"
    )

    response = aladhan_session.get(
        f"{ALADHAN_API}/{date_string}",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if result.get("code") != 200 or not result.get("data"):
        raise ValueError(
            f"AlAdhan API returned an invalid response: "
            f"{result.get('status', {}).get('message', 'Unknown error')}"
        )

    data = result["data"]

    if not data.get("timings"):
        raise ValueError("The API did not return prayer timings.")

    return data


def validate_location(location):
    today = datetime.now(TIMEZONE).date()
    fetch_prayer_data(location, today)


def format_time(value):
    match = re.search(r"\b\d{2}:\d{2}\b", str(value))

    if not match:
        raise ValueError(f"Unexpected prayer time format: {value}")

    return match.group(0)


def format_12_hour(value):
    time_24 = format_time(value)

    return datetime.strptime(
        time_24, "%H:%M"
    ).strftime("%I:%M %p").lstrip("0")


def format_prayer_message(location, target_date, data):
    hijri = data["date"]["hijri"]

    hijri_date = (
        f"{hijri['day']} {hijri['month']['en']} {hijri['year']}"
    )

    gregorian_date = target_date.strftime("%d %B %Y")
    city = location["city"]

    timings = data["timings"]

    lines = [
        f"🕌 *Daily Namaz Timings ({city})*",
        "",
        f"{gregorian_date} - {hijri_date}",
        "",
        f"*Fajr:* {format_12_hour(timings['Fajr'])}",
        f"*Sunrise:* {format_12_hour(timings['Sunrise'])}",
        f"*Dhuhr:* {format_12_hour(timings['Dhuhr'])}",
        f"*Asr:* {format_12_hour(timings['Asr'])}",
        f"*Maghrib:* {format_12_hour(timings['Maghrib'])}",
        f"*Isha:* {format_12_hour(timings['Isha'])}",
    ]

    return "\n".join(lines)


# -------------------------
# Process /setcity commands
# -------------------------

def process_commands(state):
    updates = get_pending_updates(state.get("last_update_id"))

    if not updates:
        return state, []

    notifications = []

    for update in updates:
        update_id = update["update_id"]

        current_id = state.get("last_update_id")

        if current_id is None or update_id > current_id:
            state["last_update_id"] = update_id

        message = update.get("message", {})

        sender_chat_id = str(
            message.get("chat", {}).get("id", "")
        )

        # Only accept commands from the configured chat.
        if sender_chat_id != CHAT_ID:
            continue

        message_text = message.get("text", "").strip()

        if not message_text:
            continue

        command_parts = message_text.split(maxsplit=1)
        command = command_parts[0].split("@")[0].lower()

        if command != "/setcity":
            continue

        if len(command_parts) < 2:
            notifications.append(
                "Usage:\n"
                "/setcity City, State, Country\n\n"
                "Example:\n"
                "/setcity Kochi, Kerala, India"
            )
            continue

        parts = [
            part.strip()
            for part in command_parts[1].split(",")
        ]

        if len(parts) != 3 or not all(parts):
            notifications.append(
                "❌ Invalid location format.\n\n"
                "Use:\n"
                "/setcity City, State, Country\n\n"
                "Example:\n"
                "/setcity Uppala, Kerala, India"
            )
            continue

        new_location = {
            "city": parts[0],
            "state": parts[1],
            "country": parts[2],
        }

        try:
            validate_location(new_location)

        except (requests.RequestException, ValueError) as error:
            print(f"Location validation failed: {error}")

            notifications.append(
                "❌ Could not validate this location:\n"
                f"{parts[0]}, {parts[1]}, {parts[2]}\n\n"
                "Please check the spelling and try again."
            )
            continue

        # Latest valid command wins.
        state.update(new_location)

        notifications.append(
            "✅ Prayer location updated!\n\n"
            f"📍 {state['city']}, {state['state']}, "
            f"{state['country']}\n\n"
            "Your daily Namaz timings will use this location."
        )

    save_state(state)

    return state, notifications


# -------------------------
# Main
# -------------------------

def main():
    state = load_state()

    # 1. Process pending Telegram commands.
    state, notifications = process_commands(state)

    # 2. Send command responses.
    for notification in notifications:
        send_message(notification)

    # 3. Get TODAY'S date in Indian time.
    today = datetime.now(TIMEZONE).date()

    print(f"Today's date in IST: {today}")

    # 4. Fetch TODAY'S prayer timings.
    data = fetch_prayer_data(state, today)

    # 5. Format the message.
    message = format_prayer_message(
        state,
        today,
        data,
    )

    # 6. Send timings.
    send_message(message)

    print(
        f"Successfully sent Namaz timings for {today} "
        f"in {state['city']}, {state['state']}, "
        f"{state['country']}."
    )


if __name__ == "__main__":
    main()
