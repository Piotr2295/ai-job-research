"""
Reasoning Agent with Agentic Loop for Job Analysis.

This agent can autonomously decide which tools to use based on the job analysis,
implements a decision loop, and provides orchestration for complex analysis.
"""

from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from app.agent_tools import (
    ToolType,
    execute_tool,
)
from app.agent_reflection import (
    validate_analysis,
    get_reflection_feedback,
    AnalysisValidation,
)
from app.agent_events import get_event_emitter, EventType
from dotenv import load_dotenv
import json
import re

load_dotenv()

# Lazy initialization of LLM
llm = None


def get_llm():
    global llm
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm


# AGENT STATE DEFINITION


class AgentState(TypedDict):
    """State for the agentic job analysis workflow"""

    # Input
    job_description: str
    current_skills: list[str]
    job_title: str
    location: str
    github_username: Optional[str]  # Optional GitHub username for enriched analysis

    # Core analysis results
    skills_required: list[str]
    skill_gaps: list[str]

    # Tool results storage
    rag_results: Optional[dict]
    skill_validation_results: Optional[dict]
    market_research_results: Optional[dict]
    gap_analysis_results: Optional[dict]
    learning_plan_results: Optional[dict]
    github_analysis_results: Optional[dict]  # GitHub profile analysis

    # Self-reflection & validation
    validation_report: Optional[dict]  # Complete validation report
    reflection_feedback: Optional[dict]  # Actionable feedback from validation
    analysis_quality_score: float
    analysis_confidence_score: float

    # Agent decision tracking
    tool_call_count: int
    max_tool_calls: int
    executed_tools: list[str]
    agent_reasoning: list[str]
    reflection_iterations: int  # Track how many times we've reflected

    # Final output
    learning_plan: str
    rag_evaluation: dict


# AGENT NODES (AGENTIC LOOP)


def extract_required_skills(state: AgentState) -> AgentState:
    """Step 1: Extract required skills from job description"""
    emitter = get_event_emitter()
    emitter.emit_event(
        EventType.NODE_START, node_name="extract_skills", status="processing"
    )

    try:
        llm_client = get_llm()

        prompt = f"""
        Extract all required technical and soft skills from this job description:

        JOB TITLE: {state['job_title']}
        LOCATION: {state['location']}

        DESCRIPTION:
        {state['job_description']}

        Return skills as a comma-separated list. Be specific and include both hard and soft skills.
        """

        response = llm_client.invoke(prompt)
        skills = [skill.strip() for skill in response.content.split(",")]

        state["skills_required"] = skills
        state["agent_reasoning"].append(
            f"Extracted {len(skills)} required skills from job description"
        )

        emitter.emit_event(
            EventType.NODE_END,
            node_name="extract_skills",
            status="completed",
            data={"skills_count": len(skills), "skills": skills[:5]},
        )

        return state
    except Exception as e:
        emitter.emit_event(
            EventType.NODE_ERROR, node_name="extract_skills", error=str(e)
        )
        raise


def agent_think(state: AgentState) -> AgentState:
    """Step 2: Agent analyzes what tools it needs (THINK phase)"""
    emitter = get_event_emitter()
    emitter.emit_event(EventType.NODE_START, node_name="think", status="processing")
    emitter.emit_event(
        EventType.THINKING,
        node_name="think",
        data={"message": "Analyzing which tools to use..."},
    )

    try:
        llm_client = get_llm()

        # Build context of what we know so far
        skill_gaps = set(state["skills_required"]) - set(state["current_skills"])

        # Check if GitHub analysis is available
        has_github = bool(state.get("github_username"))

        prompt = f"""
        You are a career development agent analyzing a job opportunity.

        JOB: {state['job_title']} at {state['location']}
        REQUIRED SKILLS: {', '.join(state['skills_required'])}
        CURRENT SKILLS: {', '.join(state['current_skills'])}
        SKILL GAPS: {', '.join(skill_gaps)}
        {'GITHUB PROFILE: Available - ' + state.get('github_username', '') if has_github else 'GITHUB PROFILE: Not provided'}

        AVAILABLE TOOLS:
        1. RAG_QUERY - Deep dive into learning resources and advanced insights
        2. SKILL_VALIDATOR - Validate skills, check relevance, prerequisites
        3. MARKET_RESEARCH - Research salary, trends, competitor skills
        4. GAP_ANALYZER - Detailed gap analysis with difficulty and priority
        5. LEARNING_PATH_GENERATOR - Create personalized learning plan
        6. GITHUB_ANALYZER - Analyze GitHub profile for proven skills and projects ({"AVAILABLE" if has_github else "NOT AVAILABLE - no username provided"})

        Previous tool calls: {len(state['executed_tools'])} / {state['max_tool_calls']}

        Decide which tools you need to call NEXT to build a comprehensive analysis.
        Think about what information you still need.
        {f"IMPORTANT: GitHub profile is available - consider using GITHUB_ANALYZER to validate actual skills from projects." if has_github else ""}

        Return JSON with:
        {{
            "reasoning": "why you're choosing these tools",
            "selected_tools": ["TOOL_NAME1", "TOOL_NAME2"],
            "should_continue": true/false,
            "next_action": "brief description of next action"
        }}
        """

        response = llm_client.invoke(prompt)

        try:
            # Parse agent decision
            decision_text = response.content
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", decision_text, re.DOTALL)
            if json_match:
                agent_decision = json.loads(json_match.group())
            else:
                # Fallback: default to comprehensive analysis
                agent_decision = {
                    "reasoning": "Insufficient information, running all tools",
                    "selected_tools": [
                        "GAP_ANALYZER",
                        "RAG_QUERY",
                        "SKILL_VALIDATOR",
                        "MARKET_RESEARCH",
                    ],
                    "should_continue": True,
                    "next_action": "Execute selected tools",
                }
        except Exception:
            agent_decision = {
                "reasoning": "Error parsing decision, using default tools",
                "selected_tools": ["GAP_ANALYZER", "RAG_QUERY"],
                "should_continue": True,
                "next_action": "Execute selected tools",
            }

        state["agent_reasoning"].append(agent_decision["reasoning"])

        emitter.emit_event(
            EventType.REASONING,
            node_name="think",
            data={
                "reasoning": agent_decision["reasoning"],
                "tools_selected": agent_decision.get("selected_tools", []),
            },
        )
        emitter.emit_event(EventType.NODE_END, node_name="think", status="completed")

        return state
    except Exception as e:
        emitter.emit_event(EventType.NODE_ERROR, node_name="think", error=str(e))
        raise


def agent_execute_tools(state: AgentState) -> AgentState:
    """Step 3: Execute selected tools (ACT phase)"""
    emitter = get_event_emitter()
    emitter.emit_event(
        EventType.NODE_START, node_name="execute_tools", status="processing"
    )

    try:
        # Parse which tools to execute
        # This would normally come from agent_think, but for MVP we run key tools
        tools_to_execute = [
            ToolType.GAP_ANALYZER,
            ToolType.RAG_QUERY,
            ToolType.SKILL_VALIDATOR,
        ]

        # Add GitHub analyzer if username is provided
        if state.get("github_username"):
            tools_to_execute.insert(0, ToolType.GITHUB_ANALYZER)

        state["tool_call_count"] += 1

        for tool_type in tools_to_execute:
            if state["tool_call_count"] >= state["max_tool_calls"]:
                break

            # Emit tool start event
            emitter.emit_event(
                EventType.TOOL_START, tool_name=tool_type.value, status="executing"
            )

            result = execute_tool(
                tool_type,
                required_skills=state["skills_required"],
                current_skills=state["current_skills"],
                job_description=state["job_description"],
                job_title=state["job_title"],
                location=state["location"],
                github_username=state.get("github_username", ""),
            )

            # Store results based on tool type
            if tool_type == ToolType.GAP_ANALYZER:
                state["gap_analysis_results"] = result["data"]
                state["skill_gaps"] = result["data"].get(
                    "identified_gaps", state["skill_gaps"]
                )
            elif tool_type == ToolType.RAG_QUERY:
                state["rag_results"] = result["data"]
            elif tool_type == ToolType.SKILL_VALIDATOR:
                state["skill_validation_results"] = result["data"]
            elif tool_type == ToolType.MARKET_RESEARCH:
                state["market_research_results"] = result["data"]
            elif tool_type == ToolType.LEARNING_PATH_GENERATOR:
                state["learning_plan_results"] = result["data"]
            elif tool_type == ToolType.GITHUB_ANALYZER:
                state["github_analysis_results"] = result["data"]
                # Enrich current_skills with proven GitHub skills if successful
                if result["success"] and "proven_skills" in result["data"]:
                    github_skills = result["data"]["proven_skills"].get(
                        "programming_languages", []
                    )
                    # Add GitHub-proven skills to current skills
                    enriched_skills = set(state["current_skills"])
                    enriched_skills.update(github_skills)
                    state["current_skills"] = list(enriched_skills)

            state["executed_tools"].append(tool_type.value)

            # Emit tool completion event
            emitter.emit_event(
                EventType.TOOL_END,
                tool_name=tool_type.value,
                status="completed" if result["success"] else "error",
                data={"success": result["success"]},
            )

        state["agent_reasoning"].append(f"Executed {len(tools_to_execute)} tools")

        emitter.emit_event(
            EventType.NODE_END,
            node_name="execute_tools",
            status="completed",
            data={"tools_executed": len(tools_to_execute)},
        )

        return state
    except Exception as e:
        emitter.emit_event(
            EventType.NODE_ERROR, node_name="execute_tools", error=str(e)
        )
        raise


def agent_reflect(state: AgentState) -> AgentState:
    """Step 4: Reflect on results and decide if more info needed (OBSERVE phase)"""
    emitter = get_event_emitter()
    emitter.emit_event(EventType.NODE_START, node_name="reflect", status="processing")

    try:
        llm_client = get_llm()

        # Check quality of information gathered
        has_gap_analysis = state["gap_analysis_results"] is not None
        has_rag_results = state["rag_results"] is not None
        has_skill_validation = state["skill_validation_results"] is not None
        has_github_analysis = state["github_analysis_results"] is not None

        info_quality = (
            sum(
                [
                    has_gap_analysis,
                    has_rag_results,
                    has_skill_validation,
                    has_github_analysis,
                ]
            )
            / 4
        )

        prompt = f"""
        Reflect on the analysis results gathered so far:

        Gap Analysis: {has_gap_analysis}
        RAG Insights: {has_rag_results}
        Skill Validation: {has_skill_validation}
        GitHub Analysis: {has_github_analysis}

        Information Quality Score: {info_quality:.2f}
        Tools Used: {', '.join(state['executed_tools'])}

        Is the information sufficient to generate a high-quality learning plan?
        Do we need to gather more insights?

        Respond with JSON:
        {{
            "quality_assessment": "score 0-1",
            "information_sufficient": true/false,
            "missing_insights": ["list of missing insights"],
            "confidence_in_plan": 0.0-1.0
        }}
        """

        response = llm_client.invoke(prompt)

        try:
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                reflection = json.loads(json_match.group())
                state["analysis_confidence_score"] = reflection.get(
                    "confidence_in_plan", 0.7
                )
        except Exception:
            state["analysis_confidence_score"] = info_quality

        state["agent_reasoning"].append("Reflected on analysis quality")

        emitter.emit_event(
            EventType.NODE_END,
            node_name="reflect",
            status="completed",
            data={
                "info_quality": info_quality,
                "confidence": state["analysis_confidence_score"],
            },
        )

        return state
    except Exception as e:
        emitter.emit_event(EventType.NODE_ERROR, node_name="reflect", error=str(e))
        raise


def generate_learning_plan(state: AgentState) -> AgentState:
    """Final step: Generate comprehensive learning plan based on all insights"""
    emitter = get_event_emitter()
    emitter.emit_event(
        EventType.NODE_START, node_name="generate_plan", status="processing"
    )

    try:
        llm_client = get_llm()

        # Compile all gathered insights including GitHub analysis
        github_summary = ""
        if state.get("github_analysis_results"):
            gh = state["github_analysis_results"]
            github_summary = f"""
        GITHUB ANALYSIS:
        - Profile: {gh.get('profile_url', 'N/A')}
        - Total Repos: {gh.get('metrics', {}).get('total_repos', 0)}
        - Languages: {', '.join([lang['name'] for lang in gh.get('languages', [])][:5])}
        - Proven Skills: {', '.join(gh.get('proven_skills', {}).get('programming_languages', []))}
        - Project Types: {', '.join(gh.get('project_types', []))}
        """

        insights = f"""
        SKILL GAPS: {', '.join(state['skill_gaps'])}

        RAG INSIGHTS: {state['rag_results'].get('rag_response', '') if state['rag_results'] else 'Not available'}

        SKILL VALIDATION: {state['skill_validation_results'].get('validation_analysis', '') if state['skill_validation_results'] else 'Not available'}

        GAP ANALYSIS: {state['gap_analysis_results'].get('gap_analysis', '') if state['gap_analysis_results'] else 'Not available'}
        {github_summary}
        """

        prompt = f"""
        Based on comprehensive analysis, create a detailed learning plan:

        JOB TARGET: {state['job_title']} at {state['location']}

        {insights}

        Generate a prioritized, actionable learning plan with:
        1. Phase-based approach (short-term, medium-term, long-term)
        2. Specific skills to learn in order
        3. Estimated time for each skill
        4. Learning resources and approaches
        5. Milestones and checkpoints
        6. Success metrics

        Make it practical and achievable.
        """

        response = llm_client.invoke(prompt)
        state["learning_plan"] = response.content
        state["agent_reasoning"].append("Generated comprehensive learning plan")

        emitter.emit_event(
            EventType.NODE_END,
            node_name="generate_plan",
            status="completed",
            data={"plan_length": len(response.content)},
        )

        return state
    except Exception as e:
        emitter.emit_event(
            EventType.NODE_ERROR, node_name="generate_plan", error=str(e)
        )
        raise


def self_validate_analysis(state: AgentState) -> AgentState:
    """
    Step 5: Self-validation & reflection on generated analysis.

    This node validates the quality of the analysis and identifies gaps or issues.
    If quality is low, it can trigger additional analysis or provide detailed feedback.
    """
    emitter = get_event_emitter()
    emitter.emit_event(EventType.NODE_START, node_name="validate", status="processing")

    try:
        # Run comprehensive validation
        validation_report: AnalysisValidation = validate_analysis(
            required_skills=state["skills_required"],
            current_skills=state["current_skills"],
            skill_gaps=state["skill_gaps"],
            learning_plan=state["learning_plan"],
            github_username=state.get("github_username"),
            rag_results=state.get("rag_results"),
            skill_validation=state.get("skill_validation_results"),
            market_research=state.get("market_research_results"),
            gap_analysis=state.get("gap_analysis_results"),
            github_analysis=state.get("github_analysis_results"),
        )

        # Store validation results
        state["validation_report"] = {
            "is_valid": validation_report.is_valid,
            "overall_quality_score": validation_report.overall_quality_score,
            "overall_confidence": validation_report.overall_confidence,
            "completeness_score": validation_report.completeness_score,
            "reliability_score": validation_report.reliability_score,
            "requires_revision": validation_report.requires_revision,
            "issues": [
                {
                    "risk_level": issue.risk_level.value,
                    "category": issue.category,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "impact_score": issue.impact_score,
                }
                for issue in validation_report.issues
            ],
            "recommendations": validation_report.recommendations,
            "validation_details": validation_report.validation_details,
        }

        # Get actionable feedback
        feedback = get_reflection_feedback(validation_report)
        state["reflection_feedback"] = {
            "should_revise": feedback["should_revise"],
            "revision_focus": feedback["revision_focus"],
            "missing_analysis": feedback["missing_analysis"],
            "strong_areas": feedback["strong_areas"],
            "weak_areas": feedback["weak_areas"],
            "action_items": feedback["action_items"],
        }

        # Update quality scores
        state["analysis_quality_score"] = validation_report.overall_quality_score
        state["analysis_confidence_score"] = validation_report.overall_confidence
        state["reflection_iterations"] += 1

        # Log reflection results
        state["agent_reasoning"].append(
            f"Validation complete: Quality={validation_report.overall_quality_score:.2f}, "
            f"Confidence={validation_report.overall_confidence:.2f}, "
            f"Issues={len(validation_report.issues)}"
        )

        if validation_report.requires_revision:
            state["agent_reasoning"].append(
                f"Revision needed - Focus areas: {', '.join(feedback['revision_focus'][:3])}"
            )

        emitter.emit_event(
            EventType.VALIDATION_RESULT,
            node_name="validate",
            status="completed",
            data={
                "quality_score": validation_report.overall_quality_score,
                "confidence": validation_report.overall_confidence,
                "issues_count": len(validation_report.issues),
                "requires_revision": validation_report.requires_revision,
            },
        )
        emitter.emit_event(EventType.NODE_END, node_name="validate", status="completed")

        return state
    except Exception as e:
        emitter.emit_event(EventType.NODE_ERROR, node_name="validate", error=str(e))
        raise


def router(state: AgentState) -> str:
    """Decide whether to continue agent loop or finish"""
    # Simple heuristic: if we've gathered enough info, finish
    if state["tool_call_count"] >= state["max_tool_calls"]:
        return "generate_plan"
    if state["gap_analysis_results"] and state["rag_results"]:
        return "generate_plan"
    return "execute_tools"


# BUILD THE AGENTIC GRAPH
def build_agent() -> Any:
    """Build the agentic job analysis workflow"""

    # Build graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("extract_skills", extract_required_skills)
    workflow.add_node("think", agent_think)
    workflow.add_node("execute_tools", agent_execute_tools)
    workflow.add_node("reflect", agent_reflect)
    workflow.add_node("generate_plan", generate_learning_plan)
    workflow.add_node("validate", self_validate_analysis)

    # Set entry point
    workflow.set_entry_point("extract_skills")

    # Define edges (agentic loop with validation)
    workflow.add_edge("extract_skills", "think")
    workflow.add_edge("think", "execute_tools")
    workflow.add_edge("execute_tools", "reflect")
    workflow.add_conditional_edges("reflect", router)
    workflow.add_edge("generate_plan", "validate")
    workflow.set_finish_point("validate")

    return workflow.compile()


# Create the compiled agent
agent = build_agent()
