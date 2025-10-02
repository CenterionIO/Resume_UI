# modules/scraping/scraper.py
from modules.scraping.platforms.linkedin import linkedin_scraper

class ScrapingOrchestrator:
    def __init__(self):
        self.scrapers = {
            "linkedin": linkedin_scraper
        }

    def detect_platform(self, url: str) -> str:
        """Detect which platform the URL belongs to"""
        if "linkedin.com" in url:
            return "linkedin"
        # Add more platforms here as needed
        # elif "indeed.com" in url:
        #     return "indeed"
        else:
            raise ValueError(f"Unsupported platform for URL: {url}")

    async def scrape_job_posting(self, url: str, session_id: str, websocket=None) -> str:
        """Orchestrate scraping based on the detected platform"""
        platform = self.detect_platform(url)
        scraper = self.scrapers.get(platform)
        
        if not scraper:
            raise ValueError(f"No scraper available for platform: {platform}")
        
        print(f"🔧 Using {platform} scraper for URL: {url}")
        return await scraper.scrape_job(url, session_id, websocket)

# Singleton instance
scraping_orchestrator = ScrapingOrchestrator()