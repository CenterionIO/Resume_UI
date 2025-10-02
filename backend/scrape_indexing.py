# Module: scrape_indexing.py
# Description: Handles screenshot capture, keyword persistence, and plaintext job saving.

import json
from pathlib import Path
from bs4 import BeautifulSoup

# Screenshot path
SCREENSHOT_DIR = Path("/Users/michaelsteele/Python Projects/Resume_Generator/scraped/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Keyword path
KEYWORD_JSON_PATH = Path("/Users/michaelsteele/Python Projects/Resume_Generator/db/keyword.json")
KEYWORD_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

# Structured plaintext path
FULL_TEXT_JSON_PATH = Path("/Users/michaelsteele/Python Projects/Resume_Generator/db/full_job_description.json")
FULL_TEXT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------- Screenshot ----------
async def save_screenshot(page, job_id: str):
    path = SCREENSHOT_DIR / f"{job_id}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"📸 Screenshot saved to {path}")
    return str(path)

# ---------- Keyword ----------
def load_keyword_data():
    if KEYWORD_JSON_PATH.exists():
        try:
            with open(KEYWORD_JSON_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            print("⚠️ Corrupt or empty keyword.json — starting fresh.")
            return {}
    return {}

def save_keywords_for_job(job_id: str, hard_skills: str, soft_skills: str) -> None:
    data = load_keyword_data()
    data[job_id] = {
        "hard_skills": hard_skills.strip(),
        "soft_skills": soft_skills.strip()
    }
    with open(KEYWORD_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved keyword data for Job ID {job_id}")

# ---------- Plaintext ----------
def load_existing_plaintext():
    if FULL_TEXT_JSON_PATH.exists():
        try:
            with open(FULL_TEXT_JSON_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            print("⚠️ Corrupt or empty full_job_description.json — starting fresh.")
            return {}
    return {}

def extract_structured_text(parsed_html: str) -> str:
    soup = BeautifulSoup(parsed_html, "html.parser")
    output_lines = []

    metadata = soup.find_all("div", recursive=False)
    for block in metadata:
        output_lines.append(block.get_text(separator=" ", strip=True))

    sections = soup.select("div.section-block")
    for sec in sections:
        title = sec.select_one("div.section-title")
        paragraphs = sec.select("p.section-paragraph")

        if title:
            output_lines.append(f"## {title.get_text(strip=True)}")
        for p in paragraphs:
            output_lines.append(p.get_text(strip=True))
        output_lines.append("")

    return "\n".join(output_lines).strip()

def save_plaintext(job_id: str, parsed_html: str) -> bool:
    existing = load_existing_plaintext()
    if job_id in existing:
        print(f"⚠️ Skipping plaintext save — Job ID {job_id} already exists.")
        return False

    structured_text = extract_structured_text(parsed_html)
    existing[job_id] = structured_text

    with open(FULL_TEXT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved structured plaintext for Job ID {job_id}")
    return True

def get_plaintext(job_id: str) -> str:
    data = load_existing_plaintext()
    return data.get(job_id, "")
