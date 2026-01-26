import pdfplumber
import PyPDF2
from typing import Dict, List
from app.models import UserExperience
import re
import io


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using pdfplumber (better for structured text)"""
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        # Fallback to PyPDF2 if pdfplumber fails
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e2:
            raise Exception(f"Failed to extract text from PDF: {str(e)}, {str(e2)}")


def parse_resume_sections(text: str) -> Dict[str, str]:
    """Parse resume text into sections"""
    sections = {}

    # Common section headers (case insensitive)
    section_patterns = {
        "experience": (
            r"(?i)(?:experience|work experience|professional experience|employment)"
        ),
        "education": r"(?i)(?:education|academic background|degrees)",
        "skills": r"(?i)(?:skills|technical skills|competencies|expertise)",
        "projects": r"(?i)(?:projects|personal projects|key projects)",
        "certifications": r"(?i)(?:certifications|certificates|licenses)",
        "summary": r"(?i)(?:summary|professional summary|objective|profile)",
        "contact": r"(?i)(?:contact|contact information)",
    }

    # Split text into lines
    lines = text.split("\n")
    current_section = "general"
    current_content: List[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this line is a section header
        found_section = None
        for section_name, pattern in section_patterns.items():
            if re.match(pattern, line):
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []

                current_section = section_name
                found_section = section_name
                break

        if found_section is None:
            current_content.append(line)

    # Save the last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def extract_experiences_from_text(text: str) -> List[UserExperience]:
    """Extract work experiences from resume text using LLM or regex patterns"""
    experiences = []

    # Simple regex-based extraction (can be enhanced with LLM)
    # Look for patterns like "Company Name - Role (dates)"
    # or "Role at Company Name (dates)"

    experience_patterns = [
        r"(.+?)\s*[-–]\s*(.+?)\s*\((.+?)\)",  # Company - Role (dates)
        r"(.+?)\s*at\s*(.+?)\s*\((.+?)\)",  # Role at Company (dates)
        r"(.+?)\s*[-–]\s*(.+?)\s*[,;]\s*(.+?)",  # Company - Role, dates
    ]

    for pattern in experience_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) >= 3:
                role = match[1].strip()
                company = match[0].strip()
                duration = match[2].strip()

                # Extract achievements (lines following the role/company)
                # This is a simplified approach - could be enhanced
                achievements: List[str] = []

                experiences.append(
                    UserExperience(
                        role=role,
                        company=company,
                        duration=duration,
                        achievements=achievements,
                        skills=[],
                    )
                )

    return experiences


def parse_resume(file_content: bytes, filename: str) -> Dict:
    """Main function to parse resume PDF"""
    # Extract text
    full_text = extract_text_from_pdf(file_content)

    # Parse sections
    sections = parse_resume_sections(full_text)

    # Extract structured experiences
    extracted_experiences = extract_experiences_from_text(full_text)

    return {
        "full_text": full_text,
        "sections": sections,
        "extracted_experiences": extracted_experiences,
        "filename": filename,
    }
