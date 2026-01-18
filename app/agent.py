from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from app.prompts import SKILL_EXTRACTION_PROMPT, GAP_ANALYSIS_PROMPT, LEARNING_PLAN_PROMPT
from app.rag import retrieve_resources
import os

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

def analyze_gaps(state):
    current_skills = state.get("current_skills", [])
    prompt = GAP_ANALYSIS_PROMPT.format(
        required_skills=", ".join(state["skills_required"]),
        current_skills=", ".join(current_skills)
    )
    response = get_llm().invoke(prompt)
    gaps = [gap.strip() for gap in response.content.split(",")]
    state["skill_gaps"] = gaps
    return state

def generate_plan(state):
    prompt = LEARNING_PLAN_PROMPT.format(
        gaps=", ".join(state["skill_gaps"]),
        resources="\n".join(state["relevant_resources"])
    )
    response = get_llm().invoke(prompt)
    state["learning_plan"] = response.content
    return state

# Define the graph
graph = StateGraph(dict)
graph.add_node("extract_skills", extract_skills)
graph.add_node("retrieve_resources", retrieve_resources_node)
graph.add_node("analyze_gaps", analyze_gaps)
graph.add_node("generate_plan", generate_plan)

graph.set_entry_point("extract_skills")
graph.add_edge("extract_skills", "retrieve_resources")
graph.add_edge("retrieve_resources", "analyze_gaps")
graph.add_edge("analyze_gaps", "generate_plan")

agent = graph.compile()