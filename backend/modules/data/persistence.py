# modules/data/persistence.py
import json
from pathlib import Path
from bs4 import BeautifulSoup # type: ignore
from core.config import BASE_DIR

class DataPersistence:
    def __init__(self):
        self.keyword_json_path = BASE_DIR / "storage" / "keyword.json"
        self.full_text_json_path = BASE_DIR / "storage" / "full_job_description.json"
        
        # Ensure directories exist
        self.keyword_json_path.parent.mkdir(parents=True, exist_ok=True)
        self.full_text_json_path.parent.mkdir(parents=True, exist_ok=True)

    def load_keyword_data(self):
        """Load existing keyword data"""
        if self.keyword_json_path.exists():
            try:
                with open(self.keyword_json_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
            except (json.JSONDecodeError, ValueError):
                print("⚠️ Corrupt or empty keyword.json — starting fresh.")
                return {}
        return {}

    def save_keywords_for_job(self, job_id: str, hard_skills: str, soft_skills: str) -> None:
        """Save keyword data for a job"""
        data = self.load_keyword_data()
        data[job_id] = {
            "hard_skills": hard_skills.strip(),
            "soft_skills": soft_skills.strip()
        }
        with open(self.keyword_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved keyword data for Job ID {job_id}")

    def load_existing_plaintext(self):
        """Load existing plaintext job descriptions"""
        if self.full_text_json_path.exists():
            try:
                with open(self.full_text_json_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
            except (json.JSONDecodeError, ValueError):
                print("⚠️ Corrupt or empty full_job_description.json — starting fresh.")
                return {}
        return {}

    def extract_structured_text(self, parsed_html: str) -> str:
        """Extract structured text from HTML"""
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

    def save_plaintext(self, job_id: str, parsed_html: str) -> bool:
        """Save plaintext job description"""
        existing = self.load_existing_plaintext()
        if job_id in existing:
            print(f"⚠️ Skipping plaintext save — Job ID {job_id} already exists.")
            return False

        structured_text = self.extract_structured_text(parsed_html)
        existing[job_id] = structured_text

        with open(self.full_text_json_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved structured plaintext for Job ID {job_id}")
        return True

    def get_plaintext(self, job_id: str) -> str:
        """Get plaintext job description by ID"""
        data = self.load_existing_plaintext()
        return data.get(job_id, "")

# Singleton instance
data_persistence = DataPersistence()