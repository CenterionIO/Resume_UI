import re
from bs4 import BeautifulSoup # type: ignore
import json

import os
STATES_FILE = os.path.expanduser(
    '~/Library/Mobile Documents/com~apple~CloudDocs/Python_Projects/HTML_Parser/html_parser_app/backend/utils/parser_search_helper.json'
)
US_STATES = None
if os.path.exists(STATES_FILE):
    with open(STATES_FILE, 'r') as f:
        US_STATES = json.load(f)

if isinstance(US_STATES, dict):
    STATE_CODES = '|'.join(US_STATES.keys())
else:
    STATE_CODES = ''


def parse_linkedin_job(html):
    pos = 0
    data = {}

    # 1. Find company image URL
    image_marker = html.find('data-view-name="image"><svg', pos)
    if image_marker != -1:
        img_tag = html.find('<img class=', image_marker)
        if img_tag != -1:
            src_start = html.find('src="', img_tag) + 5
            src_end = html.find('"', src_start)
            data['company_image_url'] = html[src_start:src_end]
            pos = src_end

    # 2. Find company name from LinkedIn URL
    company_link = html.find('href="https://www.linkedin.com/company/', pos)
    if company_link != -1:
        slug_start = company_link + len('href="https://www.linkedin.com/company/')
        slug_end = html.find('/', slug_start)
        data['company_slug'] = html[slug_start:slug_end]
        data['company_name'] = data['company_slug'].replace('-', ' ').title()
        pos = company_link

    # 3. Find job title
    html_after_company = html[pos:pos + 5000]
    
    pattern = r'>([^<>]+)<span class="'
    matches = re.finditer(pattern, html_after_company)
    
    special_chars = set('!@#$%^&*()_+=[]{}|\\;:\'",<>/?`~')
    
    for match in matches:
        potential_title = match.group(1).strip()
        
        # Filter criteria
        has_special = any(char in special_chars for char in potential_title)
        valid_length = 5 < len(potential_title) < 200
        
        if not has_special and valid_length:
            data['title'] = potential_title
            pos = pos + match.end()
            break

    # 4. Find location - search after title
    if 'title' in data:
        html_after_title = html[pos:pos + 30000]
        
        # Pattern: ">City, STATE</span><span class=" where STATE is valid US state code
        pattern = rf'>([^<>]+,\s*(?:{STATE_CODES}))</span><span class="'
        match = re.search(pattern, html_after_title)
        
        if match:
            data['location'] = match.group(1).strip()
            pos = pos + match.end()

    # 5. Find posted date - search after location (or title if no location)
    html_after_pos = html[pos:pos + 30000]
    
    # Look for anything containing "ago" inside ">text</span><span class="
    pattern = r'>([^<>]*ago[^<>]*)</span><span class="'
    match = re.search(pattern, html_after_pos, re.IGNORECASE)
    
    if match:
        posted_text = match.group(1).strip()
        time_pattern = r'(?:Reposted\s+)?(\d+\s+(?:day|days|week|weeks|month|months)\s+ago)'
        time_match = re.search(time_pattern, posted_text, re.IGNORECASE)
        if time_match:
            data['posted'] = time_match.group(0).strip()
        else:
            data['posted'] = posted_text
        pos = pos + match.end()

    # 5b. Find "people clicked apply" phrase - store full string as applicants
    html_after_posted = html[pos:pos + 30000]

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_after_posted, "html.parser")
    text_block = soup.get_text(" ", strip=True)

    match = re.search(r'([Oo]ver\s*\d+\s*people\s+clicked\s+apply|\d+\s*people\s+clicked\s+apply)', text_block)
    if match:
        data['applicants'] = match.group(1).strip()
        data['applicants_pos'] = pos + match.start()
        pos = pos + match.end()

    # 5c. Salary: capture including leading $
    html_after_applicants = html[pos:pos + 30000]
    salary_match = re.search(r'>\s*(\$\s*[^<]+)<', html_after_applicants)
    if salary_match:
        data['salary'] = salary_match.group(1).strip()
        # don't advance pos too far yet — keep same scope for next searches

    # Extract text after salary for type scanning
    html_after_salary = html[pos:pos + 30000]
    soup2 = BeautifulSoup(html_after_salary, "html.parser")
    text_block2 = soup2.get_text(" ", strip=True)

    # 5d. Work type (Full-time, Part-time, etc.)
    work_type_match = re.search(
        r'\b(full[\s\-]?time|part[\s\-]?time|contract|temporary|internship|freelance|seasonal)\b',
        text_block2, re.IGNORECASE
    )
    if work_type_match:
        data['work_type'] = work_type_match.group(1).replace("-", " ").strip().title()

    # 5e. Employment type (Hybrid, Remote, On-site, etc.)
    employment_type_match = re.search(
        r'\b(hybrid|remote|on[\s\-]?site|in[\s\-]?office|work\s*from\s*home)\b',
        text_block2, re.IGNORECASE
    )
    if employment_type_match:
        # precedence: prefer hybrid > remote > on-site > in-office
        found = employment_type_match.group(1).lower()
        if "hybrid" in found:
            data['employment_type'] = "Hybrid"
        elif "remote" in found:
            data['employment_type'] = "Remote"
        elif "on" in found or "site" in found:
            data['employment_type'] = "On-Site"
        elif "office" in found:
            data['employment_type'] = "In Office"
        elif "home" in found:
            data['employment_type'] = "Work From Home"



        # 6. Find "About the job" section (up to end marker)
    formatted = ""  # ensure defined, prevents UnboundLocalError

    about_start = html.find('About the job', pos)
    if about_start != -1:
        about_end = html.find('<div class="job-details-how-you-match-card__container', about_start)
        if about_end == -1:
            about_end = html.find('</div>', about_start + 5000)

        raw_desc = html[about_start:about_end]

        # Remove literal header if duplicated
        raw_desc = re.sub(r'^\s*About the job\s*', '', raw_desc, flags=re.IGNORECASE)
        formatted = raw_desc

        # --- Clean tags - just remove bold tags (no Markdown conversion) ---
        # Case 1: Bold tags immediately followed by ":" or "!" → keep text with punctuation
        formatted = re.sub(
            r'<\s*(strong|b)[^>]*>([^<]+)</\s*\1\s*>\s*([:!])',
            lambda m: f"{m.group(2).strip()}{m.group(3)}",
            formatted,
            flags=re.IGNORECASE,
        )

        # Case 2: Regular bold tags - just keep the text
        formatted = re.sub(
            r'<\s*(strong|b)[^>]*>([^<]+)</\s*\1\s*>',
            lambda m: f"{m.group(2).strip()}",
            formatted,
            flags=re.IGNORECASE,
        )


        # Convert <li> to bullets
        formatted = re.sub(r'<li[^>]*>(.*?)</li>', r'BULLETPOINT\1', formatted, flags=re.DOTALL)
        formatted = formatted.replace('<ul>', '').replace('</ul>', '')

        # Convert <br> and paragraph tags to newlines
        formatted = re.sub(r'(<br\s*/?>\s*){2,}', '\n\n', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'<br\s*/?>', '\n', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', formatted, flags=re.DOTALL)

        # Remove any other leftover tags
        formatted = re.sub(r'<[^>]+>', '', formatted)

        # --- Detect implicit headers (non-bold, short lines) ---
        lines = []
        for line in formatted.splitlines():
            stripped = line.strip()
            if not stripped:
                lines.append('')
                continue

            # Header-like if short, single-sentence, not ending with a period
            if (
                len(stripped) < 100
                and not stripped.endswith('.')
                and stripped.count('.') <= 1
            ):
                # Add blank line before to isolate header visually
                if lines and lines[-1]:
                    lines.append('')
                lines.append(stripped)
                lines.append('')
            else:
                lines.append(stripped)

        formatted = "\n".join(lines)

        # Replace bullets
        formatted = formatted.replace('BULLETPOINT', '\n• ')

        # Normalize spacing
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = re.sub(r'[ \t]+', ' ', formatted)
        formatted = formatted.strip()

        # Save cleaned description
        data['description'] = formatted

    return data

