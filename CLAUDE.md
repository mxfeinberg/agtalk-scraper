# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgTalk Scraper is a Python web scraper that extracts forum posts from AgTalk (talk.newagtalk.com) with robots.txt compliance and rate limiting. Data is stored in PostgreSQL.

## Commands

```bash
# Run scraper (requires PostgreSQL and env vars set)
uv run main.py --forum-id 3 --max-pages 5 --delay 2.0

# Quick test run
uv run main.py --max-pages 1 --log-level DEBUG

# Reset database and scrape
uv run main.py --reset-db --max-pages 1

# Docker build (Apple Silicon)
make build-arm64

# Docker build and export for distribution
make export

# Run in Docker
make run

# Test container
make test
```

## Environment Variables

Set via `.env` file (see `.env.example`) or export directly:
- `DATABASE_URL` - PostgreSQL connection string, OR:
- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`

## Architecture

```
main.py          Entry point, CLI args, logging setup
    ↓
config.py        ScraperConfig dataclass, loads env vars
    ↓
scraper.py       AgTalkScraper orchestrates the flow
    ├→ robots_checker.py   Checks robots.txt before scraping
    ├→ parser.py           AgTalkParser extracts URLs and post data from HTML
    └→ database.py         DatabaseManager handles PostgreSQL CRUD
```

**Key pagination patterns:**
- Forum pages: `bookmark` param = 1 + ((page-1) * 50)
- Thread pages: `start` param = 1 + ((page-1) * 50)

**Deduplication:** Posts get unique URLs as `{thread_url}#post{post_number}`. Database has UNIQUE constraint on URL.

## Database Schema

`posts` table with columns: id, url (unique), title, author, post_date, content, scraped_at, thread_id, post_number, forum_id. Indexed on url, thread_id, scraped_at, post_date, forum_id.
