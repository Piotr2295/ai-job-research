"""
Tests for Self-Reflection & Validation System
"""

import pytest
from app.agent_reflection import (
    validate_skill_coverage,
    validate_learning_plan_quality,
    validate_github_integration,
    validate_data_sources,
    calculate_analysis_metrics,
    validate_analysis,
    get_reflection_feedback,
    ValidationRisk,
)


class TestSkillCoverage:
    """Test skill coverage validation"""

    def test_full_coverage(self):
        """Test with all required skills covered"""
        required_skills = ["Python", "Django", "PostgreSQL"]
        gap_analysis = {"identified_gaps": ["Python", "Django"]}
        rag_results = {"resources": [{"topic": "PostgreSQL"}]}
        
        coverage, issues = validate_skill_coverage(
            required_skills, gap_analysis, rag_results, None
        )
        
        assert coverage == 1.0
        assert len(issues) == 0

    def test_partial_coverage(self):
        """Test with partial skill coverage"""
        required_skills = ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes"]
        gap_analysis = {"identified_gaps": ["Python", "Django"]}
        rag_results = None
        
        coverage, issues = validate_skill_coverage(
            required_skills, gap_analysis, rag_results, None
        )
        
        assert coverage < 1.0
        assert len(issues) > 0  # Should flag uncovered skills

    def test_no_coverage(self):
        """Test with no skills covered"""
        required_skills = ["Python", "Django", "PostgreSQL"]
        
        coverage, issues = validate_skill_coverage(
            required_skills, None, None, None
        )
        
        assert coverage == 0.0

    def test_github_skill_inclusion(self):
        """Test that GitHub skills are included in coverage calculation"""
        required_skills = ["Python", "JavaScript", "React"]
        gap_analysis = {"identified_gaps": ["Python"]}
        github_analysis = {
            "proven_skills": {
                "programming_languages": ["JavaScript", "React"],
            }
        }
        
        coverage, issues = validate_skill_coverage(
            required_skills, gap_analysis, None, github_analysis
        )
        
        assert coverage == 1.0
        assert len(issues) == 0


class TestLearningPlanQuality:
    """Test learning plan quality validation"""

    def test_comprehensive_plan(self):
        """Test with a comprehensive learning plan"""
        plan = """
        LEARNING PLAN FOR PYTHON DEVELOPER
        
        SHORT-TERM (1-2 months):
        - Week 1-2: Python fundamentals course
        - Week 3-4: Data structures practice
        
        MEDIUM-TERM (3-4 months):
        - Deploy Django project
        - PostgreSQL optimization
        
        LONG-TERM (5-6 months):
        - Build production system
        
        RESOURCES:
        - Coursera Python course
        - Django documentation
        - LeetCode for practice
        
        MILESTONES:
        - Complete course in 2 weeks
        - Deploy project in month 2
        - Build full system by month 6
        """
        skill_gaps = ["Python", "Django", "PostgreSQL"]
        
        quality, issues = validate_learning_plan_quality(plan, skill_gaps, None)
        
        assert quality >= 0.7
        assert len([i for i in issues if i.risk_level == ValidationRisk.CRITICAL]) == 0

    def test_minimal_plan(self):
        """Test with a minimal learning plan"""
        plan = "Learn the required skills"
        skill_gaps = ["Python", "Django", "PostgreSQL"]
        
        quality, issues = validate_learning_plan_quality(plan, skill_gaps, None)
        
        assert quality < 0.5
        # Should have issues
        assert len(issues) > 0
        # Should have issues for lack of structure
        assert any("phase" in i.description.lower() for i in issues)

    def test_plan_with_resources(self):
        """Test plan that includes learning resources"""
        plan = """
        Phase 1: Complete Coursera Python course (3 weeks)
        Phase 2: Django tutorial from official docs (2 weeks)
        Phase 3: PostgreSQL course on Udemy (2 weeks)
        
        Checkpoint 1: Build simple Flask app
        Checkpoint 2: Deploy Django project
        """
        skill_gaps = ["Python", "Django", "PostgreSQL"]
        
        quality, issues = validate_learning_plan_quality(plan, skill_gaps, None)
        
        assert quality > 0.2  # Has some resources and structure
        assert not any(i.risk_level == ValidationRisk.CRITICAL for i in issues)


class TestGitHubIntegration:
    """Test GitHub integration validation"""

    def test_no_github_provided(self):
        """Test when no GitHub username is provided"""
        quality, issues = validate_github_integration(None, None, [])
        
        assert quality == 1.0
        assert len(issues) == 0

    def test_github_username_without_analysis(self):
        """Test when GitHub username provided but analysis failed"""
        quality, issues = validate_github_integration(
            "johndoe", None, ["Python", "JavaScript"]
        )
        
        assert quality < 0.5
        assert len(issues) > 0
        assert any(i.risk_level == ValidationRisk.HIGH for i in issues)

    def test_github_analysis_successful(self):
        """Test successful GitHub analysis"""
        github_analysis = {
            "proven_skills": {
                "programming_languages": ["Python", "JavaScript"],
                "frameworks_and_tools": ["Django", "React"],
            },
        }
        current_skills = ["Python", "JavaScript"]
        
        quality, issues = validate_github_integration(
            "johndoe", github_analysis, current_skills
        )
        
        assert quality > 0.5
        assert len(issues) == 0

    def test_github_skills_mismatch(self):
        """Test when GitHub skills don't match reported skills"""
        github_analysis = {
            "proven_skills": {
                "programming_languages": ["Go", "Rust"],
            },
        }
        current_skills = ["Python", "JavaScript"]
        
        quality, issues = validate_github_integration(
            "johndoe", github_analysis, current_skills
        )
        
        # Should have lower quality (Go and Rust not in current skills)
        # Might or might not have issues depending on thresholds
        assert quality < 1.0


class TestDataSources:
    """Test data source validation"""

    def test_all_sources_available(self):
        """Test when all data sources are available"""
        rag_results = {"resources": [{"topic": "Python"}, {"topic": "Django"}, {"topic": "PostgreSQL"}]}
        skill_validation = {"validation": "data"}
        market_research = {"salary": "data"}
        gap_analysis = {"gaps": []}
        
        quality, issues = validate_data_sources(
            rag_results, skill_validation, market_research, gap_analysis
        )
        
        assert quality >= 0.8
        # May or may not have issues depending on resource count
        assert len([i for i in issues if i.risk_level.value == "critical"]) == 0

    def test_insufficient_sources(self):
        """Test when insufficient data sources are available"""
        rag_results = None
        skill_validation = None
        market_research = None
        gap_analysis = None
        
        quality, issues = validate_data_sources(
            rag_results, skill_validation, market_research, gap_analysis
        )
        
        assert quality == 0.0
        assert any(i.risk_level == ValidationRisk.CRITICAL for i in issues)

    def test_minimal_resources(self):
        """Test when minimal resources are found"""
        rag_results = {"resources": [{"topic": "Python"}]}
        gap_analysis = {"identified_gaps": []}
        
        quality, issues = validate_data_sources(
            rag_results, None, None, gap_analysis
        )
        
        # Just verify we get a quality score and issues list
        assert isinstance(quality, float)
        assert isinstance(issues, list)


class TestAnalysisMetrics:
    """Test analysis metrics calculation"""

    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly"""
        required_skills = ["Python", "Django", "PostgreSQL"]
        skill_gaps = ["Django", "PostgreSQL"]
        rag_results = {"resources": [{"type": "course"}, {"type": "tutorial"}]}
        gap_analysis = {
            "identified_gaps": ["Django", "PostgreSQL"],
            "time_estimates": {"Django": 30, "PostgreSQL": 20},
        }
        
        metrics = calculate_analysis_metrics(
            required_skills,
            skill_gaps,
            rag_results,
            None,
            None,
            gap_analysis,
            None,
        )
        
        assert metrics["skill_coverage"] > 0
        assert metrics["learning_resources_coverage"] > 0
        assert metrics["gap_analysis_depth"] > 0
        assert 0 <= metrics["overall_confidence"] <= 1.0

    def test_metrics_with_github(self):
        """Test metrics with GitHub analysis included"""
        github_analysis = {
            "project_types": ["API Development", "Frontend"],
        }
        
        metrics = calculate_analysis_metrics(
            ["Python"], ["Python"], None, None, None, None, github_analysis
        )
        
        assert metrics["project_type_coverage"] > 0


class TestFullValidation:
    """Test complete validation workflow"""

    def test_comprehensive_analysis_validation(self):
        """Test full validation of a comprehensive analysis"""
        validation = validate_analysis(
            required_skills=["Python", "Django", "PostgreSQL"],
            current_skills=["Python"],
            skill_gaps=["Django", "PostgreSQL"],
            learning_plan="""
            LEARNING PLAN
            
            Phase 1: Django Basics (3 weeks)
            - Complete official Django tutorial
            - Build simple CRUD app
            
            Phase 2: PostgreSQL (2 weeks)
            - Learn SQL fundamentals
            - Optimize queries
            
            Milestones: Complete tutorial, Deploy app, Write queries
            """,
            github_username=None,
            rag_results={"resources": [{"topic": "Django"}, {"topic": "PostgreSQL"}]},
            skill_validation={"analysis": "Valid skills"},
            market_research={"data": "Research data"},
            gap_analysis={"identified_gaps": ["Django", "PostgreSQL"]},
            github_analysis=None,
        )
        
        assert validation.overall_quality_score > 0.5
        assert validation.is_valid is True
        assert len(validation.recommendations) > 0

    def test_poor_analysis_validation(self):
        """Test validation of a poor analysis"""
        validation = validate_analysis(
            required_skills=["Python", "Django", "PostgreSQL", "AWS"],
            current_skills=["Python"],
            skill_gaps=["Django", "PostgreSQL", "AWS"],
            learning_plan="Learn programming",  # Very minimal
            github_username=None,
            rag_results=None,  # No resources
            skill_validation=None,
            market_research=None,
            gap_analysis=None,  # No gap analysis
            github_analysis=None,
        )
        
        assert validation.overall_quality_score < 0.6
        assert len(validation.issues) > 0

    def test_reflection_feedback(self):
        """Test conversion of validation to feedback"""
        validation = validate_analysis(
            required_skills=["Python"],
            current_skills=[],
            skill_gaps=["Python"],
            learning_plan="Short plan",
            github_username=None,
            rag_results=None,
            skill_validation=None,
            market_research=None,
            gap_analysis=None,
            github_analysis=None,
        )
        
        feedback = get_reflection_feedback(validation)
        
        assert "should_revise" in feedback
        assert isinstance(feedback["action_items"], list)
        assert len(feedback["action_items"]) > 0


class TestValidationIntegration:
    """Integration tests for validation system"""

    def test_validation_identifies_missing_resources(self):
        """Test that validation identifies missing learning resources"""
        validation = validate_analysis(
            required_skills=["Python", "Django"],
            current_skills=[],
            skill_gaps=["Python", "Django"],
            learning_plan="Learn Python and Django",
            github_username=None,
            rag_results=None,  # No resources
            skill_validation=None,
            market_research=None,
            gap_analysis={"identified_gaps": ["Python", "Django"]},
            github_analysis=None,
        )
        
        # Should identify issues - validation provides recommendations
        assert len(validation.recommendations) > 0 or len(validation.issues) > 0

    def test_validation_checks_github_optional(self):
        """Test that validation correctly handles optional GitHub"""
        # Without GitHub - should be valid
        validation_no_github = validate_analysis(
            required_skills=["Python"],
            current_skills=[],
            skill_gaps=["Python"],
            learning_plan="Complete Python course (3 months)",
            github_username=None,
            rag_results={"resources": [{"topic": "Python"}]},
            skill_validation=None,
            market_research=None,
            gap_analysis={"identified_gaps": ["Python"]},
            github_analysis=None,
        )
        
        # With GitHub - should incorporate it
        validation_with_github = validate_analysis(
            required_skills=["Python"],
            current_skills=[],
            skill_gaps=["Python"],
            learning_plan="Complete Python course (3 months)",
            github_username="johndoe",
            rag_results={"resources": [{"topic": "Python"}]},
            skill_validation=None,
            market_research=None,
            gap_analysis={"identified_gaps": ["Python"]},
            github_analysis={
                "proven_skills": {"programming_languages": ["Python"]},
                "project_types": ["API Development"],
            },
        )
        
        # Both should be valid, but GitHub version might have higher confidence
        assert validation_no_github.is_valid
        assert validation_with_github.is_valid
