# modules/html_parser.py
import re
import json
from difflib import get_close_matches
from bs4 import BeautifulSoup # type: ignore


def load_section_titles(path="config/section_titles.json"):
    """Load section titles configuration"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback section titles
        return {
            "Job Description": ["job description", "about the job", "role description"],
            "Company Description": ["company description", "about the company", "about us"],
            "Qualifications": ["qualifications", "requirements", "what you'll need", "what you bring", "skills"],
            "Responsibilities": ["responsibilities", "what you'll do", "key responsibilities", "role responsibilities", "duties"],
            "Benefits": ["benefits", "what we offer", "compensation", "perks", "salary", "benefits and perks"],
            "Additional Information": ["additional information", "other information", "more details", "notes"],
            "Application Process": ["how to apply", "application process", "next steps", "to apply"]
        }


def normalize(text):
    """Normalize text by removing extra whitespace"""
    return re.sub(r"\s+", " ", text.strip()) if text else ""


# parsers/linkedin_html_parser.py - Update the extract_linkedin_metadata function

def extract_linkedin_metadata(scraped_content: str) -> dict:
    """Extract job metadata from LinkedIn HTML"""
    soup = BeautifulSoup(scraped_content, 'html.parser')

    metadata = {
        'company': 'Not found',
        'job_title': 'Not found',
        'location': 'Not found',
        'work_type': 'Not found',
        'applicants': 'Not found',
        'posted_time': 'Not found',
        'logo_url': ''
    }

    # Company name extraction - more specific selectors
    company_selectors = [
        'a[href*="company"]',
        '[data-view-name*="company"]',
        '.topcard__org-name-link',
        '.jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__subtitle-primary',
        'a[data-tracking-control-name="public_jobs_topcard-org-name"]'
    ]

    for selector in company_selectors:
        company_elem = soup.select_one(selector)
        if company_elem:
            company_text = company_elem.get_text(strip=True)
            if company_text and len(company_text) > 2 and "followers" not in company_text.lower():
                metadata['company'] = company_text
                break

    # Job title extraction - more specific selectors
    title_selectors = [
        '.jobs-unified-top-card__job-title',
        '.topcard__title',
        'h1[class*="title"]',
        'h1',
        '[data-view-name*="job-detail"] h1'
    ]

    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if title_text and len(title_text) > 5:
                metadata['job_title'] = title_text
                break

    # Location extraction - look for specific patterns
    location_selectors = [
        '.jobs-unified-top-card__bullet',
        '.topcard__flavor--bullet',
        '.jobs-unified-top-card__subtitle-secondary',
        '[class*="location"]',
        '[data-test-id*="location"]'
    ]

    for selector in location_selectors:
        loc_elem = soup.select_one(selector)
        if loc_elem:
            loc_text = loc_elem.get_text(strip=True)
            if loc_text and any(indicator in loc_text.lower() for indicator in ['miami', 'remote', 'hybrid', 'on-site']):
                metadata['location'] = loc_text
                break

    # Work type extraction
    work_type_indicators = ['On-site', 'Remote', 'Hybrid', 'Full-time', 'Part-time']
    for text in soup.stripped_strings:
        text_clean = normalize(text)
        if any(indicator in text_clean for indicator in work_type_indicators):
            metadata['work_type'] = text_clean
            break

    # Applicants count - more specific patterns
    applicants_patterns = [
        r'(\d+)\s*applicants?',
        r'(\d+)\s*people?\s*applied',
        r'(\d+)\s*candidates?'
    ]
    
    for text in soup.stripped_strings:
        for pattern in applicants_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['applicants'] = match.group(0)
                break
        if metadata['applicants'] != 'Not found':
            break

    # Posted time
    time_patterns = [
        r'(\d+\s*(?:hours?|days?|weeks?|months?)\s*ago)',
        r'Posted\s*(?:on)?\s*([^•]+)',
        r'Promoted\s*•?\s*([^•]+)'
    ]
    
    for text in soup.stripped_strings:
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['posted_time'] = match.group(1)
                break
        if metadata['posted_time'] != 'Not found':
            break

    # Logo URL - more specific selectors
    logo_selectors = [
        'img[src*="company-logo"]',
        '.jobs-unified-top-card__company-logo img',
        '.topcard__flavor--logo img',
        'img[alt*="logo"]',
        'img[data-ghost-classes*="company-logo"]'
    ]

    for selector in logo_selectors:
        logo_elem = soup.select_one(selector)
        if logo_elem and logo_elem.get('src'):
            metadata['logo_url'] = logo_elem.get('src')
            break

    return metadata


def parse_job_description_sections(html_block: str) -> dict:
    """Parse job description into structured sections"""
    soup = BeautifulSoup(html_block, "html.parser")
    
    # Multiple strategies to find the main job content container
    container_selectors = [
        'div[class*="jobs-description-content"]',
        'div[class*="job-details"]',
        'div[data-view-name*="job-detail"]',
        'div[componentkey*="job"]',
        'div[class*="description-content"]',
        'div[class*="jobs-description"]'
    ]
    
    container = None
    for selector in container_selectors:
        container = soup.select_one(selector)
        if container:
            break
    
    if not container:
        # Fallback: look for common LinkedIn job content patterns
        container = soup.find(lambda tag: tag.name == 'div' and 
                            any(keyword in str(tag.get('class', [])).lower() 
                                for keyword in ['job', 'description', 'content', 'detail']))
    
    if not container:
        return {"Job Description": "No job description content found"}

    # Extract all text content with structure
    sections = {}
    current_section = "Job Description"
    buffer = []
    
    # Get all text elements while preserving some structure
    elements = container.find_all(['p', 'div', 'span', 'h2', 'h3', 'h4', 'li', 'strong', 'b'])
    
    for element in elements:
        text = normalize(element.get_text())
        if not text or text in buffer:  # Avoid duplicates
            continue
            
        # Check if this element is a section header
        is_header = False
        header_text = ""
        
        # Strategy 1: Check for common header patterns
        header_indicators = [
            element.name in ['h2', 'h3', 'h4'],
            element.find(['strong', 'b']) is not None,
            any(attr in str(element.get('class', [])).lower() 
                for attr in ['title', 'header', 'heading', 'label', 'subtitle'])
        ]
        
        if any(header_indicators):
            # Try to match with known section titles
            titles = load_section_titles()
            for section_name, keywords in titles.items():
                if any(keyword in text.lower() for keyword in keywords):
                    is_header = True
                    header_text = section_name
                    break
            else:
                # Check for direct text matches
                possible = get_close_matches(text.lower(), 
                                           [t.lower() for t in titles.keys()], 
                                           n=1, cutoff=0.7)
                if possible:
                    is_header = True
                    header_text = possible[0].title()
        
        if is_header:
            # Save previous section
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
                buffer = []
            current_section = header_text
        else:
            # Regular content - avoid adding very short irrelevant text
            if len(text) > 10 or any(keyword in text.lower() for keyword in ['years', 'experience', 'degree', 'salary']):
                buffer.append(text)
    
    # Don't forget the last section
    if buffer:
        sections[current_section] = "\n".join(buffer).strip()
    
    # If no sections were found, put everything in Job Description
    if not sections and buffer:
        sections["Job Description"] = "\n".join(buffer).strip()
    
    return sections


def format_sections_as_html(sections: dict) -> str:
    """Format sections dictionary as HTML"""
    if not sections:
        return "<p>No job description content found.</p>"
    
    html_output = ""
    for section_name, content in sections.items():
        if content:
            html_output += f"""
            <div class="section-block" style="margin-bottom: 2rem;">
                <div class="section-title" style="font-size: 1.2em; font-weight: bold; color: #333; margin-bottom: 0.5rem; border-bottom: 2px solid #0073b1; padding-bottom: 0.25rem;">
                    {section_name}
                </div>
                <div class="section-content" style="line-height: 1.6; color: #555;">
                    {content.replace(chr(10), '<br>')}
                </div>
            </div>
            """
    
    return html_output


def extract_job_id(scraped_content: str) -> str:
    """Extract job ID from LinkedIn URL"""
    job_id_match = re.search(r'/jobs/view/(\d+)', scraped_content)
    return job_id_match.group(1) if job_id_match else "unknown"


async def extract_summary_section(scraped_content: str, websocket=None) -> dict:
    """Main function to extract and structure job information"""
    
    def send_update(message):
        if websocket:
            import asyncio
            try:
                asyncio.create_task(websocket.send_text(json.dumps({"message": message})))
            except RuntimeError:
                print("⚠️ WebSocket already closed, skipping send.")
        print(message)

    # Extract job ID for reference
    job_id = extract_job_id(scraped_content)
    
    # --- Extract metadata ---
    send_update("🔍 Extracting job metadata...")
    metadata = extract_linkedin_metadata(scraped_content)
    
    # Build metadata display
    logo_img = f'<img src="{metadata["logo_url"]}" alt="Logo" style="height:60px; vertical-align:middle; margin-right:12px; border-radius:4px;">' if metadata["logo_url"] else "🏢"
    
    metadata_html = f"""
    <div style="border:1px solid #ddd; padding:16px; border-radius:8px; margin-bottom:20px; background:#f9f9f9;">
        {logo_img} 
        <div style="display:inline-block; vertical-align:middle;">
            <strong style="font-size:1.3em; color:#333;">{metadata['company']}</strong><br>
            <strong style="font-size:1.1em; color:#0073b1;">{metadata['job_title']}</strong><br>
            📍 {metadata['location']} | 🏢 {metadata['work_type']}<br>
            👥 {metadata['applicants']} | ⏰ {metadata['posted_time']}
        </div>
    </div>
    """
    
    # --- Parse job description sections ---
    send_update("📋 Parsing job description sections...")
    sections = parse_job_description_sections(scraped_content)
    
    if sections:
        formatted_body = format_sections_as_html(sections)
        parsed_output = f"{metadata_html}{formatted_body}"
        
        send_update(f"✅ Successfully extracted {len(sections)} sections")
        
        return {
            "message": "✅ Extracted structured job description",
            "parsed_text": parsed_output,
            "metadata": metadata,
            "sections": list(sections.keys())
        }
    
    # --- Fallback: Basic text extraction ---
    send_update("⚠️ Using fallback text extraction...")
    soup = BeautifulSoup(scraped_content, "html.parser")
    
    # Try to find any meaningful text content
    paragraphs = soup.find_all(["p", "div"], attrs={"dir": "ltr"})
    if not paragraphs:
        paragraphs = soup.find_all("p")
    
    if paragraphs:
        raw_text = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short irrelevant text
                raw_text.append(text)
        
        if raw_text:
            formatted_body = "<div class='section-block'>"
            formatted_body += "<div class='section-title'>Job Description</div>"
            for text in raw_text[:10]:  # Limit to first 10 paragraphs
                formatted_body += f"<p class='section-paragraph'>{text}</p>"
            formatted_body += "</div>"
            
            parsed_output = f"{metadata_html}{formatted_body}"
            
            send_update("✅ Job summary extracted successfully (fallback method)")
            
            return {
                "message": "✅ Job summary extracted successfully (fallback method)",
                "parsed_text": parsed_output,
                "metadata": metadata,
                "sections": ["Job Description"]
            }
    
    # --- Final fallback: Return metadata only ---
    send_update("⚠️ No detailed job description found, returning metadata only")
    
    minimal_output = f"""
    {metadata_html}
    <div style="border:1px solid #ffa500; padding:16px; border-radius:8px; background:#fffaf0;">
        <strong>Note:</strong> Unable to extract detailed job description. 
        The job posting may be in a format not currently supported, or content may be loaded dynamically.
    </div>
    """
    
    return {
        "message": "⚠️ No detailed job description found",
        "parsed_text": minimal_output,
        "metadata": metadata,
        "sections": []
    }