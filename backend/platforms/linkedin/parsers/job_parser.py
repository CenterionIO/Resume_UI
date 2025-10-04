from playwright.async_api import Page # type: ignore
from typing import Dict, Any


async def parse_job_posting(page: Page) -> Dict[str, Any]:
    """Robust LinkedIn job parser using Playwright locators and fallbacks."""
    data: Dict[str, Any] = {}

    # --- expand collapsed content before parsing ---
    try:
        see_more = page.locator("button[aria-label*='See more']")
        if await see_more.count() > 0:
            await see_more.first.click()
            await page.wait_for_timeout(500)
    except Exception:
        pass

    # --- company name ---
    try:
        company = await page.locator("a.topcard__org-name-link, span.topcard__flavor").first.inner_text()
        if "There's not enough quality data" in company:
            company = await page.locator("div.top-card-layout__card").get_by_role("link").first.inner_text()
    except Exception:
        company = None
    data["company"] = company.strip() if company else None

    # ... rest of the function unchanged ...


    # --- job title ---
    try:
        title = await page.locator("h1.top-card-layout__title, h1").first.inner_text()
    except Exception:
        title = None
    data["job_title"] = title.strip() if title else None

    # --- location ---
    try:
        loc = await page.locator("span.topcard__flavor--bullet, span.topcard__flavor").first.inner_text()
    except Exception:
        loc = None
    data["location"] = loc.strip() if loc else None

    # --- work type / hybrid / remote ---
    try:
        work_type = await page.locator("span.topcard__flavor--metadata").first.inner_text()
    except Exception:
        work_type = None
    data["work_type"] = work_type.strip() if work_type else None

    # --- applicants & posting time ---
    try:
        data["applicants"] = (await page.locator("span.num-applicants__caption").first.inner_text()).strip()
    except Exception:
        data["applicants"] = None

    try:
        data["posted_time"] = (await page.locator("span.posted-time-ago__text").first.inner_text()).strip()
    except Exception:
        data["posted_time"] = None

    # --- logo image ---
    try:
        data["logo_url"] = await page.locator("img.artdeco-entity-image").first.get_attribute("src")
    except Exception:
        data["logo_url"] = None

    # --- section extraction ---
    data["sections"] = {}
    data["raw_sections"] = {}

    section_nodes = await page.locator("div.show-more-less-html__markup, section").all()
    for node in section_nodes:
        try:
            header = None
            try:
                header = await node.locator("h2,h3").first.inner_text()
            except Exception:
                pass

            body = await node.inner_text()
            if not header:
                # Heuristic fallback
                if "responsib" in body.lower():
                    header = "Responsibilities"
                elif "qualif" in body.lower():
                    header = "Qualifications"
                elif "benefit" in body.lower():
                    header = "Benefits"
                else:
                    header = "Content"

            # store if long enough to be meaningful
            if len(body.strip()) > 40:
                data["sections"][header] = body.strip()
                data["raw_sections"][header] = body.strip()
        except Exception:
            continue

    return data
