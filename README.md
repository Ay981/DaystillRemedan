Days-until-Remedhan Telegram Poster

What this does
- A small Python script that computes the days remaining until a target date (Remedhan) and posts a short message to a Telegram channel using a bot.

Files created
- `post_days_remaining.py` — main script. Reads config from env vars or CLI.
- `requirements.txt` — lists Python dependency.

Configuration
You can configure via environment variables or CLI flags:
- BOT_TOKEN (or --token): your bot token (e.g. 8373361785:...)
- CHANNEL_ID (or --channel): channel id or username (e.g. @DaystillRemedhan)
- TARGET_DATE (or --target): target date in YYYY-MM-DD format

Examples
Dry-run (safe test, does not send):

```bash
BOT_TOKEN=8373361785:REPLACE CHANNEL_ID=@DaystillRemedhan TARGET_DATE=2026-02-16 python3 post_days_remaining.py --dry-run
```

Send message once:

```bash
BOT_TOKEN=8373361785:REPLACE CHANNEL_ID=@DaystillRemedhan TARGET_DATE=2026-02-16 python3 post_days_remaining.py
```

Scheduling every 3 days
Option A — cron (simple, day-of-month based)
- Edit your crontab with `crontab -e` and add a line like below to run at 09:00 every 3 days of the month:

```cron
0 9 */3 * * BOT_TOKEN=your_token_here CHANNEL_ID=@DaystillRemedhan TARGET_DATE=2026-02-16 /usr/bin/python3 /home/aymen/personal/DaystillRemedan/post_days_remaining.py
```

Note: `*/3` in the day-of-month field repeats every 3 days within each calendar month and will not be perfectly every-72-hours across month boundaries. If you need exact 72-hour intervals, use Option B.

Option B — systemd timer (better for exact intervals)
- Create a service and timer that runs the script every 72 hours. Example files are not created here automatically; if you want I can scaffold them.

Option B — systemd timer (accurate 72-hour interval)
- I have scaffolded a user unit + timer and an install helper in `systemd/`.

Files added:
- `systemd/daystill.service` — user unit that runs the script once when triggered. It reads env vars from `$HOME/.config/daystill/daystill.env`.
- `systemd/daystill.timer` — timer set to `OnUnitActiveSec=72h` (runs every 72 hours).
- `systemd/install_systemd_user.sh` — helper script that copies the unit/timer into `$HOME/.config/systemd/user/` and creates an example env file.

Quick install and enable (run locally):

```bash
# copy files and create example env
bash systemd/install_systemd_user.sh

# edit the env file and set your values
${EDITOR:-nano} $HOME/.config/daystill/daystill.env

# reload user systemd units and enable the timer now
systemctl --user daemon-reload
systemctl --user enable --now daystill.timer
```

Check status and logs:

```bash
systemctl --user status daystill.timer
systemctl --user status daystill.service
journalctl --user -u daystill.service --since "1 hour ago"
```

Notes:
- The env file created is at `$HOME/.config/daystill/daystill.env`. Put these three lines (no quotes):

		BOT_TOKEN=8373361785:AAGOoArxjh3hn4gkVZEZ9LHZ8xvmmqDMvLs
		CHANNEL_ID=@DaystillRemedhan
		TARGET_DATE=2026-02-16

- The timer uses `OnUnitActiveSec=72h` for a strict 72-hour interval. `Persistent=true` ensures missed runs are triggered after reboots.

Security note
- Avoid committing your bot token to version control. Prefer storing `BOT_TOKEN` in a secure secrets store or as a user-only environment variable.

Next steps
- If you want, I can create a systemd unit and timer that runs the script on a strict 72-hour interval, or set up a small Docker container for easier deployment.

Hosting on Render (step-by-step)

If you want to host on Render, the simplest approach is to use a Render Scheduled Job that runs this container every few days.

Repository changes for Render
- `Dockerfile` — a small image that installs dependencies and runs the script (already added).
- `.dockerignore` — keeps the build small and avoids leaking local files.

Deploying to Render (recommended flow)

1. Push this repository to GitHub (or another supported git provider) and connect it to Render.

2. In Render, create a new Scheduled Job (Cron Job):
	- Select your repo and branch.
	- For the build method choose `Dockerfile` (Render will build the image from the repo).
	- Set the command to run (if you want to override the Docker CMD):

	  python3 post_days_remaining.py

	- Add environment variables (in Render UI -> Environment):
	  - BOT_TOKEN (secret)
	  - CHANNEL_ID (public `@DaystillRemedhan` or numeric id for private channel)
	  - TARGET_DATE (2026-02-16)

3. Schedule:
	- Use a cron expression such as `0 9 */3 * *` to run at 09:00 every 3rd day of the month (same caveat as cron across month boundaries).
	- If Render UI supports interval scheduling, set the interval to 72 hours for a strict every-72-hours run.

4. Test the job:
	- Trigger the job manually from Render once to confirm it runs and posts.
	- Inspect job logs in Render to confirm success.

Local Docker test (before pushing)

```bash
docker build -t daystill:local .
docker run --rm -e BOT_TOKEN=replace -e CHANNEL_ID=@DaystillRemedhan -e TARGET_DATE=2026-02-16 daystill:local --dry-run
```

Notes & security
- Keep `BOT_TOKEN` secret; set it in Render as an environment variable (secrets in the dashboard).
- If your channel is private, use the numeric `chat_id` (starts with -100...).

Want me to next:
- Create a `render.yaml` manifest you can import into Render (I can scaffold it here), or
- Add a GitHub Actions workflow that builds the container and optionally pushes it to a registry (useful if you want CI before Render builds), or
- Walk you step-by-step through the Render UI and assist with the first deploy interactively.
