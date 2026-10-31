# 🕌 Daily Namaz Timings Bot

A lightweight Telegram bot that automatically sends daily Islamic prayer timings for your selected location in India. Built with Python, the AlAdhan Prayer Times API, and GitHub Actions.

Receive your daily prayer schedule directly on Telegram without installing an additional app or running a server 24/7.

## ✨ Features

- 🕌 **Five Daily Prayers** — Fajr, Dhuhr, Asr, Maghrib, and Isha.
- 🌅 **Sunrise Timing** — Includes sunrise alongside the prayer schedule.
- 🌙 **Islamic Calendar** — Displays the Hijri date for the requested day.
- 📍 **Location-Based Timings** — Fetches prayer timings for your selected city.
- 🕛 **Automated Daily Notifications** — Sends the upcoming day's schedule at midnight Indian Standard Time.
- 🧭 **Flexible Location** — Designed to support changing locations when travelling.
- 🕋 **Shafi Asr Calculation** — Uses the Shafi school preference for Asr timings.
- ⚙️ **Automated Execution** — Runs through GitHub Actions without requiring a continuously running server.
- 💸 **Low-Cost Hosting** — Designed to operate within GitHub Actions' free usage allowance.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| AlAdhan Prayer Times API | Prayer timings and Hijri dates |
| Telegram Bot API | Message delivery |
| GitHub Actions | Scheduled execution |
| GitHub Secrets & Variables | Secure credentials and configuration |

## 📁 Project Structure

```text
daily-namaz-bot/
├── .github/
│   └── workflows/
│       └── daily-namaz.yml
├── bot.py
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`.
3. Choose a display name and a unique username.
4. Copy the bot token provided by BotFather.
5. Open your new bot and press **Start**.

Keep your bot token private.

### 2. Get Your Telegram Chat ID

After starting your bot, open the following URL in your browser, replacing `YOUR_BOT_TOKEN` with your actual token:

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

Find the `chat.id` field in the JSON response and copy its numeric value.

Your bot must receive a message from you before your chat ID appears in the updates.

### 3. Create a GitHub Repository

Create a repository on [GitHub](https://github.com/new).

You can use the name:

```text
daily-namaz-bot
```

Upload the project files using the directory structure shown above.

### 4. Install Dependencies

The project uses Python and the `requests` library.

Add the following to `requirements.txt`:

```text
requests
```

To run the script locally, install the dependency:

```bash
pip install -r requirements.txt
```

### 5. Configure GitHub Secrets

Navigate to:

**Repository → Settings → Secrets and variables → Actions → Secrets**

Add the following repository secrets:

| Secret | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token obtained from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

Never hardcode these credentials into your Python script or commit them to your repository.

### 6. Configure GitHub Variables

Navigate to:

**Repository → Settings → Secrets and variables → Actions → Variables**

Add the following variables:

| Variable | Example | Description |
|---|---|---|
| `CITY` | `Uppala` | Selected city |
| `STATE` | `Kerala` | State or region |
| `COUNTRY` | `India` | Country |
| `CALCULATION_METHOD` | `1` | AlAdhan calculation method |
| `ASR_SCHOOL` | `0` | Shafi Asr calculation preference |

**Default location:** Uppala, Kerala, India.

The Python script must pass the state parameter to the API and read these variables for the configuration to take effect.

### 7. Configure GitHub Actions

The workflow file is located at:

```text
.github/workflows/daily-namaz.yml
```

The scheduled workflow is configured to run daily at:

```text
30 18 * * *
```

GitHub Actions interprets cron schedules in UTC. This corresponds to midnight Indian Standard Time (IST).

GitHub-hosted runners execute the script automatically, so your personal computer does not need to remain switched on.

Scheduled executions can occasionally be delayed.

## 📩 Example Notification

The bot sends a message similar to the following:

```text
🕌 Daily Namaz Timings

🌙 Islamic Date: [Hijri date]
📅 [Day, Date, Month, Year]
📍 Uppala, Kerala, India

━━━━━━━━━━━━━━

🌅 Fajr: [Prayer time]

☀️ Sunrise: [Sunrise time]

🌤️ Dhuhr: [Prayer time]

🌇 Asr: [Prayer time]

🌆 Maghrib: [Prayer time]

🌙 Isha: [Prayer time]

━━━━━━━━━━━━━━
```

The actual date and prayer timings are retrieved from the API.

## 🧭 Location Configuration

The bot is designed to support different locations when travelling.

For example:

- Uppala, Kerala
- Kasaragod, Kerala
- Kozhikode, Kerala
- Bengaluru, Karnataka
- Mysuru, Karnataka

The current configuration can be changed through GitHub repository variables.

**Planned enhancement:** Add Telegram commands such as `/setcity`, allowing the user to change locations directly through Telegram. The selected location will need persistent storage so scheduled GitHub Actions runs can retrieve it.

Location changes should be validated against the prayer-times API before being saved.

## 🕋 Prayer-Time Calculation

Prayer timings are provided by the [AlAdhan Prayer Times API](https://aladhan.com/prayer-times-api).

The application requests the schedule for the selected location and date.

The configuration distinguishes between:

- **Calculation method:** Determines the prayer-time calculation convention.
- **Asr school:** Controls the Shafi or Hanafi preference for calculating Asr.

The project uses the Shafi preference for Asr calculations.

Prayer times can vary between calculation methods and local mosque timetables. Verify the configured method and compare the output with a trusted local timetable before relying on the notifications.

Hijri dates may also differ from locally observed Islamic calendar dates.

## 🧪 Testing

To test the bot without waiting for midnight:

1. Open your repository on GitHub.
2. Navigate to the **Actions** tab.
3. Select the **Daily Namaz Timings** workflow.
4. Click **Run workflow**.
5. Open the workflow run and inspect the logs.
6. Check your Telegram chat for the notification.

The workflow must include the `workflow_dispatch` trigger for manual execution.

A manual test sends a real Telegram message.

## 🔐 Security

- Store credentials in GitHub Secrets.
- Never publish your Telegram bot token.
- Avoid printing tokens in workflow logs.
- Grant the workflow only the permissions it needs.
- If a token is exposed, revoke it through BotFather and configure the replacement securely.

## 💰 Cost

The project is designed to run within GitHub Actions' free usage allowance, subject to GitHub's current quotas and account limits.

No continuously running server or database is required for the basic scheduled notification workflow.

Persistent storage will be needed if you implement Telegram-controlled location changes.

## 🗺️ Roadmap

- [x] Fetch prayer timings from an API.
- [x] Include the Hijri date in the message.
- [x] Format each prayer on a separate line.
- [x] Schedule daily notifications through GitHub Actions.
- [x] Support Shafi Asr calculations.
- [ ] Add `/start` and `/help` commands.
- [ ] Add `/today` and `/tomorrow` commands.
- [ ] Add `/location` to display the selected city.
- [ ] Add `/setcity` to change locations through Telegram.
- [ ] Validate new locations before saving them.
- [ ] Persist location settings across workflow runs.
- [ ] Add optional prayer-time reminders.

## 📚 Resources

- [AlAdhan Prayer Times API](https://aladhan.com/prayer-times-api)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram BotFather](https://t.me/BotFather)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

---

**Built to make daily prayer schedules simple, accessible, and automated.** 🕌
