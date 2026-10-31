import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =====================================================
# CONFIGURATION
# =====================================================

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])

TIMEZONE = ZoneInfo("Asia/Kolkata")

LOCATION_FILE = Path("location.json")

# Calculation settings
CALCULATION_METHOD = os.getenv("CALCULATION_METHOD", "1")
ASR_SCHOOL = os.getenv("ASR_SCHOOL", "0")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

ALADHAN_API = "https://api.aladhan.com/v1"

GEOCODING_API = (
    "https://geocoding-api.open-meteo.com/v1/search"
)


# =====================================================
# HTTP SESSION WITH RETRIES
# =====================================================

def create_session():
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


http = create_session()


# =====================================================
# LOCATION STATE
# =====================================================

def load_state():
    if LOCATION_FILE.exists():
        with LOCATION_FILE.open(
            "r", encoding="utf-8"
        ) as file:
            state = json.load(file)

        return state

    return {
        "city": "Uppala",
        "state": "Kerala",
        "country": "India",
        "latitude": 12.684361,
        "longitude": 74.900682,
        "last_update_id": None,
    }


def save_state(state):
    with LOCATION_FILE.open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write("\n")


# =====================================================
# TELEGRAM HELPERS
# =====================================================

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
            f"Telegram API error: "
            f"{result.get('description', 'Unknown error')}"
        )

    return result["result"]


def send_message(message):
    telegram_request(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": message,
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

    return telegram_request(
        "getUpdates",
        payload,
    )


# =====================================================
# CITY COORDINATE LOOKUP
# =====================================================

def get_coordinates(city, state, country):
    print(
        f"Looking up coordinates for "
        f"{city}, {state}, {country}"
    )

    response = http.get(
        GEOCODING_API,
        params={
            "name": city,
            "count": 10,
            "language": "en",
            "format": "json",
        },
        timeout=30,
    )

    response.raise_for_status()

    results = response.json().get("results", [])

    for result in results:
        result_country = result.get(
            "country", ""
        ).lower()

        result_state = result.get(
            "admin1", ""
        ).lower()

        if (
            result_country == country.lower()
            and result_state == state.lower()
        ):
            coordinates = {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
            }

            print(f"Coordinates found: {coordinates}")

            return coordinates

    raise ValueError(
        f"Could not find coordinates for "
        f"{city}, {state}, {country}"
    )


# =====================================================
# PRAYER TIMINGS API
# =====================================================

def fetch_prayer_data(location, target_date):
    date_string = target_date.strftime("%d-%m-%Y")

    url = (
        f"{ALADHAN_API}/timings/{date_string}"
    )

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "method": CALCULATION_METHOD,
        "school": ASR_SCHOOL,
        "timezonestring": "Asia/Kolkata",
    }

    print(
        f"Fetching prayer timings for "
        f"{location['city']}, "
        f"{location['state']}, "
        f"{location['country']} "
        f"on {date_string}"
    )

    for attempt in range(1, 6):
        try:
            response = http.get(
                url,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

            result = response.json()

            if (
                result.get("code") != 200
                or not result.get("data")
            ):
                raise ValueError(
                    "Invalid AlAdhan API response"
                )

            data = result["data"]

            if not data.get("timings"):
                raise ValueError(
                    "Prayer timings missing from API response"
                )

            print(
                f"Prayer timings fetched successfully "
                f"on attempt {attempt}"
            )

            return data

        except (
            requests.RequestException,
            ValueError,
        ) as error:

            print(
                f"Attempt {attempt}/5 failed: {error}"
            )

            if attempt == 5:
                raise RuntimeError(
                    "Unable to retrieve prayer timings "
                    "after multiple attempts. "
                    "AlAdhan may be temporarily unavailable."
                ) from error

            time.sleep(attempt * 10)


def validate_location(location):
    today = datetime.now(TIMEZONE).date()

    fetch_prayer_data(location, today)


# =====================================================
# TIME FORMATTING
# =====================================================

def format_time(value):
    match = re.search(
        r"\b\d{2}:\d{2}\b",
        str(value),
    )

    if not match:
        raise ValueError(
            f"Unexpected prayer time format: {value}"
        )

    return match.group(0)


def format_12_hour(value):
    time_24 = format_time(value)

    return datetime.strptime(
        time_24,
        "%H:%M",
    ).strftime(
        "%I:%M %p"
    ).lstrip("0")


# =====================================================
# TELEGRAM MESSAGE FORMATTING
# =====================================================

def format_prayer_message(
    location,
    target_date,
    data,
):
    hijri = data["date"]["hijri"]

    hijri_date = (
        f"{hijri['day']} "
        f"{hijri['month']['en']} "
        f"{hijri['year']}"
    )

    gregorian_date = target_date.strftime(
        "%d %B %Y"
    )

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


# =====================================================
# PROCESS /SETCITY COMMANDS
# =====================================================

def process_commands(state):
    updates = get_pending_updates(
        state.get("last_update_id")
    )

    if not updates:
        print("No pending Telegram commands.")
        return state, []

    notifications = []

    for update in updates:

        update_id = update["update_id"]

        current_id = state.get("last_update_id")

        if (
            current_id is None
            or update_id > current_id
        ):
            state["last_update_id"] = update_id

        message = update.get("message", {})

        sender_chat_id = str(
            message.get("chat", {}).get("id", "")
        )

        # Only accept commands from the configured chat.
        if sender_chat_id != CHAT_ID:
            continue

        message_text = message.get(
            "text", ""
        ).strip()

        if not message_text:
            continue

        command_parts = message_text.split(
            maxsplit=1
        )

        command = (
            command_parts[0]
            .split("@")[0]
            .lower()
        )

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
            # Find the new city's coordinates.
            coordinates = get_coordinates(
                new_location["city"],
                new_location["state"],
                new_location["country"],
            )

            new_location.update(coordinates)

            # Validate the new location with AlAdhan.
            validate_location(new_location)

        except (
            requests.RequestException,
            ValueError,
            RuntimeError,
        ) as error:

            print(
                f"Location validation failed: {error}"
            )

            notifications.append(
                "❌ Could not validate this location.\n\n"
                "Please check the city, state and country "
                "and try again."
            )

            continue

        # Latest valid command wins.
        state.update(new_location)

        notifications.append(
            "✅ Prayer location updated!\n\n"
            f"📍 {state['city']}, "
            f"{state['state']}, "
            f"{state['country']}\n\n"
            "Your daily Namaz timings will use "
            "this location."
        )

    # Save location and update ID.
    save_state(state)

    return state, notifications


# =====================================================
# MAIN
# =====================================================

def main():

    print("Starting Daily Namaz Timings Bot...")

    # 1. Load saved location.
    state = load_state()

    # 2. Process pending Telegram commands.
    state, notifications = process_commands(state)

    # 3. Send command responses.
    for notification in notifications:
        send_message(notification)

    # 4. Get today's date in Indian time.
    today = datetime.now(TIMEZONE).date()

    print(f"Today's date in IST: {today}")

    # 5. Fetch today's prayer timings.
    data = fetch_prayer_data(
        state,
        today,
    )

    # 6. Format the Telegram message.
    message = format_prayer_message(
        state,
        today,
        data,
    )

    # 7. Send timings.
    send_message(message)

    print(
        f"Successfully sent Namaz timings for {today} "
        f"in {state['city']}, "
        f"{state['state']}, "
        f"{state['country']}."
    )


if __name__ == "__main__":
    main()
