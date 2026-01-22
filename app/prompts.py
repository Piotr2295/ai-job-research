SKILL_EXTRACTION_PROMPT = """
Extract the key skills and technologies required from this job description.
Focus on technical skills, tools, and frameworks mentioned.
Return as a comma-separated list.

Job Description:
{job_description}
"""

GAP_ANALYSIS_PROMPT = """
Compare the required skills with the current skills and identify gaps.

Required Skills: {required_skills}
Current Skills: {current_skills}

Return the skill gaps as a comma-separated list.
"""

LEARNING_PLAN_PROMPT = """
Based on the skill gaps and relevant resources, create a concise learning plan.

Skill Gaps: {gaps}
Relevant Resources: {resources}

Provide a step-by-step learning plan.
"""
