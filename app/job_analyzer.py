"""
Job Description Analysis Module
Extracts structured requirements and skills from job descriptions
"""

from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def analyze_job_description(
    job_description: str, job_title: Optional[str] = None, company: Optional[str] = None
) -> Dict:
    """
    Analyze job description and extract structured requirements

    Args:
        job_description: Full job description text
        job_title: Optional job title for context
        company: Optional company name for context

    Returns:
        Dict with extracted information including required skills, nice-to-have skills,
        responsibilities, qualifications, experience required, etc.
    """

    context = ""
    if job_title:
        context += f"Job Title: {job_title}\n"
    if company:
        context += f"Company: {company}\n"

    prompt = f"""
    Analyze the following job description and extract structured information.

    {context}
    JOB DESCRIPTION:
    {job_description}

    Please extract and structure the following information:

    1. **Required Technical Skills**: Must-have technical skills, programming languages, frameworks, tools
    2. **Required Soft Skills**: Communication, leadership, teamwork, etc.
    3. **Nice-to-Have Skills**: Preferred but not required skills
    4. **Years of Experience**: Required years of experience (if mentioned)
    5. **Education Requirements**: Degree requirements, certifications
    6. **Key Responsibilities**: Main duties and responsibilities
    7. **Technologies**: Specific technologies, platforms, databases mentioned
    8. **Domain Knowledge**: Industry-specific knowledge required

    Return your answer ONLY as a JSON object with this exact structure:
    {{
        "required_technical_skills": ["skill1", "skill2", ...],
        "required_soft_skills": ["skill1", "skill2", ...],
        "nice_to_have_skills": ["skill1", "skill2", ...],
        "years_of_experience": "X years" or "Not specified",
        "education_requirements": ["requirement1", ...],
        "key_responsibilities": ["responsibility1", ...],
        "technologies": ["tech1", "tech2", ...],
        "domain_knowledge": ["domain1", ...]
    }}

    Be comprehensive and specific. Extract all relevant details.
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    try:
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        job_analysis = json.loads(content)
        return job_analysis
    except json.JSONDecodeError:
        # Fallback structure
        return {
            "required_technical_skills": [],
            "required_soft_skills": [],
            "nice_to_have_skills": [],
            "years_of_experience": "Not specified",
            "education_requirements": [],
            "key_responsibilities": [],
            "technologies": [],
            "domain_knowledge": [],
        }


def compare_skills_with_job(
    user_skills: Dict[str, List[str]], job_requirements: Dict
) -> Dict:
    """
    Compare user skills with job requirements to identify matches and gaps

    Args:
        user_skills: Dict from skill_extractor.extract_skills_from_resume
        job_requirements: Dict from analyze_job_description

    Returns:
        Dict with matching_skills, skill_gaps, strength_areas, improvement_areas
    """

    # Flatten user skills
    all_user_skills = []
    for category, skills in user_skills.items():
        all_user_skills.extend([s.lower() for s in skills])

    user_skill_set = set(all_user_skills)

    # Get job required skills
    required_technical = [
        s.lower() for s in job_requirements.get("required_technical_skills", [])
    ]
    required_soft = [
        s.lower() for s in job_requirements.get("required_soft_skills", [])
    ]
    nice_to_have = [s.lower() for s in job_requirements.get("nice_to_have_skills", [])]
    technologies = [s.lower() for s in job_requirements.get("technologies", [])]

    all_required = set(required_technical + required_soft + technologies)
    nice_to_have_set = set(nice_to_have)

    # Calculate matches and gaps
    matching_required = user_skill_set.intersection(all_required)
    missing_required = all_required - user_skill_set
    matching_nice_to_have = user_skill_set.intersection(nice_to_have_set)

    # Calculate match percentage
    if all_required:
        match_percentage = (len(matching_required) / len(all_required)) * 100
    else:
        match_percentage = 0

    return {
        "matching_skills": list(matching_required),
        "skill_gaps": list(missing_required),
        "nice_to_have_matches": list(matching_nice_to_have),
        "match_percentage": round(match_percentage, 1),
        "strength_areas": _categorize_strengths(matching_required, job_requirements),
        "improvement_areas": _categorize_gaps(missing_required, job_requirements),
    }


def _categorize_strengths(matching_skills: set, job_requirements: Dict) -> List[str]:
    """Categorize matching skills into strength areas"""
    strengths = []

    tech_skills = set(
        s.lower() for s in job_requirements.get("required_technical_skills", [])
    )
    soft_skills = set(
        s.lower() for s in job_requirements.get("required_soft_skills", [])
    )

    tech_matches = matching_skills.intersection(tech_skills)
    soft_matches = matching_skills.intersection(soft_skills)

    if tech_matches:
        strengths.append(f"Technical Skills: {', '.join(tech_matches)}")
    if soft_matches:
        strengths.append(f"Soft Skills: {', '.join(soft_matches)}")

    return strengths


def _categorize_gaps(missing_skills: set, job_requirements: Dict) -> List[str]:
    """Categorize missing skills into improvement areas"""
    gaps = []

    tech_skills = set(
        s.lower() for s in job_requirements.get("required_technical_skills", [])
    )
    soft_skills = set(
        s.lower() for s in job_requirements.get("required_soft_skills", [])
    )
    technologies = set(s.lower() for s in job_requirements.get("technologies", []))

    tech_gaps = missing_skills.intersection(tech_skills)
    soft_gaps = missing_skills.intersection(soft_skills)
    tech_stack_gaps = missing_skills.intersection(technologies)

    if tech_gaps:
        gaps.append(f"Technical Skills: {', '.join(tech_gaps)}")
    if soft_gaps:
        gaps.append(f"Soft Skills: {', '.join(soft_gaps)}")
    if tech_stack_gaps:
        gaps.append(f"Technology Stack: {', '.join(tech_stack_gaps)}")

    return gaps


def generate_skill_gap_analysis(
    user_skills: Dict[str, List[str]],
    job_requirements: Dict,
    job_title: str = "the position",
    company: str = "the company",
) -> str:
    """
    Generate a comprehensive skill gap analysis report

    Args:
        user_skills: User's extracted skills
        job_requirements: Job requirements from analyze_job_description
        job_title: Job title for context
        company: Company name for context

    Returns:
        Formatted analysis report as string
    """

    comparison = compare_skills_with_job(user_skills, job_requirements)

    prompt = f"""
    Generate a comprehensive skill gap analysis report for a job application.

    JOB: {job_title} at {company}

    USER'S SKILLS:
    {json.dumps(user_skills, indent=2)}

    JOB REQUIREMENTS:
    {json.dumps(job_requirements, indent=2)}

    SKILL COMPARISON:
    - Match Percentage: {comparison['match_percentage']}%
    - Matching Skills: {comparison['matching_skills']}
    - Missing Required Skills: {comparison['skill_gaps']}
    - Nice-to-Have Matches: {comparison['nice_to_have_matches']}

    Please provide:
    1. Executive Summary of the candidate's fit for this role
    2. Detailed analysis of strengths (matching skills)
    3. Detailed analysis of skill gaps (missing required skills)
    4. Recommendations for closing the skill gaps
    5. Learning priority (which skills to focus on first)
    6. Timeline estimate for becoming job-ready

    Format the response as a clear, professional analysis report.
    """

    response = llm.invoke(prompt)
    return response.content
