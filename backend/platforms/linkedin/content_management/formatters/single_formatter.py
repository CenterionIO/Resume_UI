import re

def clean_html(value: str) -> str:
    """Remove leftover tags and normalize spacing (but preserve newlines)."""
    if not value:
        return ""
    # Remove SVGs, scripts, etc.
    value = re.sub(r"<(svg|script|style)[^>]*>.*?</\1>", "", value, flags=re.DOTALL)
    # Remove other HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Normalize horizontal whitespace only (preserve newlines)
    value = re.sub(r"[ \t]+", " ", value)
    return value.strip()

def format_job_post(data: dict) -> str:
    """Format parsed LinkedIn job post cleanly with line breaks and readable spacing."""
    lines = []

    # --- Company name ---
    if data.get("company_name"):
        lines.append(clean_html(data['company_name']))
        lines.append("")

    # --- Title ---
    if data.get("title"):
        # Ensure there's a blank line before the title for clearer section separation
        if len(lines) > 0 and lines[-1].strip() != "":
            lines.append("")
        lines.append(clean_html(data['title']))
        lines.append("")

    # --- Location / Posted / Applicants ---
    details = [clean_html(data.get(k, "") or "") for k in ["location", "posted", "applicants"] if data.get(k)]
    if details:
        lines.append(" · ".join(details))
        lines.append("")

    # --- Salary / Work type / Employment type ---
    extras = [clean_html(data.get(k, "") or "") for k in ["salary", "work_type", "employment_type"] if data.get(k)]
    if extras:
        lines.append(" · ".join(extras))
        lines.append("")

    # --- About / Description ---
    if data.get("description"):
        # DON'T call clean_html() on description - it's already formatted in parser.py
        desc = data["description"]

        # Ensure there's a blank line before the section header
        if len(lines) > 0 and lines[-1].strip() != "":
            lines.append("")

        lines.append("About the job")
        lines.append("")
        lines.append(desc.strip())

    formatted = "\n".join(lines)
    return formatted.strip()