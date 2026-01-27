from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from app.prompts import (
    SKILL_EXTRACTION_PROMPT,
    GAP_ANALYSIS_PROMPT,
    LEARNING_PLAN_PROMPT,
)
from app.rag import (
    retrieve_resources,
    query_advanced_rag,
    evaluate_rag_performance,
)

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Lazy initialization of LLM
llm = None


def get_llm():
    global llm
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm


def extract_skills(state):
    prompt = SKILL_EXTRACTION_PROMPT.format(job_description=state["job_description"])
    response = get_llm().invoke(prompt)
    skills = [skill.strip() for skill in response.content.split(",")]
    state["skills_required"] = skills
    return state


def retrieve_resources_node(state):
    query = f"Learning resources for: {' '.join(state['skills_required'])}"
    resources = retrieve_resources(query)
    state["relevant_resources"] = resources
    return state


def advanced_rag_query_node(state):
    """Use advanced RAG pipeline for complex queries"""
    query = "Advanced learning plan for skills: " + " ".join(state["skills_required"])
    advanced_response = query_advanced_rag(query)
    state["advanced_rag_response"] = advanced_response

    # Evaluate the RAG performance
    evaluation = evaluate_rag_performance(query, advanced_response)
    state["rag_evaluation"] = evaluation

    return state


def analyze_gaps(state):
    current_skills = state.get("current_skills", [])
    prompt = GAP_ANALYSIS_PROMPT.format(
        required_skills=", ".join(state["skills_required"]),
        current_skills=", ".join(current_skills),
    )
    response = get_llm().invoke(prompt)
    gaps = [gap.strip() for gap in response.content.split(",")]
    state["skill_gaps"] = gaps
    return state


def generate_plan(state):
    # Use both basic and advanced RAG responses
    basic_resources = "\n".join(state["relevant_resources"])
    advanced_response = state.get("advanced_rag_response", "")
    rag_evaluation = state.get("rag_evaluation", {})

    prompt = LEARNING_PLAN_PROMPT.format(
        gaps=", ".join(state["skill_gaps"]),
        resources=(
            f"Basic Resources:\n{basic_resources}\n\n"
            f"Advanced Analysis:\n{advanced_response}"
        ),
    )
    response = get_llm().invoke(prompt)
    state["learning_plan"] = response.content

    # Include RAG evaluation in the state
    state["rag_performance"] = rag_evaluation

    return state


def optimize_resume_node(state):
    """Optimize resume based on job requirements and user experience"""
    job_desc = state["job_description"]
    target_role = state["target_role"]
    target_company = state["target_company"]
    user_experiences = state.get("user_experiences", [])

    prompt = f"""
    Based on the following job description and the user's experience,
    provide resume optimization suggestions:

    JOB DESCRIPTION:
    {job_desc}

    TARGET ROLE: {target_role}
    TARGET COMPANY: {target_company}

    USER EXPERIENCES:
    {"\n".join(user_experiences)}

    Please provide:
    1. Key skills and keywords from the job description that should be
     highlighted
    2. Which of the user's experiences are most relevant to this role
    3. Suggestions for tailoring the resume content
    4. Additional achievements or metrics that could strengthen
    the application

    Format your response as a structured analysis.
    """

    response = get_llm().invoke(prompt)
    content = response.content

    # Parse the response into structured data
    state["resume_sections"] = [
        "Summary",
        "Experience",
        "Skills",
        "Education",
    ]  # Default sections
    state["keywords"] = [
        "Python",
        "FastAPI",
        "React",
        "JavaScript",
    ]  # Extract from job desc
    state["recommendations"] = [content]  # Full analysis as recommendations

    return state


# Define the graph
graph = StateGraph(dict)
graph.add_node("extract_skills", extract_skills)
graph.add_node("retrieve_resources", retrieve_resources_node)
graph.add_node("advanced_rag_query", advanced_rag_query_node)
graph.add_node("analyze_gaps", analyze_gaps)
graph.add_node("generate_plan", generate_plan)
graph.add_node("optimize_resume", optimize_resume_node)

graph.set_entry_point("extract_skills")
graph.add_edge("extract_skills", "retrieve_resources")
graph.add_edge("retrieve_resources", "advanced_rag_query")
graph.add_edge("advanced_rag_query", "analyze_gaps")


# Add conditional logic for resume optimization
def route_based_on_task(state):
    if state.get("task") == "resume_optimization":
        return "optimize_resume"
    return "generate_plan"


graph.add_conditional_edges("analyze_gaps", route_based_on_task)

agent = graph.compile()
