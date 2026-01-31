# AgTalk Forum Scraper

A sophisticated Python web scraping tool designed to ethically extract and manage agricultural forum posts from AgTalk, with advanced data processing capabilities and PostgreSQL database integration.

## Features

- **Multi-Forum Scraping**: Scrape multiple forums in a single run with round-robin page processing
- **Ethical Scraping**: Full robots.txt compliance and respectful rate limiting
- **Multi-page Support**: Handles both forum pagination and multi-page thread discussions
- **PostgreSQL Integration**: Robust database storage with proper indexing
- **Flexible Pagination**: Support for custom starting pages and page ranges
- **Complete Data Capture**: Extracts titles, authors, dates, content, thread relationships, and forum IDs
- **Advanced Parsing**: Handles AgTalk's complex HTML structure with enhanced date extraction

## Installation

1. Install dependencies using [uv](https://docs.astral.sh/uv/):
```bash
uv sync
```

Or with pip:
```bash
pip install psycopg2-binary requests beautifulsoup4 trafilatura
```

2. Set up PostgreSQL database (see Database Setup section)

## Quick Start

### Local Setup
Set up your PostgreSQL database and configure environment variables:

```bash
# Run the setup script
python setup_local_db.py

# Test your connection
python debug_database.py

# Start scraping (single forum)
uv run main.py --forum-id 3 --max-pages 5 --delay 2.0 --log-level INFO

# Scrape multiple forums with round-robin processing
uv run main.py --forum-ids 3,7 --max-pages 5 --delay 2.0

# Reset database and scrape
uv run main.py --reset-db --max-pages 1
```

## Database Setup

### Option 1: Automated Setup (Recommended)
```bash
python setup_local_db.py
```
This interactive script will:
- Create the database and user
- Set proper permissions
- Generate environment variables
- Create a .env file

### Option 2: Manual Setup
1. Create database and user:
```sql
CREATE DATABASE agtalk_posts;
CREATE USER agtalk_user WITH PASSWORD '<YOUR_PASSWORD>';
GRANT ALL PRIVILEGES ON DATABASE agtalk_posts TO agtalk_user;
```

2. Set environment variables:
```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=agtalk_posts
export PGUSER=agtalk_user
export PGPASSWORD=<YOUR_PASSWORD>
```

## Usage

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --forum-id FORUM_ID       Forum ID to scrape (can be specified multiple times)
  --forum-ids IDS           Comma-separated forum IDs (e.g., 3,7,12)
  --max-pages MAX_PAGES     Maximum number of pages to scrape (default: 10)
  --start-page START_PAGE   Page number to start scraping from (default: 1)
  --delay DELAY             Delay between requests in seconds (default: 2.0)
  --log-level LEVEL         Logging level (default: INFO)
  --reset-db                Reset the database before scraping
```

### Examples

```bash
# Scrape first 5 pages of forum 3
python main.py --forum-id 3 --max-pages 5

# Scrape multiple forums with comma-separated IDs (round-robin processing)
python main.py --forum-ids 3,7,12 --max-pages 5

# Scrape multiple forums using repeated --forum-id flags
python main.py --forum-id 3 --forum-id 7 --max-pages 5

# Scrape pages 10-15 with debug logging
python main.py --start-page 10 --max-pages 5 --log-level DEBUG

# Reset database and scrape with custom delay
python main.py --reset-db --delay 3.0 --max-pages 1
```

## Database Schema

```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    post_date TEXT,
    content TEXT NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thread_id TEXT,
    post_number INTEGER,
    forum_id INTEGER
);
```

Indexed on: `url`, `thread_id`, `scraped_at`, `post_date`, `forum_id`.

## Troubleshooting

### Database Connection Issues

1. **Run the debug tool**:
```bash
python debug_database.py
```

2. **Common fixes**:
   - Ensure PostgreSQL is running: `sudo systemctl start postgresql`
   - Check environment variables are set
   - Verify database exists and user has permissions
   - Test connection: `psql -h localhost -U agtalk_user -d agtalk_posts`

### Local vs Replit Differences

| Environment | Database | Configuration |
|-------------|----------|---------------|
| Replit | Automatic PostgreSQL | Uses DATABASE_URL |
| Local | Manual PostgreSQL setup | Uses individual PG* variables |

### Permission Errors
```bash
# Grant additional permissions if needed
psql -U postgres -c "ALTER USER agtalk_user CREATEDB;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE agtalk_posts TO agtalk_user;"
```

## Architecture

- **config.py**: Database and scraping configuration
- **scraper.py**: Main scraping logic with pagination support  
- **parser.py**: HTML parsing and data extraction
- **database.py**: PostgreSQL database operations
- **robots_checker.py**: robots.txt compliance verification

## Key Features

### Multi-Forum Round-Robin Scraping
When scraping multiple forums, pages are processed in round-robin order to distribute load evenly. For example, with `--forum-ids 3,7 --max-pages 3`:
1. Page 1 of forum 3
2. Page 1 of forum 7
3. Page 2 of forum 3
4. Page 2 of forum 7
5. Page 3 of forum 3
6. Page 3 of forum 7

### Multi-page Thread Support
The scraper automatically detects and follows pagination links within individual threads, ensuring complete data capture for discussions spanning multiple pages.

### Bookmark-based Pagination
Uses AgTalk's bookmark parameter system for accurate page navigation:
- Page 1: `forum-view.asp?fid=3&displaytype=flat`
- Page N: `forum-view.asp?fid=3&bookmark=X&displaytype=flat` where X = 1 + ((N-1) * 50)

### Enhanced Date Parsing
Robust date extraction that searches multiple HTML locations to capture post timestamps in MM/DD/YYYY HH:MM format.

## Docker Deployment

### Quick Start with Docker

```bash
# Build for Apple Silicon
make build-arm64

# Build and export for distribution
make export

# Run with environment variables
make run
```

### Docker Build Options

| Command | Description |
|---------|-------------|
| `make build-arm64` | Build for Apple Silicon (ARM64) |
| `make build-multi` | Build multi-platform (ARM64 + AMD64) |
| `make export` | Build and export to tar file |
| `make run` | Run container with environment |
| `make shell` | Interactive container shell |

### Container Configuration

The container runs: `uv run main.py --forum-id 3 --max-pages 100 --delay 20.0 --log-level INFO`

Set database environment variables:
```bash
export DATABASE_URL="postgresql://<username>:<password>@<host>:<port>/<database>"
# OR individual variables:
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=agtalk_posts
export PGUSER=agtalk_user
export PGPASSWORD=<YOUR_PASSWORD>
```

### Docker Compose

For complete setup with PostgreSQL:
```bash
docker-compose up -d
```

## Contributing

1. Test changes locally: `uv run main.py --max-pages 1 --log-level DEBUG`
2. Test Docker build: `make test`
3. Check database integrity after modifications

## License

Educational and research purposes. Respects robots.txt and implements ethical scraping practices.