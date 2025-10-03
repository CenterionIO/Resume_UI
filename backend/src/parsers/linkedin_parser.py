import re
from bs4 import BeautifulSoup # type: ignore

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def parse_job_posting_to_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # --- Company Logo ---
    logo_url = ""
    logo_tag = soup.select_one("img[src*='company-logo']")
    if logo_tag:
        logo_url = logo_tag["src"]

    # --- Company Name ---
    company_name = "Unknown"
    company_tag = soup.find("a", href=re.compile("/company/"))
    if company_tag:
        company_name = normalize(company_tag.get_text())

    # --- Job Title ---
    job_title = "Unknown"
    title_tag = soup.select_one("h1, h2, p._33e6522e")
    if title_tag:
        job_title = normalize(title_tag.get_text())

    # --- Location ---
    location = "Unknown"
    loc_tag = soup.find(string=re.compile(r"(Hybrid|Remote|Seattle|WA|USA)", re.I))
    if loc_tag:
        location = normalize(loc_tag)

    # --- Posting Info ---
    posted = ""
    posted_match = re.search(r"(\d+\s+(day|week|month|hour)s?\s+ago)", html, re.I)
    if posted_match:
        posted = posted_match.group(1)

    applies = ""
    applies_match = re.search(r"(\d+)\s+people\s+clicked\s+apply", html, re.I)
    if applies_match:
        applies = f"{applies_match.group(1)} people applied"

    promoted = "Promoted by hirer" if re.search(r"Promoted by hirer", html, re.I) else ""

    # --- Description ---
    description_html = ""
    desc_container = soup.select_one(
        "div.jobs-description-content__text, div.jobs-description__content, section.jobs-description"
    )
    if desc_container:
        for br in desc_container.find_all("br"):
            br.replace_with("\n")
        blocks = []
        for tag in desc_container.find_all(["p", "li"]):
            txt = normalize(tag.get_text())
            if txt:
                blocks.append(f"<p>{txt}</p>")
        description_html = "\n".join(blocks)

    # --- Build Output HTML ---
    logo_html = f'<img src="{logo_url}" alt="Logo" style="height:60px; vertical-align:middle; margin-right:10px;">' if logo_url else "🏢"

    header_html = f"""
    <div class="job-header" style="font-family:sans-serif; margin-bottom:1em;">
        {logo_html}<span style="font-size:1.2em; font-weight:bold;">{company_name}</span><br>
        <span style="font-size:1.1em;">{job_title}</span><br>
        <span style="color:#666;">{location}</span><br>
        <small>{posted} {applies} {promoted}</small>
    </div>
    """

    body_html = f"""
    <div class="job-description" style="font-family:sans-serif; line-height:1.4;">
        {description_html}
    </div>
    """

    return header_html + body_html