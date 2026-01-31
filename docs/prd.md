# PRD: Multi-Forum Scraping Support

## Overview

Add support for scraping multiple forums in a single run with round-robin page processing to distribute load evenly across forums.

## Current Behavior

- CLI accepts a single `--forum-id` integer value (default: 3)
- `ScraperConfig.forum_id` is an `int`
- `scrape_forum()` processes all pages of a single forum sequentially

## Proposed Behavior

- CLI accepts multiple forum IDs via `--forum-ids` (comma-separated) or multiple `--forum-id` flags
- When multiple forums are specified, pages are processed in round-robin order
- Example with `--forum-ids 3,7 --max-pages 3`:
  1. Page 1 of forum 3
  2. Page 1 of forum 7
  3. Page 2 of forum 3
  4. Page 2 of forum 7
  5. Page 3 of forum 3
  6. Page 3 of forum 7

## Requirements

### CLI Changes (main.py)

1. Add `--forum-ids` argument accepting comma-separated integers (e.g., `--forum-ids 3,7,12`)
2. Keep `--forum-id` for backward compatibility (single forum)
3. If both are provided, merge them (no duplicates)
4. Validation: at least one forum ID must be provided

### Config Changes (config.py)

1. Add `forum_ids: list[int]` field to `ScraperConfig`
2. Keep `forum_id: int` for backward compatibility, defaulting to first item in `forum_ids`
3. Update `__post_init__` validation to check all forum IDs are positive

### Scraper Changes (scraper.py)

1. Add `get_forum_page_url(forum_id: int, page: int) -> str` helper method
   - Extracts URL building logic from `get_forum_page_urls()`
   - Returns single URL for given forum and page number

2. Add `scrape_forums() -> int` method
   - Iterates page numbers from `start_page` to `start_page + max_pages - 1`
   - For each page number, iterates through all `forum_ids`
   - Calls existing `scrape_forum_page()` and thread processing logic
   - Returns total posts scraped across all forums

3. Update `scrape_forum()` to use new helper (optional refactor for consistency)

### Backward Compatibility

- Single `--forum-id 3` continues to work as before
- `scrape_forum()` method unchanged for existing code that uses it directly
- Default behavior (no args) scrapes forum 3 only

## Implementation Notes

### Round-Robin Logic

```python
def scrape_forums(self) -> int:
    total_scraped = 0
    forum_ids = self.config.forum_ids

    for page_num in range(self.config.start_page, self.config.start_page + self.config.max_pages):
        for forum_id in forum_ids:
            url = self.get_forum_page_url(forum_id, page_num)
            # ... existing scrape_forum_page and thread processing

    return total_scraped
```

### CLI Parsing

```python
parser.add_argument('--forum-ids', type=str, default=None,
                    help='Comma-separated forum IDs to scrape (e.g., 3,7,12)')
parser.add_argument('--forum-id', type=int, action='append',
                    help='Forum ID to scrape (can be specified multiple times)')
```

### Merging Forum IDs

```python
forum_ids = []
if args.forum_ids:
    forum_ids.extend(int(x.strip()) for x in args.forum_ids.split(','))
if args.forum_id:
    forum_ids.extend(args.forum_id)
if not forum_ids:
    forum_ids = [3]  # default
forum_ids = list(dict.fromkeys(forum_ids))  # dedupe preserving order
```

## Testing

1. `python main.py --forum-id 3` - single forum (backward compat)
2. `python main.py --forum-ids 3,7` - multiple forums comma-separated
3. `python main.py --forum-id 3 --forum-id 7` - multiple forums via repeated flag
4. `python main.py --forum-ids 3,7 --forum-id 12` - combined (results in [3,7,12])
5. Verify round-robin ordering in logs with `--log-level DEBUG`

## Files to Modify

1. `main.py` - CLI argument parsing, forum ID merging logic
2. `config.py` - Add `forum_ids` field, update validation
3. `scraper.py` - Add `get_forum_page_url()` helper and `scrape_forums()` method
