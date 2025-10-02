# modules/scraping/content_extractor.py
import re
import asyncio
from asyncio import sleep, gather, create_task
from playwright.async_api import Page # type: ignore

class ContentExtractor:
    def __init__(self):
        pass

    async def extract_job_content(self, page: Page):
        """Extract job description content from LinkedIn"""
        try:
            job_description = await page.query_selector(".jobs-description__content")
            if job_description:
                content = await job_description.text_content()
                if content and len(content.strip()) > 100:
                    return content.strip()
            
            # Fallback: extract from body
            body_text = await page.text_content("body")
            return body_text[:3000] if body_text else ""
            
        except Exception as e:
            print(f"Error extracting content: {e}")
            return f"Error extracting job description: {str(e)}"

    def extract_job_id(self, url: str):
        """Extract job ID from LinkedIn URL"""
        job_id_match = re.search(r'/jobs/view/(\d+)', url)
        if not job_id_match:
            raise ValueError("❌ Invalid LinkedIn job URL")
        return job_id_match.group(1)

    async def expand_job_description(self, page: Page):
        """Try to expand job description if there's a 'See more' button"""
        expand_selectors = [
            "button:has-text('See more')",
            "button:has-text('See more')",
            "button[aria-label*='see more']",
            ".jobs-description-expand"
        ]
        
        for selector in expand_selectors:
            see_more = await page.query_selector(selector)
            if see_more:
                print("🔽 Expanding job description...")
                await see_more.click()
                await asyncio.sleep(2)  # Wait for expansion
                break

# Singleton instance
content_extractor = ContentExtractor()