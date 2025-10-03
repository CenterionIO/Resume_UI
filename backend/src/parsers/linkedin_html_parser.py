# backend/src/parsers/linkedin_text_parser.py
import re

def parse_linkedin_job_text(text: str) -> str:
    """
    Parse LinkedIn job content from plain text (no HTML tags)
    """
    print("🔍 Parsing plain text LinkedIn job content...")
    
    # --- Extract Title ---
    title = "Unknown Title"
    # Look for patterns like "Job Title • Company" or "Job Title at Company"
    title_patterns = [
        r"([A-Z][A-Za-z\s\/]+\s(?:Manager|Director|Engineer|Developer|Analyst))",  # Job title patterns
        r"^([A-Za-z\s\/]+)(?=\s•|\sat\s|$)",  # Text before bullet/separator
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            title = match.group(1).strip()
            print(f"✅ Found title: {title}")
            break
    
    # --- Extract Company ---
    company = "Unknown Company"
    company_patterns = [
        r"([A-Z][A-Za-z\s&]+)(?=\s•|\sDirector of|\sManager of)",  # Company before title
        r"at\s+([A-Z][A-Za-z\s&]+)(?=\s•|$)",  # "at Company"
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            company = match.group(1).strip()
            print(f"✅ Found company: {company}")
            break
    
    # --- Extract Location ---
    location = "Unknown Location"
    location_match = re.search(r"([A-Za-z\s]+(?:,\s*[A-Z]{2})?(?:\s*\([^)]+\))?)(?=\s·|\s•|$)", text)
    if location_match:
        location = location_match.group(1).strip()
        print(f"✅ Found location: {location}")
    
    # --- Extract Posted Time ---
    posted = ""
    posted_match = re.search(r"(\d+\s+(?:hour|day|week|month)s?\s+ago)", text)
    if posted_match:
        posted = posted_match.group(1)
        print(f"✅ Found posted time: {posted}")
    
    # --- Extract Applicants ---
    applicants = ""
    applicants_match = re.search(r"(\d+)\s+applicants?", text)
    if applicants_match:
        applicants = f"{applicants_match.group(1)} applicants"
        print(f"✅ Found applicants: {applicants}")
    
    # --- Extract Description ---
    description = "No description available"
    
    # Look for description after "About the job" or "Role Description"
    desc_patterns = [
        r"About the job\s*(.*?)(?=Set alert|Applicants for|About the company|$)",
        r"Role Description\s*(.*?)(?=Set alert|Applicants for|About the company|$)",
        r"Company Description\s*(.*?)(?=Role Description|Set alert|Applicants for|$)",
    ]
    
    for pattern in desc_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            description = match.group(1).strip()
            # Clean up the description
            description = re.sub(r'\s+', ' ', description)  # Normalize whitespace
            description = description[:1000] + "..." if len(description) > 1000 else description
            print(f"✅ Found description ({len(description)} chars)")
            break
    
    # --- Build HTML Output ---
    metadata_bits = " • ".join(filter(None, [posted, applicants, "Promoted by hirer" if "Promoted" in text else ""]))
    
    html_output = f"""
    <div class="job-header" style="font-family:sans-serif; margin-bottom:1em;">
        🏢<span style="font-size:1.3em; font-weight:bold;">{company}</span><br>
        <span style="font-size:1.1em;">{title}</span><br>
        <span style="color:#666;">{location}</span><br>
        <small style="color:#888;">{metadata_bits}</small>
    </div>
    
    <div class="job-description" style="font-family:sans-serif; line-height:1.4;">
        <p>{description}</p>
    </div>
    """
    
    return html_output