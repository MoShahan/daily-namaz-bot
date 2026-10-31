# 🕌 Daily Namaz Timings Bot

A lightweight Telegram bot that automatically sends daily Islamic prayer timings to your Telegram chat. Built with Python, powered by the AlAdhan Prayer Times API, and automated using GitHub Actions.

The bot fetches prayer timings for a configured location and delivers them every day at **12:01 AM IST**, so the day's prayer schedule is ready at the beginning of the day.

## ✨ Features

- **Daily Prayer Timings:** Automatically sends the six daily timings:
  - Fajr
  - Sunrise
  - Dhuhr
  - Asr
  - Maghrib
  - Isha
- **Automated Scheduling:** Runs every day at 12:01 AM Indian Standard Time using GitHub Actions.
- **Location Support:** Supports changing the location directly through Telegram using the `/setcity` command.
- **Automatic Location Detection:** Uses Open-Meteo Geocoding API to resolve a city, state, and country into geographical coordinates.
- **Dynamic Prayer Calculations:** Fetches prayer timings based on the configured geographical coordinates and calculation settings.
- **Hijri Date:** Includes the corresponding Hijri date in the daily message.
- **Telegram Formatting:** Uses a clean, readable Markdown-formatted message.
- **Persistent Location:** Saves the selected location and Telegram update tracking information in `location.json`, committed back to the repository.
- **Retry Handling:** Retries temporary API failures when fetching prayer timings.

## 📍 Changing the Location

The bot supports changing its location directly through Telegram.

Use the following command:

`/setcity City, State, Country`

Example:

`/setcity Kochi, Kerala, India`

The bot resolves the location, validates it, and saves the updated geographical coordinates. The latest valid location command is used.

For security, location changes are accepted only from the Telegram chat configured in the repository secrets.

## 🕒 Scheduling

The bot runs daily at:

**12:01 AM IST**

GitHub Actions uses the following UTC cron expression:

`31 18 * * *`

The workflow can also be triggered manually through GitHub Actions.

## 🧮 Prayer Time Configuration

The project currently uses the following calculation settings:

| Setting | Value |
|---|---|
| Calculation method | Karachi (1) |
| Asr school | Shafi (0) |
| Timezone | Asia/Kolkata |
| Prayer time provider | AlAdhan API |

Prayer timings are calculated using the configured method and geographical coordinates. They may differ from the official Azan schedule followed by an individual local mosque.

## 🛠️ Technology Stack

- **Python** – Main bot implementation.
- **Telegram Bot API** – Sends messages and receives location commands.
- **AlAdhan API** – Provides prayer timings and Hijri dates.
- **Open-Meteo Geocoding API** – Resolves city names into geographical coordinates.
- **GitHub Actions** – Runs the bot automatically on a daily schedule.
- **GitHub Repository** – Stores the source code and persistent location configuration.

## 📂 Project Structure

```text
daily-namaz-bot/
│
├── .github/
│   └── workflows/
│       └── daily-namaz.yml
│
├── bot.py
├── location.json
├── requirements.txt
├── README.md
└── SETUP.md
```

## 📖 Documentation

Want to create your own version of this bot?

Check out the **[Setup and Recreation Guide](SETUP.md)** for instructions covering:

- Creating a Telegram bot using BotFather.
- Setting up a GitHub repository.
- Configuring GitHub Actions and repository secrets.
- Connecting Telegram and prayer-time APIs.
- Configuring locations and prayer calculation methods.
- Running and troubleshooting the bot.

## ⚠️ Notes

- Prayer timings depend on the selected calculation method and location coordinates.
- The bot currently relies on the AlAdhan API for prayer timings. Retries are implemented for temporary failures, but there is no independent offline calculation fallback.
- Telegram commands are processed when the GitHub Actions workflow runs. This is not a continuously running Telegram bot.
- The repository must have GitHub Actions write permission enabled for the workflow to commit updated location state.

---

Built with Python and GitHub Actions. 🕌
