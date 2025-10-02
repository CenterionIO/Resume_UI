# core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv  # type: ignore

# Load environment variables
load_dotenv("/Users/michaelsteele/Documents/python_projects/resume-generator-ui/.env")

# Base paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"

# Session configuration
SESSION_MAX_AGE_HOURS = 336  # 2 weeks

# LinkedIn credentials (temporary - will move to user auth)
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Browser configuration
BROWSER_CONFIG = {
    "viewport": {"width": 1280, "height": 720},
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "args": ['--no-sandbox', '--disable-setuid-sandbox'],
    "timeout": 60000
}

# Storage paths
COOKIE_STORAGE_DIR = STORAGE_DIR / "cookies"
BROWSER_PROFILES_DIR = STORAGE_DIR / "browser_profiles"
SCREENSHOTS_DIR = STORAGE_DIR / "screenshots"

# Ensure directories exist
for directory in [COOKIE_STORAGE_DIR, BROWSER_PROFILES_DIR, SCREENSHOTS_DIR]:
    os.makedirs(directory, exist_ok=True)