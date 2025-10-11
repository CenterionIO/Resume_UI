# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack web application that scrapes job postings from LinkedIn and other job boards, parses the job descriptions using custom HTML/regex parsers, and displays the formatted results in a React frontend. The goal is to generate AI-tailored resumes based on job descriptions.

**Tech Stack:**
- Backend: FastAPI (Python 3.12+) with WebSocket support
- Frontend: React 19 + Vite + TailwindCSS
- Scraping: Playwright (browser automation) + BeautifulSoup (HTML parsing)
- Parser: Custom regex-based HTML parser for LinkedIn job postings

## Development Commands

### Backend
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server (with hot reload)
python main.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (default: http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Environment Setup
- Create a `.env` file in the project root with:
  ```
  LINKEDIN_EMAIL=your_email@example.com
  LINKEDIN_PASSWORD=your_password
  ```
- Note: The hardcoded path in `backend/core/config.py:7` needs to be updated to your local path

## Architecture

### Backend Structure (`backend/`)

**Main Application** (`main.py`):
- FastAPI app with CORS middleware
- Two primary endpoints:
  - `POST /parse` - Accepts HTML content or URL for parsing
  - `WS /ws/scrape-progress` - WebSocket endpoint for real-time scraping progress
  - `GET /platforms/linkedin/bulk` - Bulk LinkedIn job scraping (via router)
- Parser registry system in `PARSERS` dict maps parser types to functions
- Currently only LinkedIn parser is fully implemented

**Platform-Based Organization** (`platforms/linkedin/`):
- `parsers/` - HTML parsing logic
  - `parser.py` - Core LinkedIn job parser using regex patterns
  - `linkedin_soup_parser.py` - Alternative BeautifulSoup-based parser
  - `linkedin_bulk_scraper.py` - Bulk scraping via LinkedIn's public AJAX API
  - `linkedin_bulk.py` - FastAPI router for bulk scraping endpoint
  - `job_parser.py` - Legacy parser (likely deprecated)
- `auth/` - Authentication and session management
  - `auth_manager.py` - LinkedIn authentication logic
- `utils/` - Helper utilities
  - `linkedin_login.py` - Login automation
  - `session_manager.py` - Browser session persistence
  - `broser_utils.py` - Browser configuration helpers
- `scrapers/` - Browser automation scrapers
  - `linkedin_scraper.py` - Playwright-based scraper
- `routers/` - API route handlers
  - `websockets/job_parser.py` - WebSocket handlers
  - `internal/parser_toggle.py` - Parser selection logic

**Configuration** (`backend/core/config.py`):
- Environment variables loading
- Browser configuration (viewport, user agent, Playwright args)
- Storage paths for cookies, browser profiles, screenshots
- Session management settings (2-week max age)

**Storage** (`backend/storage/`):
- `cookies/` - Persistent session cookies
- `browser_profiles/` - Playwright browser profile data
- `screenshots/` - Debug screenshots

### Frontend Structure (`frontend/src/`)

**Main Component** (`App.jsx`):
- Simple wrapper that renders `UrlInput` component
- Manages submission state

**Components** (`components/`):
- `UrlInput.jsx` - Main form component with:
  - Parser selection (LinkedIn, Indeed, HTML Formatter, LinkedIn Bulk)
  - URL input mode (WebSocket-based scraping)
  - Bulk scraping mode (keyword + location + pages)
  - Progress display
  - Integration with `JobDescriptionDisplay`
- `JobDescriptionDisplay.jsx` - Renders parsed job data
- `ProgressDisplay.jsx` - Shows real-time scraping progress
- `InitialContent.jsx` - Landing page UI
- `UrlInputForm.jsx` - Reusable form component

**Hooks** (`hooks/`):
- `useWebSocket.js` - WebSocket connection management
  - Auto-reconnect on disconnect
  - Session ID persistence in localStorage
  - Message parsing and error handling

**Utils** (`utils/`):
- `linkedinService.js` - API service layer for LinkedIn operations
- `htmlParser.js` - Client-side HTML formatting utilities
- `scrapingUtils.js` - Scraping helper functions

### LinkedIn Parser Logic (`backend/platforms/linkedin/parsers/parser.py`)

The parser uses a **sequential position-tracking algorithm** to extract job data:

1. **Company Image** - Finds `data-view-name="image"` marker, then locates `<img>` tag
2. **Company Name** - Extracts from LinkedIn company URL slug
3. **Job Title** - Regex pattern `>([^<>]+)<span class="` with special character filtering
4. **Location** - Matches `>City, STATE</span>` pattern using US state codes from JSON
5. **Posted Date** - Finds text containing "ago" (e.g., "2 days ago", "Reposted 1 week ago")
6. **Applicants** - Extracts "X people clicked apply" phrase
7. **Salary** - Finds dollar amounts in format `$XX,XXX - $XX,XXX`
8. **Work Type** - Searches for keywords: full-time, part-time, contract, internship, etc.
9. **Employment Type** - Detects hybrid, remote, on-site, work from home
10. **Job Description** - Extracts "About the job" section and formats:
    - Converts `<strong>`/`<b>` to Markdown `**bold**`
    - Converts `<li>` to bullet points `•`
    - Preserves paragraph structure
    - Detects implicit headers (short non-bold lines)
    - Normalizes whitespace

**Key Implementation Details:**
- Uses `pos` variable to track parsing position and avoid backtracking
- Relies on BeautifulSoup for text extraction from HTML blocks
- Uses regex with named groups and state code validation
- Preserves native bold formatting from LinkedIn HTML

### WebSocket Communication Flow

1. Frontend connects to `ws://localhost:8000/ws/scrape-progress`
2. Frontend sends JSON: `{"url": "https://...", "parser": "linkedin_soup"}`
3. Backend sends progress updates: `{"status": "started", "message": "..."}`
4. Backend sends completion: `{"status": "complete", "data": "<formatted_html>"}`
5. Frontend renders parsed job data in `JobDescriptionDisplay`

### LinkedIn Bulk Scraping (`linkedin_bulk_scraper.py`)

- Scrapes LinkedIn's public AJAX endpoint: `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`
- Parameters: `keywords`, `location`, `start` (pagination offset)
- Extracts basic job metadata: title, company, location, URL, publication date
- Implements retry logic (3 attempts) and random delays (1.5-3.5s) to mimic human behavior
- Returns list of job dictionaries without full descriptions

## Common Development Patterns

### Adding a New Parser

1. Create parser function in `backend/platforms/{platform}/parsers/`
2. Register in `PARSERS` dict in `backend/main.py`
3. Add parser option to `parsers` array in `frontend/src/components/UrlInput.jsx`
4. Implement parser logic following the pattern in `parser.py`

### Testing Parsers

1. Save sample HTML to `test.html` in project root
2. Run `Test.py` or create a simple script:
   ```python
   from backend.platforms.linkedin.parsers.parser import parse_linkedin_job
   with open('test.html', 'r') as f:
       html = f.read()
   result = parse_linkedin_job(html)
   print(result)
   ```

### Debugging WebSocket Issues

- Check backend logs for connection status (`✅ WebSocket connected`)
- Check frontend console for WebSocket events
- Verify backend is running on port 8000
- Test WebSocket connection directly with browser DevTools

## Known Issues & Technical Debt

1. **Hardcoded path** in `backend/core/config.py:7` - needs to use relative path or env var
2. **Parser selection broken** - Recent commits mention "parse toggle-broken, needs help"
3. **Multiple parser implementations** - `parser.py`, `linkedin_soup_parser.py`, `job_parser.py` - consolidation needed
4. **Missing module** - `linkedin_scraper.py` imports `modules.linkedin_html_parser.extract_summary_section` which doesn't exist in this codebase
5. **US States dependency** - Parser relies on external JSON file at hardcoded path (`parser_search_helper.json`)
6. **Limited error handling** - WebSocket errors fall back to mock data instead of retrying
7. **No authentication flow** - LinkedIn credentials stored in plaintext .env file
8. **Browser profile bloat** - Multiple UUID-named profiles in `storage/browser_profiles/`

## File Naming Conventions

- Python: `snake_case.py`
- React components: `PascalCase.jsx`
- Hooks: `useCamelCase.js`
- Utils: `camelCase.js`
- Config files: `lowercase.config.js`
