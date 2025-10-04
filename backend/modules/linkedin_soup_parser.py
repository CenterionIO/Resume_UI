# modules/linkedin_soup_parser.py
import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup # type: ignore


class LinkedInSoupParser:
    def __init__(self):
        self.company_pattern = re.compile(r'linkedin\.com/company/([^/]+)')

    def parse(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, 'html.parser')

        return {
            'company': self._extract_company(soup),
            'title': self._extract_title(soup),
            'location': self._extract_location(soup),
            'posted_time': self._extract_posted_time(soup),
            'applicants': self._extract_applicants(soup),
            'salary': self._extract_salary(soup),
            'work_arrangement': self._extract_work_arrangement(soup),
            'employment_type': self._extract_employment_type(soup),
            'description': self._extract_description(soup),
            'sections': self._extract_job_sections(soup)
        }

    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        company_links = soup.find_all('a', href=True)
        for link in company_links:
            if 'linkedin.com/company/' in link['href']:
                return link.get_text(strip=True)
        return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = ['h1[class*="title"]', '.topcard__title']
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return None

    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = ['.topcard__flavor--bullet']
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return None

    def _extract_posted_time(self, soup: BeautifulSoup) -> Optional[str]:
        match = soup.find(text=re.compile(r'(\d+\s+(day|week|month|hour)s?\s+ago)'))
        return match.strip() if match else None

    def _extract_applicants(self, soup: BeautifulSoup) -> Optional[str]:
        match = soup.find(text=re.compile(r'(\d+\s+applicants?)'))
        return match.strip() if match else None

    def _extract_salary(self, soup: BeautifulSoup) -> Optional[str]:
        match = soup.find(text=re.compile(r'\$[\d,]+'))
        return match.strip() if match else None

    def _extract_work_arrangement(self, soup: BeautifulSoup) -> List[str]:
        terms = ['Remote', 'Hybrid', 'On-site']
        return [t for t in terms if soup.find(text=re.compile(t, re.IGNORECASE))]

    def _extract_employment_type(self, soup: BeautifulSoup) -> List[str]:
        types = ['Full-time', 'Part-time', 'Contract', 'Internship']
        return [t for t in types if soup.find(text=re.compile(t, re.IGNORECASE))]

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        desc = soup.select_one('.description, .show-more-less-html__markup')
        return desc.get_text(strip=True) if desc else None

    def _extract_job_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        sections = {}
        for header in soup.find_all(['h2', 'h3']):
            title = header.get_text(strip=True)
            body = []
            sib = header.find_next_sibling()
            while sib and sib.name not in ['h2', 'h3']:
                body.append(sib.get_text(strip=True))
                sib = sib.find_next_sibling()
            if title and body:
                sections[title] = "\n".join(body)
        return sections
