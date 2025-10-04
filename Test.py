import os
import re
import json
import webbrowser
import tempfile

def load_section_titles():
    """Load section titles - simplified version"""
    return [
        "Job Description", "Qualifications", "Responsibilities", 
        "Requirements", "Benefits", "About the Company",
        "Compensation", "Skills", "Experience"
    ]

def normalize(text):
    """Normalize text by removing extra whitespace"""
    return re.sub(r"\s+", " ", text.strip())

def parse_job_description_sections(html_block: str) -> dict:
    """Simple text-based parser without BeautifulSoup"""
    sections = {}
    
    # Simple regex-based parsing
    lines = html_block.split('\n')
    current_section = "Job Description"
    buffer = []
    
    titles = load_section_titles()
    
    for line in lines:
        line = normalize(line)
        if not line:
            continue
            
        # Check if this line matches any section title
        found_section = None
        for title in titles:
            if title.lower() in line.lower() and len(line) < 100:  # Section titles are usually short
                found_section = title
                break
                
        if found_section:
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
                buffer = []
            current_section = found_section
        else:
            buffer.append(line)
    
    if buffer:
        sections[current_section] = "\n".join(buffer).strip()
    
    return sections

def format_sections_as_html(sections: dict) -> str:
    """Format sections as HTML"""
    if not sections:
        return "<p>No job description content found.</p>"
    
    html_output = ""
    for section_title, section_content in sections.items():
        html_output += '<div class="section-block">'
        html_output += f'<div class="section-title">{section_title}</div>'
        
        paragraphs = section_content.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                html_output += f'<p class="section-paragraph">{paragraph.strip()}</p>'
        
        html_output += '</div>'
    
    return html_output

def parse_job_html(file_path):
    """Parse the HTML file using simple text parsing"""
    
    # Read the HTML file
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Simple regex extraction
    company_match = re.search(r'<span[^>]*style="[^"]*font-size:1\.3em[^"]*font-weight:bold[^"]*"[^>]*>([^<]+)</span>', html_content)
    company_name = company_match.group(1) if company_match else "Not found"
    
    title_match = re.search(r'<span[^>]*style="[^"]*font-size:1\.1em[^"]*"[^>]*>([^<]+)</span>', html_content)
    job_title = title_match.group(1) if title_match else "Not found"
    
    location_match = re.search(r'<span[^>]*style="[^"]*color:#666[^"]*"[^>]*>([^<]+)</span>', html_content)
    location = location_match.group(1) if location_match else "Not found"
    
    posted_match = re.search(r'<small[^>]*style="[^"]*color:#888[^"]*"[^>]*>([^<]+)</small>', html_content)
    posted_info = posted_match.group(1) if posted_match else "Not found"
    
    logo_match = re.search(r'<img[^>]*src="([^"]*)"', html_content)
    logo_url = logo_match.group(1) if logo_match else None
    
    # Parse job description sections
    job_description_sections = parse_job_description_sections(html_content)
    formatted_description = format_sections_as_html(job_description_sections)
    
    return {
        'company_name': company_name,
        'job_title': job_title,
        'location': location,
        'posted_info': posted_info,
        'logo_url': logo_url,
        'job_description': formatted_description,
        'sections_found': list(job_description_sections.keys()),
        'raw_html': html_content
    }

def create_browser_view(parsed_data):
    """Create an HTML file to display the parsed data"""
    
    logo_html = ''
    if parsed_data['logo_url']:
        logo_url = parsed_data['logo_url']
        logo_html = f'<div class="logo-section"><img src="{logo_url}" alt="Company Logo" class="logo-img"></div>'
    
    sections_text = ', '.join(parsed_data['sections_found']) if parsed_data['sections_found'] else 'No sections identified'
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Description Parser Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }}
        .job-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .job-info {{
            display: grid;
            gap: 15px;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        .label {{
            font-weight: bold;
        }}
        .value {{
            text-align: right;
        }}
        .logo-section {{
            text-align: center;
            margin: 20px 0;
        }}
        .logo-img {{
            max-width: 100px;
            max-height: 100px;
            border-radius: 5px;
        }}
        .description-section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .section-block {{
            margin-bottom: 25px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border: 1px solid #e5e7eb;
        }}
        .section-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #667eea;
        }}
        .section-paragraph {{
            margin: 8px 0;
            line-height: 1.5;
            color: #555;
        }}
        .sections-found {{
            background: #e8f4fd;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .raw-html {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            border-left: 4px solid #667eea;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }}
        .section-title-main {{
            color: #333;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px solid #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Job Description Parser</h1>
            <p>Extracted structured data from LinkedIn job posting</p>
        </div>
        
        <div class="job-card">
            <h2 style="margin-top: 0; text-align: center;">{parsed_data['company_name']}</h2>
            
            {logo_html}
            
            <div class="job-info">
                <div class="info-item">
                    <span class="label">Company:</span>
                    <span class="value">{parsed_data['company_name']}</span>
                </div>
                <div class="info-item">
                    <span class="label">Job Title:</span>
                    <span class="value">{parsed_data['job_title']}</span>
                </div>
                <div class="info-item">
                    <span class="label">Location:</span>
                    <span class="value">{parsed_data['location']}</span>
                </div>
                <div class="info-item">
                    <span class="label">Posted:</span>
                    <span class="value">{parsed_data['posted_info']}</span>
                </div>
            </div>
        </div>

        <div class="sections-found">
            <strong>Sections Found:</strong> {sections_text}
        </div>

        <h3 class="section-title-main">Job Description</h3>
        <div class="description-section">
            {parsed_data['job_description']}
        </div>
        
        <h3 class="section-title-main">Raw HTML Content</h3>
        <div class="raw-html">
            <pre>{parsed_data['raw_html']}</pre>
        </div>
    </div>
</body>
</html>"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_template)
        return f.name

def main():
    file_path = "/Users/michaelsteele/Documents/python_projects/resume-generator-ui/test.html"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    try:
        print("🔍 Parsing HTML file...")
        parsed_data = parse_job_html(file_path)
        
        print("\n✅ Parsed Job Data:")
        print(f"🏢 Company: {parsed_data['company_name']}")
        print(f"💼 Title: {parsed_data['job_title']}")
        print(f"📍 Location: {parsed_data['location']}")
        print(f"📅 Posted: {parsed_data['posted_info']}")
        print(f"🖼️ Logo URL: {parsed_data['logo_url'] or 'No logo found'}")
        print(f"📋 Sections Found: {', '.join(parsed_data['sections_found'])}")
        print(f"📝 Description Length: {len(parsed_data['job_description'])} characters")
        
        print("\n🌐 Opening browser view...")
        output_file = create_browser_view(parsed_data)
        webbrowser.open(f'file://{output_file}')
        print(f"📁 Temporary file created: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()