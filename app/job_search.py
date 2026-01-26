"""
Job Search Integration for JustJoin.it
Searches for job postings and extracts job descriptions
"""

import httpx
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)


async def search_justjoinit_jobs(
    skills: List[str],
    location: str = "remote",
    experience_level: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    """
    Search for jobs on JustJoin.it by scraping the website

    Args:
        skills: List of skills to search for
        location: Job location (default: "remote")
        experience_level: junior, mid, senior, or None for all
        limit: Maximum number of jobs to return

    Returns:
        List of job dictionaries with title, company, url, skills_required, etc.
    """

    # Build search keyword from skills
    keyword = " ".join(skills[:3]) if skills else "developer"  # Use top 3 skills

    # Map location to JustJoin.it format
    location_param = location.lower()
    if location_param == "remote":
        location_param = "all-locations"

    # Build URL for web scraping
    search_url = f"https://justjoin.it/job-offers/{location_param}"
    if keyword:
        # URL encode the keyword
        import urllib.parse

        encoded_keyword = urllib.parse.quote(keyword)
        search_url += f"?keyword={encoded_keyword}"

    jobs = []

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        ) as client:
            logger.info(f"Scraping jobs from: {search_url}")

            # Fetch the page
            response = await client.get(search_url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Find job listings - JustJoin.it uses specific CSS classes for job cards
            # We'll look for common patterns in job listing websites
            job_cards = []

            # Try multiple selectors as the structure might vary
            possible_selectors = [
                'div[data-test-id="virtuoso-item-list"] > div',
                "div.css-1x8vx75",
                'a[href*="/offers/"]',
                'div[class*="offer"]',
            ]

            for selector in possible_selectors:
                job_cards = soup.select(selector)
                if job_cards and len(job_cards) > 3:  # Found meaningful results
                    logger.info(
                        f"Found {len(job_cards)} job cards with selector: {selector}"
                    )
                    break

            if not job_cards:
                logger.warning("Could not find job listings on page")
                return []

            # Extract job information from each card
            for idx, card in enumerate(
                job_cards[: limit * 2]
            ):  # Get more than limit to filter later
                try:
                    # Extract job URL
                    link = card.find("a", href=True)
                    if not link:
                        link = card.find_parent("a", href=True)

                    if not link or "/offers/" not in link.get("href", ""):
                        continue

                    job_url = link["href"]
                    if not job_url.startswith("http"):
                        job_url = f"https://justjoin.it{job_url}"

                    # Extract job ID from URL
                    job_id = job_url.split("/offers/")[-1].split("?")[0]

                    # Extract title
                    title_elem = card.find(["h2", "h3"]) or card.find(
                        class_=lambda x: x and "title" in x.lower()
                    )
                    title = (
                        title_elem.get_text(strip=True)
                        if title_elem
                        else "Position Available"
                    )

                    # Extract company name
                    company_elem = card.find(
                        class_=lambda x: x and "company" in x.lower()
                    )
                    if not company_elem:
                        # Try finding by text pattern
                        company_elem = card.find(
                            "div", string=lambda x: x and len(str(x).strip()) > 2
                        )
                    company = (
                        company_elem.get_text(strip=True) if company_elem else "Company"
                    )

                    # Extract skills/technologies
                    skill_tags = card.find_all(
                        ["span", "div"],
                        class_=lambda x: x
                        and ("skill" in x.lower() or "tag" in x.lower()),
                    )
                    skills_found = [
                        tag.get_text(strip=True)
                        for tag in skill_tags
                        if tag.get_text(strip=True)
                    ]

                    # Extract location
                    location_elem = card.find(
                        string=lambda x: x
                        and any(
                            city in str(x).lower()
                            for city in [
                                "warszawa",
                                "kraków",
                                "wrocław",
                                "remote",
                                "warsaw",
                                "krakow",
                            ]
                        )
                    )
                    job_location = location_elem.strip() if location_elem else location

                    # Check if remote
                    is_remote = (
                        "remote" in str(card).lower()
                        or "remote" in job_location.lower()
                    )

                    # Filter by experience level if specified
                    if experience_level:
                        card_text = card.get_text().lower()
                        if experience_level.lower() not in card_text:
                            continue

                    job_data = {
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "url": job_url,
                        "location": job_location,
                        "remote": is_remote,
                        "experience_level": experience_level or "not specified",
                        "skills_required": skills_found,
                        "matching_skills": (
                            list(
                                set(skills_found).intersection(
                                    set(s.lower() for s in skills)
                                )
                            )
                            if skills
                            else []
                        ),
                    }

                    jobs.append(job_data)

                    if len(jobs) >= limit:
                        break

                except Exception as e:
                    logger.debug(f"Error parsing job card {idx}: {str(e)}")
                    continue

            logger.info(f"Successfully scraped {len(jobs)} jobs from JustJoin.it")
            return jobs

    except Exception as e:
        logger.error(f"Error scraping JustJoin.it: {str(e)}")
        return []


async def get_job_details(job_id: str) -> Optional[Dict]:
    """
    Get full job details by scraping the job page

    Args:
        job_id: JustJoin.it job ID (from URL)

    Returns:
        Complete job details dict with description
    """
    url = f"https://justjoin.it/offers/{job_id}"

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        ) as client:
            logger.info(f"Fetching job details from: {url}")

            response = await client.get(url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract job details from the page
            title = ""
            title_elem = soup.find("h1") or soup.find("h2")
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract company name
            company = ""
            company_elem = soup.find(class_=lambda x: x and "company" in x.lower())
            if company_elem:
                company = company_elem.get_text(strip=True)

            # Extract full description - look for main content area
            description = ""
            description_elem = soup.find(
                ["div", "section"],
                class_=lambda x: x
                and ("description" in x.lower() or "content" in x.lower()),
            )
            if not description_elem:
                # Fallback: get the main content area
                description_elem = soup.find("main") or soup.find("article")

            if description_elem:
                description = description_elem.get_text(separator="\n", strip=True)

            # Extract skills
            skill_tags = soup.find_all(
                ["span", "div"],
                class_=lambda x: x
                and ("skill" in x.lower() or "tag" in x.lower() or "tech" in x.lower()),
            )
            skills_required = list(
                set(
                    [
                        tag.get_text(strip=True)
                        for tag in skill_tags
                        if tag.get_text(strip=True)
                    ]
                )
            )

            # Extract location
            location = "Not specified"
            location_elem = soup.find(
                string=lambda x: x
                and any(
                    city in str(x).lower()
                    for city in [
                        "warszawa",
                        "kraków",
                        "wrocław",
                        "poznań",
                        "gdańsk",
                        "remote",
                        "warsaw",
                    ]
                )
            )
            if location_elem:
                location = location_elem.strip()

            # Check if remote
            page_text = soup.get_text().lower()
            is_remote = "remote" in page_text or "zdalnie" in page_text

            # Extract experience level
            experience_level = "Not specified"
            for level in ["senior", "mid", "junior", "lead", "principal"]:
                if level in page_text:
                    experience_level = level
                    break

            return {
                "id": job_id,
                "title": title or "Position Available",
                "company": company or "Company",
                "description": description,
                "requirements": extract_requirements_from_description(description),
                "location": location,
                "remote": is_remote,
                "experience_level": experience_level,
                "skills_required": skills_required,
                "url": url,
            }

    except Exception as e:
        logger.error(f"Error fetching job details for {job_id}: {str(e)}")
        return None


def extract_requirements_from_description(description: str) -> List[str]:
    """
    Extract requirements from job description text

    Args:
        description: HTML or text job description

    Returns:
        List of requirement strings
    """
    if not description:
        return []

    # Parse HTML if present
    try:
        soup = BeautifulSoup(description, "html.parser")
        text = soup.get_text()
    except Exception:
        text = description

    # Look for requirements sections
    requirements = []
    lines = text.split("\n")

    in_requirements = False
    for line in lines:
        line = line.strip()

        # Detect requirements section
        if any(
            keyword in line.lower()
            for keyword in [
                "requirements",
                "required skills",
                "what we expect",
                "must have",
                "qualifications",
                "you should have",
            ]
        ):
            in_requirements = True
            continue

        # Detect end of requirements section
        if in_requirements and any(
            keyword in line.lower()
            for keyword in [
                "responsibilities",
                "what we offer",
                "benefits",
                "nice to have",
            ]
        ):
            in_requirements = False

        # Extract bullet points or numbered items
        if in_requirements and line:
            # Remove bullet points, numbers, etc.
            cleaned = line.lstrip("•-*0123456789.)").strip()
            if cleaned and len(cleaned) > 10:  # Ignore very short lines
                requirements.append(cleaned)

    return requirements


async def search_and_fetch_jobs(
    skills: List[str],
    location: str = "remote",
    experience_level: Optional[str] = None,
    limit: int = 5,
) -> List[Dict]:
    """
    Search for jobs and fetch full details for each

    Args:
        skills: List of skills to search for
        location: Job location filter
        experience_level: Experience level filter
        limit: Maximum number of jobs to fetch details for

    Returns:
        List of complete job dictionaries with descriptions
    """

    # First, search for jobs
    jobs = await search_justjoinit_jobs(skills, location, experience_level, limit)

    # If scraping failed, return empty list (caller will handle it gracefully)
    if not jobs:
        logger.warning("No jobs found from JustJoin.it scraping")
        return []

    # Then fetch details for each job
    detailed_jobs = []
    for job in jobs[:limit]:
        job_id = job.get("id")
        if job_id:
            details = await get_job_details(job_id)
            if details:
                detailed_jobs.append(details)
            else:
                # If we can't get full details, use what we have from search
                detailed_jobs.append(job)

            # Small delay to be respectful to the server
            await asyncio.sleep(1.0)  # Increased delay for web scraping

    return detailed_jobs
