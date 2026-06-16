# Goal Discovery Report

**Project:** test-project
**Date:** 2026-06-16
**Discovery method:** Direct file inspection (no skill used)

---

## Goals Found: 1

### Goal: Scraw — Unified Scraping & Document Processing Workflow

**Source file:** `goal/initial-goal/scraw.md`

**Description:**
Build a unified scraping workflow that can handle static sites, JS-rendered pages, anti-bot protection, and document processing.

**Steps involved (6 total):**
1. Analyze the scraping task — Determine source type, scale, output needs, and anti-bot level
2. Select the right tool — Choose from Scrapling, Playwright, Crawl4AI, CloakBrowser, Scrapy, or document processors
3. Load sub-skills — Load the appropriate tool-specific skill and follow its instructions
4. Execute the scrape — Perform the actual data extraction
5. Structure the output — Clean, deduplicate, and format results
6. Return results — Present the final output to the user

**Success criteria:**
- Can handle static HTML, JS-rendered, and anti-bot protected sites
- Produces clean, structured output (JSON, Markdown, or database)
- Follows robots.txt and rate-limiting best practices
- Works for single pages through to multi-page crawls

**Constraints:**
- Must respect robots.txt and terms of service
- No bypassing paywalls or authentication
- 100+ page crawls require user approval

---

## Summary

The test project contains **1 goal** under `goal/initial-goal/`. The goal is to build a unified scraping and document processing workflow called "Scraw" that can intelligently select the right scraping tool for different types of web content and produce structured output. No work has been started on this goal — it is in the initial/goal definition stage.
