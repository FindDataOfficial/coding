# Scraw — Unified Scraping & Document Processing Workflow

## Description
Build a unified scraping workflow that can handle static sites, JS-rendered pages, anti-bot protection, and document processing.

## Steps
1. Analyze the scraping task — Determine source type, scale, output needs, and anti-bot level
2. Select the right tool — Choose from Scrapling, Playwright, Crawl4AI, CloakBrowser, Scrapy, or document processors
3. Load sub-skills — Load the appropriate tool-specific skill and follow its instructions
4. Execute the scrape — Perform the actual data extraction
5. Structure the output — Clean, deduplicate, and format results
6. Return results — Present the final output to the user

## Success Criteria
- Can handle static HTML, JS-rendered, and anti-bot protected sites
- Produces clean, structured output (JSON, Markdown, or database)
- Follows robots.txt and rate-limiting best practices
- Works for single pages through to multi-page crawls

## Constraints
- Must respect robots.txt and terms of service
- No bypassing paywalls or authentication
- 100+ page crawls require user approval
