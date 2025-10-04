import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup # type: ignore


class LinkedInParser:
    def __init__(self):
        self.company_pattern = re.compile(r'linkedin\.com/company/([^/]+)')
        
    def parse_linkedin_job(self, html_content: str) -> Dict:
        """Main method to parse LinkedIn job posting using DOM structure"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Start from company logo as anchor point
        company_logo = soup.find('img', {'data-view-name': 'image'})
        
        result = {
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
        
        return result
    
    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from LinkedIn company link"""
        # Look for company links
        company_links = soup.find_all('a', href=True)
        
        for link in company_links:
            href = link.get('href', '')
            if 'linkedin.com/company/' in href:
                # Get company name from link text
                company_name = link.get_text().strip()
                if company_name:
                    return company_name
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job title from paragraph elements"""
        # Look for common title patterns
        title_selectors = [
            'p[class*="title"]',
            'h1[class*="title"]',
            '.jobs-unified-top-card__job-title',
            '.topcard__title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if text and len(text) > 3:
                    return text
        
        # Fallback: look for prominent text that could be title
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if text and 10 < len(text) < 100:  # Reasonable title length
                return text
        
        return None
    
    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location from span elements"""
        location_selectors = [
            'span[class*="location"]',
            '.jobs-unified-top-card__bullet',
            '.topcard__flavor--bullet'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if text and any(char.isalpha() for char in text):
                    return text
        
        # Look for common location patterns
        spans = soup.find_all('span')
        for span in spans:
            text = span.get_text().strip()
            if self._looks_like_location(text):
                return text
        
        return None
    
    def _looks_like_location(self, text: str) -> bool:
        """Check if text looks like a location"""
        if not text or len(text) > 50:
            return False
        
        # Common location patterns
        location_indicators = [
            ', CA', ', NY', ', TX', ', WA', ', IL', ', MA', ', CO', ', GA',
            ', FL', ', NC', ', VA', ', PA', ', OH', ', MI', ', NJ', ', AZ'
        ]
        
        return any(indicator in text for indicator in location_indicators)
    
    def _extract_posted_time(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract when job was posted"""
        time_patterns = [
            r'(\d+\s*(?:day|week|month|hour)s?\s*ago)',
            r'Posted\s*(?:on)?\s*([^•]+)'
        ]
        
        for pattern in time_patterns:
            match = self._find_text_by_pattern(soup, pattern)
            if match:
                return match
        
        return None
    
    def _extract_applicants(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract applicant count"""
        applicant_patterns = [
            r'(\d+\s*people?\s*(?:clicked\s*)?appl(?:y|ied))',
            r'(\d+\s*applicants?)',
            r'(\d+\s*candidates?)'
        ]
        
        for pattern in applicant_patterns:
            match = self._find_text_by_pattern(soup, pattern)
            if match:
                return match
        
        return None
    
    def _extract_salary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract salary information"""
        # Look for $ signs
        salary_patterns = [
            r'\$[\d,]+(?:K)?\s*[-–]\s*\$[\d,]+(?:K)?',
            r'\$[\d,]+(?:K)?\s*(?:per year|annually|/yr)'
        ]
        
        for pattern in salary_patterns:
            match = self._find_text_by_pattern(soup, pattern)
            if match:
                return match
        
        return None
    
    def _extract_work_arrangement(self, soup: BeautifulSoup) -> List[str]:
        """Extract work arrangement (Remote, Hybrid, On-site)"""
        arrangements = []
        work_terms = ['remote', 'hybrid', 'on-site', 'on site', 'flexible']
        
        for term in work_terms:
            if self._find_text_by_pattern(soup, term, case_sensitive=False):
                arrangements.append(term.title())
        
        return arrangements
    
    def _extract_employment_type(self, soup: BeautifulSoup) -> List[str]:
        """Extract employment type (Full-time, Part-time, Contract)"""
        employment_types = []
        type_terms = ['full-time', 'part-time', 'contract', 'temporary', 'internship']
        
        for term in type_terms:
            if self._find_text_by_pattern(soup, term, case_sensitive=False):
                employment_types.append(term.title())
        
        return employment_types
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main job description"""
        # Look for common description sections
        description_markers = [
            'about the job',
            'job description',
            'role description',
            'position overview'
        ]
        
        for marker in description_markers:
            # Find the marker and get subsequent content
            elements = soup.find_all(text=re.compile(marker, re.IGNORECASE))
            for element in elements:
                # Get the parent element and its siblings
                parent = element.parent
                if parent:
                    # Collect text from this element and following ones
                    description_parts = []
                    current = parent
                    while current:
                        text = current.get_text().strip()
                        if text and len(text) > 10:
                            description_parts.append(text)
                        current = current.find_next_sibling()
                    
                    if description_parts:
                        return '\n\n'.join(description_parts)
        
        return None
    
    def _extract_job_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract structured sections from job description"""
        sections = {}
        
        # Common section headers in job postings
        section_headers = {
            'qualifications': ['qualifications', 'requirements', 'what you bring'],
            'responsibilities': ['responsibilities', 'what you\'ll do', 'key responsibilities'],
            'benefits': ['benefits', 'what we offer', 'compensation', 'perks'],
            'about_company': ['about us', 'company description', 'who we are']
        }
        
        for section_name, keywords in section_headers.items():
            section_content = self._extract_section_by_keywords(soup, keywords)
            if section_content:
                sections[section_name] = section_content
        
        return sections
    
    def _extract_section_by_keywords(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[str]:
        """Extract a specific section by looking for header keywords"""
        for keyword in keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                parent = element.parent
                if parent and parent.name in ['h2', 'h3', 'h4', 'strong', 'b']:
                    # Found a section header, collect content until next header
                    content_parts = []
                    current = parent.find_next_sibling()
                    
                    while current and current.name not in ['h2', 'h3', 'h4']:
                        text = current.get_text().strip()
                        if text:
                            content_parts.append(text)
                        current = current.find_next_sibling()
                    
                    if content_parts:
                        return '\n'.join(content_parts)
        
        return None
    
    def _find_text_by_pattern(self, soup: BeautifulSoup, pattern: str, case_sensitive: bool = False) -> Optional[str]:
        """Find text matching a pattern in the HTML"""
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for element in soup.find_all(text=re.compile(pattern, flags)):
            text = element.strip()
            if text:
                match = re.search(pattern, text, flags)
                if match:
                    return match.group(0)
        
        return None