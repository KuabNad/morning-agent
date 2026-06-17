# Morning Agent

Morning Agent is a small Python assistant that builds a warm daily digest and sends it to Telegram. It is designed to run every day from GitHub Actions at 09:00 Canary Islands time, with email backup and OpenAI polishing available as optional extras.

The digest includes:

- today's calendar status
- Tenerife weather
- short news sections
- suggested priorities
- a short reflection

It starts with:

```text
Good morning Kuba 👋
```

## Run Locally

1. Create a virtual environment:

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

4. Fill in any credentials you want to use. The app works without credentials and will print the digest to the terminal.

5. Run it:

   ```bash
   python main.py
   ```

## Telegram Setup

### Create A Bot

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`.
3. Follow the prompts.
4. Copy the bot token into `TELEGRAM_BOT_TOKEN`.

### Find Your Chat ID

1. Send a message to your new bot in Telegram.
2. Visit this URL in your browser, replacing the token:

   ```text
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```

3. Look for `chat.id` in the JSON response.
4. Put that number in `TELEGRAM_CHAT_ID`.

If the response is empty, send another message to the bot and refresh the URL.

## GitHub Secrets

Add these secrets in GitHub:

Repository page → Settings → Secrets and variables → Actions → New repository secret.

Required for Telegram delivery:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Optional:

- `OPENAI_API_KEY`
- `EMAIL_ENABLED`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`
- `LOCATION_NAME`
- `LATITUDE`
- `LONGITUDE`
- `TIMEZONE`
- `GOOGLE_CALENDAR_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

You can also add RSS feed overrides:

- `CANARY_RSS_FEEDS`
- `SCIENCE_RSS_FEEDS`
- `WORLD_RSS_FEEDS`

## Run Manually In GitHub

1. Open the repository on GitHub.
2. Go to Actions.
3. Select `Morning Agent`.
4. Click `Run workflow`.
5. Choose the `main` branch and run it.

## Schedule

GitHub Actions schedules use UTC, not local time.

The workflow currently uses:

```yaml
cron: "0 8 * * *"
```

That means 08:00 UTC daily.

For Canary Islands summer time, 09:00 local is 08:00 UTC. For Canary Islands winter time, 09:00 local is 09:00 UTC.

To run at 09:00 local during winter, change the cron line in `.github/workflows/morning.yml` to:

```yaml
cron: "0 9 * * *"
```

GitHub Actions does not automatically adjust cron schedules for daylight saving time, so update this twice a year if exact local time matters.

## OpenAI

OpenAI is optional.

- Add `OPENAI_API_KEY` to enable digest polishing and smarter suggested priorities.
- Leave it empty to use the built-in template.

The app still works if the OpenAI request fails.

## Email Backup

Email is optional and disabled by default.

Set:

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-user
SMTP_PASSWORD=your-password
EMAIL_FROM=you@example.com
EMAIL_TO=you@example.com
```

Telegram remains the primary delivery method. Email is sent only when enabled.

## Google Calendar

Calendar support is prepared, but not fully automatic OAuth yet.

The first version supports a service-account setup:

1. Create a Google Cloud service account.
2. Enable the Google Calendar API.
3. Share your calendar with the service-account email address.
4. Add `GOOGLE_CALENDAR_ID` to GitHub Secrets.
5. Add the full service-account JSON as `GOOGLE_SERVICE_ACCOUNT_JSON`.

If calendar credentials are missing or invalid, the digest says:

```text
No calendar configured yet.
```

Future improvement: add a friendlier OAuth flow for personal Google Calendar accounts.

## Configuration

Main environment variables are shown in `.env.example`.

Default location:

- `LOCATION_NAME=Santa Cruz de Tenerife`
- `LATITUDE=28.4636`
- `LONGITUDE=-16.2518`
- `TIMEZONE=Atlantic/Canary`

Weather uses Open-Meteo, which does not require an API key.

News uses RSS feeds. Each section is limited to a few short items so the Telegram message stays concise.

## Known Limitations

- Google Calendar OAuth is not implemented yet.
- GitHub Actions cron does not adjust automatically for daylight saving time.
- RSS feeds can occasionally be slow or unavailable; broken feeds are skipped.
- Weather and news are fetched from free public services, so occasional API changes are possible.
