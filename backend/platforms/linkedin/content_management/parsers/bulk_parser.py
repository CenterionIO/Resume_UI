"""
Simple BeautifulSoup-based parser for LinkedIn job API endpoints.
No complex parsing logic - just extract what we can find.
"""
from bs4 import BeautifulSoup
import re


def parse_linkedin_bulk(html: str) -> dict:
    """
    Parse LinkedIn job HTML using simple BeautifulSoup selectors.

    Args:
        html (str): HTML content from LinkedIn job API endpoint

    Returns:
        dict: Parsed job data with title, company, description, etc.
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    # Extract title - try multiple selectors
    title_selectors = [
        "h1",
        "h2.top-card-layout__title",
        ".topcard__title",
        "h2",
    ]
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
            break

    # Extract company
    company_selectors = [
        "a.topcard__org-name-link",
        ".topcard__flavor",
        "h4",
        "span.topcard__flavor--black-link",
    ]
    for selector in company_selectors:
        company_elem = soup.select_one(selector)
        if company_elem:
            result['company'] = company_elem.get_text(strip=True)
            break

    # Extract location
    location_selectors = [
        "span.topcard__flavor--bullet",
        ".job-details-jobs-unified-top-card__bullet",
        "span.topcard__flavor",
    ]
    for selector in location_selectors:
        location_elem = soup.select_one(selector)
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            # Check if it looks like a location (contains city/state info)
            if any(char in location_text for char in [',', 'Remote', 'Hybrid']):
                result['location'] = location_text
                break

    # Extract description - try multiple selectors
    description = None
    desc_selectors = [
        "div.description__text",
        "div.show-more-less-html__markup",
        "section.description",
        "div.description",
        "article.job-description",
    ]
    for selector in desc_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            description = desc_elem.get_text(separator="\n", strip=True)
            break

    # If no description found with specific selectors, get all text
    if not description:
        # Get all text but try to skip navigation/header stuff
        main_content = soup.select_one("main") or soup.select_one("body")
        if main_content:
            description = main_content.get_text(separator="\n", strip=True)

    if description and len(description) > 100:
        result['description'] = description

    # Try to extract salary if present
    salary_patterns = soup.find_all(string=lambda text: text and '$' in text)
    for pattern in salary_patterns:
        text = pattern.strip()
        if len(text) < 100 and '-' in text:  # Likely a salary range
            result['salary'] = text
            break

    # Try to extract applicants info
    applicants_patterns = soup.find_all(string=lambda text: text and 'applicant' in text.lower())
    for pattern in applicants_patterns:
        text = pattern.strip()
        if len(text) < 50:
            result['applicants'] = text
            break

    # Try to extract posted date
    posted_patterns = soup.find_all(string=lambda text: text and 'ago' in text.lower())
    for pattern in posted_patterns:
        text = pattern.strip()
        if len(text) < 50 and any(word in text.lower() for word in ['day', 'week', 'month', 'hour']):
            result['posted'] = text
            break

    return result
