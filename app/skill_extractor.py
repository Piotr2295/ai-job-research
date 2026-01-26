"""
Skill Extraction Module
Extracts technical and soft skills from resume text using LLM
"""

from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import re

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def extract_skills_from_resume(
    resume_text: str, sections: Optional[Dict[str, str]] = None
) -> Dict[str, List[str]]:
    """
    Extract structured skills from resume text

    Args:
        resume_text: Full text content of the resume
        sections: Optional pre-parsed sections from resume

    Returns:
        Dict with 'technical_skills', 'soft_skills', 'tools', and 'languages'
    """

    # Focus on skills section if available
    skills_section = ""
    if sections and "skills" in sections:
        skills_section = sections["skills"]

    prompt = f"""
    Analyze the following resume text and extract all skills in a structured format.
    
    RESUME TEXT:
    {resume_text}
    
    {f"SKILLS SECTION (focus here):\n{skills_section}\n" if skills_section else ""}

    Please extract and categorize skills into:
    1. **Technical Skills**: Programming languages, frameworks, databases, cloud platforms, etc.
    2. **Soft Skills**: Leadership, communication, problem-solving, teamwork, etc.
    3. **Tools**: Software tools, IDEs, project management tools, etc.
    4. **Languages**: Human languages (e.g., English, Spanish)

    Return your answer ONLY as a JSON object with this exact structure:
    {{
        "technical_skills": ["skill1", "skill2", ...],
        "soft_skills": ["skill1", "skill2", ...],
        "tools": ["tool1", "tool2", ...],
        "languages": ["language1", "language2", ...]
    }}

    Extract all skills mentioned throughout the resume, not just in the skills section.
    Be specific and comprehensive.
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    # Try to extract JSON from response
    try:
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        skills_data = json.loads(content)
        return skills_data
    except json.JSONDecodeError:
        # Fallback: try to parse manually
        return _fallback_skill_extraction(content)


def _fallback_skill_extraction(text: str) -> Dict[str, List[str]]:
    """Fallback skill extraction if JSON parsing fails"""
    skills_data: Dict[str, List[str]] = {
        "technical_skills": [],
        "soft_skills": [],
        "tools": [],
        "languages": [],
    }

    # Simple regex patterns for common skills
    # This is a basic fallback - the LLM should normally provide JSON
    lines = text.split("\n")
    current_category = None

    for line in lines:
        line = line.strip()
        if "technical" in line.lower():
            current_category = "technical_skills"
        elif "soft" in line.lower():
            current_category = "soft_skills"
        elif "tool" in line.lower():
            current_category = "tools"
        elif "language" in line.lower():
            current_category = "languages"
        elif line and current_category:
            # Extract items (comma or dash separated)
            items = re.split(r"[,;]|\s*-\s*", line)
            for item in items:
                item = item.strip(" -•*")
                if item and len(item) > 1:
                    skills_data[current_category].append(item)

    return skills_data


def get_all_skills_flat(skills_data: Dict[str, List[str]]) -> List[str]:
    """
    Get all skills as a flat list

    Args:
        skills_data: Structured skills dict from extract_skills_from_resume

    Returns:
        List of all skills combined
    """
    all_skills = []
    for category, skills in skills_data.items():
        all_skills.extend(skills)
    return all_skills


def extract_years_of_experience(resume_text: str) -> Dict[str, int]:
    """
    Extract years of experience for key technologies/skills

    Args:
        resume_text: Full resume text

    Returns:
        Dict mapping skill to years of experience
    """
    prompt = f"""
    Analyze the following resume and estimate years of experience for key technical skills.
    Look at dates in work experience and education sections.

    RESUME TEXT:
    {resume_text}

    Return a JSON object mapping each key skill to estimated years of experience:
    {{
        "Python": 5,
        "React": 3,
        "AWS": 2,
        ...
    }}

    Only include skills where you can reasonably estimate experience based on dates mentioned.
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)
    except json.JSONDecodeError:
        return {}
