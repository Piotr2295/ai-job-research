"""
Self-Reflection & Validation System for Agent Analysis.

This module provides quality assurance and validation for the agent's analysis,
including gap detection, confidence scoring, and analysis completeness checking.
"""

from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ValidationRisk(Enum):
    """Risk levels for validation issues"""

    CRITICAL = "critical"  # Analysis must be revised
    HIGH = "high"  # Significant quality issues
    MEDIUM = "medium"  # Minor quality issues
    LOW = "low"  # Negligible impact
    NONE = "none"  # No issues


@dataclass
class ValidationIssue:
    """Represents a validation issue found during analysis"""

    risk_level: ValidationRisk
    category: str  # e.g., "skill_gap_coverage", "resource_availability"
    description: str
    recommendation: str
    impact_score: float  # 0-1: how much this affects quality


@dataclass
class AnalysisValidation:
    """Complete validation report for an analysis"""

    is_valid: bool
    overall_quality_score: float  # 0-1
    overall_confidence: float  # 0-1
    issues: List[ValidationIssue]
    completeness_score: float  # 0-1 (what % of analysis is complete)
    reliability_score: float  # 0-1 (how trustworthy are the results)
    validation_details: Dict[str, Any]
    recommendations: List[str]
    requires_revision: bool  # Should analysis be revised?


class AnalysisMetrics(TypedDict):
    """Metrics for evaluating analysis quality"""

    # Coverage metrics
    skill_coverage: float  # % of required skills covered
    learning_resources_coverage: float  # % of skills with resources
    market_data_coverage: float  # % of market research done
    github_coverage: float  # % of GitHub profile analyzed

    # Depth metrics
    gap_analysis_depth: int  # Number of gaps analyzed
    resource_diversity: int  # Number of different resource types
    project_type_coverage: int  # Number of project types found

    # Validation metrics
    skill_validation_accuracy: float  # Confidence in skill validation
    prerequisite_coverage: float  # % of prerequisites identified
    time_estimation_confidence: float  # Confidence in time estimates

    # Confidence metrics
    overall_confidence: float  # Overall confidence in plan
    data_quality_score: float  # Quality of input data
    analysis_rigor_score: float  # Rigor of analysis process


class ReflectionFeedback(TypedDict):
    """Feedback from self-reflection analysis"""

    should_revise: bool
    revision_focus: List[str]  # Areas to focus on in revision
    missing_analysis: List[str]  # Missing analysis components
    strong_areas: List[str]  # Areas with strong analysis
    weak_areas: List[str]  # Areas with weak analysis
    action_items: List[str]  # Specific action items


def validate_skill_coverage(
    required_skills: List[str],
    gap_analysis: Optional[Dict[str, Any]],
    rag_results: Optional[Dict[str, Any]],
    github_analysis: Optional[Dict[str, Any]],
) -> tuple[float, List[ValidationIssue]]:
    """
    Validate that all required skills have been covered in analysis.

    Returns:
        (coverage_score, issues)
    """
    issues = []
    covered_skills = set()

    # Skills from gap analysis
    if gap_analysis and "identified_gaps" in gap_analysis:
        covered_skills.update(gap_analysis["identified_gaps"])

    # Skills from RAG results
    if rag_results and "resources" in rag_results:
        resources = rag_results["resources"]
        if isinstance(resources, list):
            for r in resources:
                if isinstance(r, dict):
                    covered_skills.add(r.get("topic", ""))
                elif isinstance(r, str):
                    covered_skills.add(r)

    # Skills from GitHub (proven skills)
    if github_analysis and "proven_skills" in github_analysis:
        gh_skills = github_analysis["proven_skills"]
        covered_skills.update(gh_skills.get("programming_languages", []))
        covered_skills.update(gh_skills.get("frameworks_and_tools", []))

    required_set = set(required_skills)
    covered_set = covered_skills & required_set
    coverage = len(covered_set) / len(required_set) if required_set else 1.0

    # Check for uncovered critical skills
    uncovered = required_set - covered_set
    if uncovered and len(uncovered) > len(required_set) * 0.3:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.HIGH,
                category="skill_coverage",
                description=f"More than 30% of required skills are uncovered: {', '.join(list(uncovered)[:5])}",
                recommendation="Run additional RAG queries or market research for uncovered skills",
                impact_score=0.7,
            )
        )

    return coverage, issues


def validate_learning_plan_quality(
    learning_plan: str,
    skill_gaps: List[str],
    github_analysis: Optional[Dict[str, Any]],
) -> tuple[float, List[ValidationIssue]]:
    """
    Validate the quality and completeness of the generated learning plan.

    Returns:
        (quality_score, issues)
    """
    issues = []
    quality_score = 0.5

    # Check length (should be reasonably detailed)
    if len(learning_plan) < 500:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.MEDIUM,
                category="plan_completeness",
                description="Learning plan is quite short (less than 500 characters)",
                recommendation="Generate a more detailed learning plan with phases and milestones",
                impact_score=0.4,
            )
        )
        quality_score = 0.3
    elif len(learning_plan) > 2000:
        quality_score = 0.9
    else:
        quality_score = 0.7

    # Check for key components
    plan_lower = learning_plan.lower()
    has_phases = any(
        p in plan_lower for p in ["phase", "week", "month", "short-term", "medium-term"]
    )
    has_resources = any(
        r in plan_lower for r in ["course", "tutorial", "book", "project", "practice"]
    )
    has_metrics = any(
        m in plan_lower
        for m in ["metric", "checkpoint", "milestone", "complete", "achieve"]
    )

    if not has_phases:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.MEDIUM,
                category="plan_structure",
                description="Learning plan lacks clear phase-based structure",
                recommendation="Organize plan into phases (short/medium/long term)",
                impact_score=0.3,
            )
        )
        quality_score -= 0.1

    if not has_resources:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.HIGH,
                category="resource_guidance",
                description="Learning plan does not reference specific learning resources",
                recommendation="Include specific courses, tutorials, books, or projects",
                impact_score=0.4,
            )
        )
        quality_score -= 0.2

    if not has_metrics:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.MEDIUM,
                category="success_criteria",
                description="Learning plan lacks clear success metrics or milestones",
                recommendation="Add checkpoints and success criteria for each phase",
                impact_score=0.3,
            )
        )
        quality_score -= 0.1

    return max(0.0, min(1.0, quality_score)), issues


def validate_github_integration(
    github_username: Optional[str],
    github_analysis: Optional[Dict[str, Any]],
    current_skills: List[str],
) -> tuple[float, List[ValidationIssue]]:
    """
    Validate that GitHub analysis was properly integrated (if available).

    Returns:
        (integration_quality, issues)
    """
    issues = []

    if not github_username:
        return 1.0, []  # No GitHub = nothing to validate

    if not github_analysis:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.HIGH,
                category="github_analysis_missing",
                description="GitHub username provided but analysis was not completed",
                recommendation="Retry GitHub analysis or check API availability",
                impact_score=0.6,
            )
        )
        return 0.3, issues

    # Check if GitHub skills were incorporated
    proven_skills = github_analysis.get("proven_skills", {})
    gh_languages = set(proven_skills.get("programming_languages", []))

    if not gh_languages:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.MEDIUM,
                category="github_skill_extraction",
                description="No programming languages found in GitHub analysis",
                recommendation="Verify GitHub profile has repositories with language data",
                impact_score=0.3,
            )
        )
        return 0.5, issues

    # Check if skills were merged with current skills
    integration_score = len(gh_languages & set(current_skills)) / max(
        1, len(gh_languages)
    )

    if integration_score < 0.5:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.LOW,
                category="github_skill_alignment",
                description="GitHub-proven skills not well aligned with current skills",
                recommendation="This may indicate GitHub profile doesn't match self-reported skills",
                impact_score=0.2,
            )
        )

    return min(1.0, integration_score + 0.5), issues


def validate_data_sources(
    rag_results: Optional[Dict[str, Any]],
    skill_validation: Optional[Dict[str, Any]],
    market_research: Optional[Dict[str, Any]],
    gap_analysis: Optional[Dict[str, Any]],
) -> tuple[float, List[ValidationIssue]]:
    """
    Validate that sufficient data sources were used in the analysis.

    Returns:
        (source_quality, issues)
    """
    issues = []
    sources_available = sum(
        [
            rag_results is not None,
            skill_validation is not None,
            market_research is not None,
            gap_analysis is not None,
        ]
    )

    source_quality = sources_available / 4.0

    if sources_available < 2:
        issues.append(
            ValidationIssue(
                risk_level=ValidationRisk.CRITICAL,
                category="insufficient_data_sources",
                description=f"Only {sources_available} out of 4 data sources are available",
                recommendation="Ensure analysis includes gap analysis and RAG queries at minimum",
                impact_score=0.8,
            )
        )

    # Check data quality/completeness
    if rag_results and "resources" in rag_results:
        resources = rag_results["resources"]
        resource_count = len(resources) if isinstance(resources, list) else 0
        if resource_count < 3:
            issues.append(
                ValidationIssue(
                    risk_level=ValidationRisk.MEDIUM,
                    category="insufficient_resources",
                    description="RAG query returned fewer than 3 learning resources",
                    recommendation="Run additional RAG queries or use different search terms",
                    impact_score=0.3,
                )
            )
            source_quality -= 0.1

    return max(0.0, min(1.0, source_quality)), issues


def calculate_analysis_metrics(
    required_skills: List[str],
    skill_gaps: List[str],
    rag_results: Optional[Dict[str, Any]],
    skill_validation: Optional[Dict[str, Any]],
    market_research: Optional[Dict[str, Any]],
    gap_analysis: Optional[Dict[str, Any]],
    github_analysis: Optional[Dict[str, Any]],
) -> AnalysisMetrics:
    """Calculate comprehensive metrics for analysis quality."""

    # Coverage metrics
    skill_coverage = len(skill_gaps) / len(required_skills) if required_skills else 1.0

    learning_resources = 0
    if rag_results and "resources" in rag_results:
        resources = rag_results["resources"]
        learning_resources = len(resources) if isinstance(resources, list) else 0
    resources_coverage = min(1.0, learning_resources / max(1, len(skill_gaps)))

    market_coverage = 1.0 if market_research else 0.0
    github_coverage = 1.0 if github_analysis else 0.5  # 0.5 if not provided

    # Depth metrics
    gap_depth = len(gap_analysis.get("identified_gaps", [])) if gap_analysis else 0

    # Calculate resource diversity safely
    resource_diversity = 0
    if rag_results and "resources" in rag_results:
        resources = rag_results.get("resources", [])
        if isinstance(resources, list):
            resource_diversity = len(
                set(r.get("type", "") if isinstance(r, dict) else "" for r in resources)
            )

    project_types = (
        len(github_analysis.get("project_types", [])) if github_analysis else 0
    )

    # Validation metrics
    validation_accuracy = 1.0 if skill_validation else 0.0
    prerequisites = len(gap_analysis.get("prerequisites", [])) if gap_analysis else 0
    prerequisite_coverage = min(1.0, prerequisites / max(1, len(skill_gaps)))
    time_confidence = 0.8 if gap_analysis and "time_estimates" in gap_analysis else 0.3

    # Overall confidence
    data_sources_used = sum(
        [
            rag_results is not None,
            skill_validation is not None,
            market_research is not None,
            gap_analysis is not None,
            github_analysis is not None,
        ]
    )
    overall_confidence = min(1.0, data_sources_used / 4.0)
    data_quality = min(1.0, (learning_resources / 5.0) + 0.5)
    analysis_rigor = min(1.0, (gap_depth / 5.0) + 0.5)

    return {
        "skill_coverage": skill_coverage,
        "learning_resources_coverage": resources_coverage,
        "market_data_coverage": market_coverage,
        "github_coverage": github_coverage,
        "gap_analysis_depth": gap_depth,
        "resource_diversity": resource_diversity,
        "project_type_coverage": project_types,
        "skill_validation_accuracy": validation_accuracy,
        "prerequisite_coverage": prerequisite_coverage,
        "time_estimation_confidence": time_confidence,
        "overall_confidence": overall_confidence,
        "data_quality_score": data_quality,
        "analysis_rigor_score": analysis_rigor,
    }


def validate_analysis(
    required_skills: List[str],
    current_skills: List[str],
    skill_gaps: List[str],
    learning_plan: str,
    github_username: Optional[str],
    rag_results: Optional[Dict[str, Any]],
    skill_validation: Optional[Dict[str, Any]],
    market_research: Optional[Dict[str, Any]],
    gap_analysis: Optional[Dict[str, Any]],
    github_analysis: Optional[Dict[str, Any]],
) -> AnalysisValidation:
    """
    Comprehensive validation of the entire analysis.

    Returns:
        Complete validation report with quality scores, issues, and recommendations.
    """
    all_issues: List[ValidationIssue] = []

    # Run all validators
    skill_coverage, coverage_issues = validate_skill_coverage(
        required_skills, gap_analysis, rag_results, github_analysis
    )
    all_issues.extend(coverage_issues)

    plan_quality, plan_issues = validate_learning_plan_quality(
        learning_plan, skill_gaps, github_analysis
    )
    all_issues.extend(plan_issues)

    github_quality, github_issues = validate_github_integration(
        github_username, github_analysis, current_skills
    )
    all_issues.extend(github_issues)

    source_quality, source_issues = validate_data_sources(
        rag_results, skill_validation, market_research, gap_analysis
    )
    all_issues.extend(source_issues)

    # Calculate metrics
    metrics = calculate_analysis_metrics(
        required_skills,
        skill_gaps,
        rag_results,
        skill_validation,
        market_research,
        gap_analysis,
        github_analysis,
    )

    # Determine overall scores
    completeness_score = min(
        1.0, (skill_coverage + source_quality + plan_quality) / 3.0
    )
    reliability_score = min(
        1.0,
        (
            github_quality
            + metrics["data_quality_score"]
            + metrics["analysis_rigor_score"]
        )
        / 3.0,
    )
    overall_quality = (completeness_score + reliability_score) / 2.0
    overall_confidence = metrics["overall_confidence"]

    # Determine if revision needed
    critical_issues = [i for i in all_issues if i.risk_level == ValidationRisk.CRITICAL]
    high_risk_issues = [i for i in all_issues if i.risk_level == ValidationRisk.HIGH]
    requires_revision = len(critical_issues) > 0 or (
        len(high_risk_issues) > 1 and overall_quality < 0.6
    )

    # Generate recommendations
    recommendations = []
    if plan_quality < 0.6:
        recommendations.append(
            "Regenerate learning plan with more detail and structure"
        )
    if skill_coverage < 0.7:
        recommendations.append("Perform additional RAG queries for uncovered skills")
    if source_quality < 0.5:
        recommendations.append("Run market research and skill validation tools")
    if github_quality < 0.5 and github_username:
        recommendations.append("Retry GitHub profile analysis")
    if not recommendations:
        recommendations.append("Analysis looks good - proceed with learning plan")

    return AnalysisValidation(
        is_valid=not requires_revision and overall_quality > 0.5,
        overall_quality_score=overall_quality,
        overall_confidence=overall_confidence,
        issues=all_issues,
        completeness_score=completeness_score,
        reliability_score=reliability_score,
        validation_details=metrics,
        recommendations=recommendations,
        requires_revision=requires_revision,
    )


def get_reflection_feedback(validation: AnalysisValidation) -> ReflectionFeedback:
    """Convert validation report into actionable reflection feedback."""

    # Categorize issues
    strong_areas = []
    weak_areas = []

    issue_categories = {}
    for issue in validation.issues:
        if issue.category not in issue_categories:
            issue_categories[issue.category] = []
        issue_categories[issue.category].append(issue)

    # Identify strengths
    if validation.completeness_score > 0.8:
        strong_areas.append("Analysis completeness")
    if validation.reliability_score > 0.8:
        strong_areas.append("Data reliability")
    if not any(i for i in validation.issues if i.risk_level == ValidationRisk.CRITICAL):
        strong_areas.append("No critical issues")

    # Identify weaknesses
    for category, issues in issue_categories.items():
        avg_risk = sum(
            i.risk_level.value == "critical" or i.risk_level.value == "high"
            for i in issues
        ) / len(issues)
        if avg_risk > 0.5:
            weak_areas.append(category)

    missing_components = [
        r
        for r in validation.recommendations
        if "additional" in r.lower() or "perform" in r.lower()
    ]
    revision_focus = [
        i.category
        for i in validation.issues
        if i.risk_level in [ValidationRisk.CRITICAL, ValidationRisk.HIGH]
    ]

    return {
        "should_revise": validation.requires_revision,
        "revision_focus": revision_focus,
        "missing_analysis": missing_components,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "action_items": validation.recommendations,
    }
