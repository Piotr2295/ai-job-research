"""
Test GitHub username extraction from resume text
"""

import pytest
from app.resume_parser import extract_github_username


def test_extract_github_username_standard_url():
    """Test extracting GitHub username from standard URL"""
    text = """
    John Doe
    Email: john@example.com
    GitHub: https://github.com/johndoe
    LinkedIn: linkedin.com/in/johndoe
    """
    
    username = extract_github_username(text)
    assert username == "johndoe"


def test_extract_github_username_without_https():
    """Test extracting GitHub username from URL without https"""
    text = """
    Profile Links:
    - github.com/jane-smith
    - linkedin.com/in/janesmith
    """
    
    username = extract_github_username(text)
    assert username == "jane-smith"


def test_extract_github_username_with_www():
    """Test extracting GitHub username from URL with www"""
    text = "Check out my work at www.github.com/awesome-dev"
    
    username = extract_github_username(text)
    assert username == "awesome-dev"


def test_extract_github_username_with_label():
    """Test extracting GitHub username with 'GitHub: @username' format"""
    text = """
    Contact Information:
    Email: dev@example.com
    GitHub: @techguru123
    """
    
    username = extract_github_username(text)
    assert username == "techguru123"


def test_extract_github_username_gh_shorthand():
    """Test extracting GitHub username with 'GH:' shorthand"""
    text = "GH: developer-pro"
    
    username = extract_github_username(text)
    assert username == "developer-pro"


def test_extract_github_username_case_insensitive():
    """Test case insensitive matching"""
    text = "GITHUB: https://GITHUB.com/CaseSensitive"
    
    username = extract_github_username(text)
    assert username == "CaseSensitive"


def test_extract_github_username_none_found():
    """Test when no GitHub username is found"""
    text = """
    John Doe
    Email: john@example.com
    LinkedIn: linkedin.com/in/johndoe
    Website: example.com
    """
    
    username = extract_github_username(text)
    assert username is None


def test_extract_github_username_filters_false_positives():
    """Test filtering out common false positives"""
    text = "Visit github.com for more information"
    
    username = extract_github_username(text)
    # Should not extract 'com' as username
    assert username is None


def test_extract_github_username_valid_length():
    """Test that extracted username respects GitHub's 1-39 character limit"""
    # Too long username (40+ chars) should be rejected
    text = f"GitHub: https://github.com/{'a' * 40}"
    
    username = extract_github_username(text)
    assert username is None
    
    # Valid 39 character username should be accepted
    text_valid = f"GitHub: https://github.com/{'a' * 39}"
    username_valid = extract_github_username(text_valid)
    assert username_valid == 'a' * 39


def test_extract_github_username_with_hyphens():
    """Test extracting usernames with hyphens (GitHub allows this)"""
    text = "GitHub: https://github.com/multi-word-username"
    
    username = extract_github_username(text)
    assert username == "multi-word-username"


def test_extract_github_username_complex_resume():
    """Test extraction from a complex resume with multiple URLs"""
    text = """
    JOHN DOE
    Software Engineer
    
    CONTACT INFORMATION
    Email: john.doe@email.com
    Phone: +1-555-0123
    LinkedIn: https://www.linkedin.com/in/johndoe
    GitHub: https://github.com/johndoe
    Portfolio: https://johndoe.dev
    
    EXPERIENCE
    Senior Developer at Tech Corp
    - Built scalable systems
    - Led team of 5 engineers
    
    EDUCATION
    BS Computer Science, MIT
    """
    
    username = extract_github_username(text)
    assert username == "johndoe"


def test_extract_github_username_first_match():
    """Test that it returns the first GitHub username found"""
    text = """
    Old GitHub: github.com/old-username
    Current GitHub: github.com/new-username
    """
    
    username = extract_github_username(text)
    # Should return the first match
    assert username == "old-username"
