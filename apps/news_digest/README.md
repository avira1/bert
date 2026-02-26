# Medicare News Digest App

This app pulls the newest articles from KFF Health News' Medicare topic page, creates short summaries, and can deliver the digest through email and/or Microsoft Teams.

## What it does

1. Fetches the topic page: `https://kffhealthnews.org/topics/medicare/`.
2. Extracts the latest article links.
3. Opens each article and captures body text.
4. Builds a short summary from the opening sentences.
5. Sends a compiled digest to:
   - Email (SMTP),
   - Microsoft Teams (incoming webhook),
   - or both.

## Setup

```bash
cd apps/news_digest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

### For email delivery

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="465"
export SMTP_USER="your-user"
export SMTP_PASSWORD="your-app-password"
export EMAIL_FROM="alerts@yourcompany.com"
export EMAIL_TO="recipient@yourcompany.com"
```

### For Teams delivery

```bash
export TEAMS_WEBHOOK_URL="https://..."
```

## Run

Print digest only:

```bash
python medicare_news_digest.py --max-articles 5 --delivery none
```

Send by email:

```bash
python medicare_news_digest.py --max-articles 5 --delivery email
```

Send to Teams:

```bash
python medicare_news_digest.py --max-articles 5 --delivery teams
```

Send to both:

```bash
python medicare_news_digest.py --max-articles 5 --delivery both
```

## Suggested production workflow

1. Put this script in a small service repo/folder.
2. Move credentials into a secret manager (Azure Key Vault, AWS Secrets Manager, etc.).
3. Schedule execution:
   - Cron (Linux),
   - GitHub Actions scheduled workflow,
   - Azure Functions timer trigger.
4. Add logging and retries (for network/API failures).
5. Add persistence (SQLite/Redis) to avoid sending duplicate articles.

## Notes

- The summarizer is intentionally simple and deterministic (first few substantial sentences).
- You can swap in an LLM summarizer later if you want richer summaries.


## Move this app into a separate repo (`medicare-news-`)

If you want this app maintained in a dedicated repository named `medicare-news-`, use the export script:

```bash
cd /workspace/bert
./apps/news_digest/scripts/export_to_medicare_news_repo.sh /workspace/medicare-news-
```

Then publish from the new repo:

```bash
cd /workspace/medicare-news-
git add .
git commit -m "Initial import from bert/apps/news_digest"
git branch -M main
git remote add origin <your-medicare-news--repo-url>
git push -u origin main
```

This keeps `bert` as the source while giving you a clean standalone repo for deployment.
