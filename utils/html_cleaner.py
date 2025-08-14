"""
HTML Cleaning Utilities
Provides safe HTML cleaning functions for user content
"""

import re


def clean_html_content(content: str) -> str:
    """
    Clean HTML content safely by removing all HTML tags and dangerous content
    
    Args:
        content: Raw content that may contain HTML
        
    Returns:
        Clean text content safe for display
    """
    if not content:
        return ""
    
    # Remove script tags and their content completely (security)
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove style tags and their content
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove all other HTML tags but keep content
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remove dangerous protocols
    content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
    content = re.sub(r'data:', '', content, flags=re.IGNORECASE)
    content = re.sub(r'vbscript:', '', content, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content


def clean_html_for_display(content: str, max_length: int = 100) -> str:
    """
    Clean HTML content and truncate for display
    
    Args:
        content: Raw content that may contain HTML
        max_length: Maximum length for display
        
    Returns:
        Clean, truncated content safe for display
    """
    cleaned = clean_html_content(content)
    
    if len(cleaned) > max_length:
        return cleaned[:max_length] + "..."
    
    return cleaned


def clean_title(title: str) -> str:
    """
    Clean HTML from title/heading content
    
    Args:
        title: Title that may contain HTML
        
    Returns:
        Clean title safe for display
    """
    return clean_html_content(title)