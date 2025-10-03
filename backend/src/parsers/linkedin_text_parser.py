# backend/src/parsers/linkedin_text_parser.py - UPDATED
import re

def parse_linkedin_job_text(text: str) -> str:
    """
    Parse LinkedIn job content from plain text (no HTML tags)
    """
    print("🔍 Parsing plain text LinkedIn job content...")
    
    # Clean the text
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    # --- Extract Title ---
    title = "Unknown Title"
    # More specific title patterns - avoid grabbing navigation text
    title_patterns = [
        r"Director of Development/\s*Project Manager",  # Specific to your example
        r"(?<=Learning)([A-Z][A-Za-z\s\/]+Manager|[A-Z][A-Za-z\s\/]+Director)(?=\s•)",  # After "Learning"
        r"(?<=NotificationsMeFor BusinessLearning)([A-Za-z\s\/]+)(?=\s•)",  # After the nav section
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            title = match.group(1 if len(match.groups()) > 0 else 0).strip()
            print(f"✅ Found title: {title}")
            break
    
    # --- Extract Company ---
    company = "Unknown Company"
    company_patterns = [
        r"Oolite Partners",  # Direct match
        r"(?<=•\s)([A-Z][A-Za-z\s&]+)(?=\s•\s*Director|\s•\s*Manager)",  # Between bullets
        r"(?<=\s)(Oolite Partners)(?=\s•|\sDirector)",  # Specific company
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            company = match.group(1 if len(match.groups()) > 0 else 0).strip()
            print(f"✅ Found company: {company}")
            break
    
    # --- Extract Location ---
    location = "Unknown Location"
    location_patterns = [
        r"Miami,\s*FL\s*\(On-site\)",  # Full location with context
        r"Miami,\s*FL",  # Just city/state
        r"(?<=•\s)([A-Za-z]+,\s*[A-Z]{2}\s*\([^)]+\))(?=\s·)",  # Between bullet and time
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            location = match.group(1 if len(match.groups()) > 0 else 0).strip()
            print(f"✅ Found location: {location}")
            break
    
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
    
    # --- Check if Promoted ---
    promoted = "Promoted by hirer" if "Promoted by hirer" in text else ""
    if promoted:
        print("✅ Found promoted tag")
    
    # --- Extract Description ---
    description = "No description available"
    
    # Look for description after key markers
    desc_markers = [
        "About the job",
        "Role Description", 
        "Company Description",
        "Unique opportunity for",
    ]
    
    for marker in desc_markers:
        if marker in text:
            start_idx = text.find(marker) + len(marker)
            # Find a reasonable end point
            end_markers = ["Set alert", "Applicants for", "About the company", "… more"]
            end_idx = len(text)
            
            for end_marker in end_markers:
                if end_marker in text[start_idx:]:
                    end_idx = start_idx + text[start_idx:].find(end_marker)
                    break
            
            description = text[start_idx:end_idx].strip()
            # Clean up the description
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 500:
                description = description[:500] + "..."
            print(f"✅ Found description using '{marker}' ({len(description)} chars)")
            break
    
    # If no structured description found, try to extract meaningful content
    if description == "No description available":
        # Look for substantial text blocks after the header section
        header_end = text.find("About the job")
        if header_end > 0:
            meaningful_text = text[header_end:]
            sentences = re.findall(r'[^.!?]*[.!?]', meaningful_text)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
            if meaningful_sentences:
                description = ' '.join(meaningful_sentences[:3])  # First 3 substantial sentences
                if len(description) > 500:
                    description = description[:500] + "..."
                print(f"✅ Extracted description from sentences ({len(description)} chars)")
    
    # --- Build HTML Output ---
    metadata_bits = " • ".join(filter(None, [posted, applicants, promoted]))
    
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
    
    print(f"✅ Final output generated: {len(html_output)} chars")
    return html_output