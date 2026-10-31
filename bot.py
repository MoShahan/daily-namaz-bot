import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


API_URL = "https://api.aladhan.com/v1/timingsByCity"
TELEGRAM_URL = "https://api.telegram.org"


def format_time(time_string):
    time_string = time_string.split()[0]
    return datetime.strptime(
        time_string, "%H:%M"
    ).strftime("%I:%M %p").lstrip("0")


def main():
    city = os.environ["CITY"]
    country = os.environ.get("COUNTRY", "India")
    method = os.environ.get("CALCULATION_METHOD", "1")

    # AlAdhan: 0 = Shafi, 1 = Hanafi.
    school = "0"

    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    india_time = datetime.now(ZoneInfo("Asia/Kolkata"))
    target_date = india_time.date() + timedelta(days=1)
    api_date = target_date.strftime("%d-%m-%Y")

    response = requests.get(
        f"{API_URL}/{api_date}",
        params={
            "city": city,
            "country": country,
            "method": method,
            "school": school,
        },
        timeout=20,
    )
    response.raise_for_status()

    result = response.json()

    if result.get("code") != 200:
        raise RuntimeError(f"Prayer API error: {result}")

    data = result["data"]
    timings = data["timings"]

    hijri = data["date"]["hijri"]
    hijri_date = (
        f"{hijri['day']} {hijri['month']['en']} "
        f"{hijri['year']} AH"
    )

    readable_date = target_date.strftime("%A, %d %B %Y")

    prayers = [
        ("🌅", "Fajr", timings["Fajr"]),
        ("☀️", "Sunrise", timings["Sunrise"]),
        ("🌤️", "Dhuhr", timings["Dhuhr"]),
        ("🌇", "Asr", timings["Asr"]),
        ("🌆", "Maghrib", timings["Maghrib"]),
        ("🌙", "Isha", timings["Isha"]),
    ]

    lines = [
        "🕌 <b>Daily Namaz Timings</b>",
        "",
        f"🌙 <b>Islamic Date:</b> {hijri_date}",
        f"📅 {readable_date}",
        f"📍 {city}, {country}",
        "",
        "━━━━━━━━━━━━━━",
        "",
    ]

    for emoji, name, time_value in prayers:
        lines.append(
            f"{emoji} <b>{name}:</b> {format_time(time_value)}"
        )

    lines.extend([
        "",
        "━━━━━━━━━━━━━━",
    ])

    message = "\n".join(lines)

    telegram_response = requests.post(
        f"{TELEGRAM_URL}/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    telegram_response.raise_for_status()

    telegram_data = telegram_response.json()

    if not telegram_data.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {telegram_data}"
        )

    print(
        f"Prayer timings sent for {target_date} "
        f"in {city}, {country}."
    )


if __name__ == "__main__":
    main()
