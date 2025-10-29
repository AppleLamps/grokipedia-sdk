"""HTML parsing and extraction logic for Grokipedia articles"""

import re
from typing import Tuple, List, Optional
from bs4 import BeautifulSoup, Tag

from .models import Section

# Summary extraction constants
MIN_SUMMARY_LENGTH = 200  # Minimum characters for a substantial summary paragraph
MIN_FALLBACK_SUMMARY_LENGTH = 50  # Minimum characters for fallback summary

# HTML Element Selectors (constants to replace magic strings)
HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
SECONDARY_HEADING_TAGS = ['h2', 'h3']
MAJOR_HEADING_TAGS = ['h1', 'h2']
SECTION_TAGS = ['ol', 'ul']
TEXT_CONTAINER_TAGS = ['p', 'div']
SCRIPT_TAGS = ['script', 'style', 'nav', 'header', 'footer', 'button']

# Meta tag properties
OG_DESCRIPTION_META = {'property': 'og:description'}
DESCRIPTION_META = {'name': 'description'}

# Regex patterns
REFERENCES_HEADING_PATTERN = re.compile(r'^References?$', re.IGNORECASE)
FACT_CHECK_PATTERN = re.compile(r'Fact-checked by', re.IGNORECASE)
FACT_CHECK_EXTRACT_PATTERN = re.compile(r'Fact-checked by\s+(.+?)(?:\s*(?:\n|$))', re.IGNORECASE)


def extract_sections(soup: BeautifulSoup) -> Tuple[List[Section], List[str]]:
    """
    Extract sections and table of contents from article.
    
    Args:
        soup: BeautifulSoup object of the article
        
    Returns:
        Tuple of (sections list, table of contents list)
    """
    sections = []
    toc = []
    
    # Find all heading tags
    headings = soup.find_all(HEADING_TAGS)
    
    for heading in headings:
        level = int(heading.name[1])  # Extract number from h1, h2, etc.
        title = heading.get_text(strip=True)
        
        # Skip the main article title (usually h1)
        if level == 1:
            continue
            
        toc.append(title)
        
        # Get content after heading until next heading
        # Use list comprehension for efficient string collection
        content_parts = [
            sibling.get_text(strip=True)
            for sibling in heading.find_next_siblings()
            if sibling.name and not sibling.name.startswith('h')
        ]
        # Filter out empty strings and join efficiently
        content = " ".join(filter(None, content_parts))
        
        sections.append(Section(
            title=title,
            content=content,
            level=level
        ))
    
    return sections, toc


def extract_references(soup: BeautifulSoup) -> List[str]:
    """
    Extract reference links from article.
    
    Args:
        soup: BeautifulSoup object of the article
        
    Returns:
        List of reference URLs
    """
    references = []
    
    # Look for References heading (h2 with id or text "References")
    ref_section = soup.find(SECONDARY_HEADING_TAGS, string=REFERENCES_HEADING_PATTERN)
    if not ref_section:
        # Try finding by id
        ref_section = soup.find(id='references') or soup.find(id='References')
    
    if ref_section:
        # Get all content after references section
        current = ref_section.find_next_sibling()
        while current:
            # Stop if we hit another major section
            if current.name in MAJOR_HEADING_TAGS:
                break
            
            # Extract all links from ordered/unordered lists
            if current.name in SECTION_TAGS:
                for link in current.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('http'):
                        references.append(href)
            
            # Extract links from paragraphs or divs
            elif current.name in TEXT_CONTAINER_TAGS:
                for link in current.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('http'):
                        references.append(href)
            
            current = current.find_next_sibling()
    
    # Fallback: Find all external links (excluding Grokipedia itself)
    if not references:
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if href.startswith('http') and 'grokipedia.com' not in href:
                references.append(href)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_refs = []
    for ref in references:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)
    
    return unique_refs


def extract_fact_check_info(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract fact-check information if available.
    
    Args:
        soup: BeautifulSoup object of the article
        
    Returns:
        Fact-check information or None
    """
    # Method 1: Look in meta tags
    meta_desc = soup.find('meta', OG_DESCRIPTION_META)
    if meta_desc:
        content = meta_desc.get('content', '')
        if 'Fact-checked' in content:
            match = re.search(r'Fact-checked by (.+?)(?:\.|$)', content)
            if match:
                return match.group(1).strip()
    
    # Method 2: Look for text in the page - search all text nodes for the pattern
    for element in soup.find_all(string=True):
        text = str(element).strip()
        if FACT_CHECK_PATTERN.search(text):
            # Extract just the fact-check info
            match = re.search(FACT_CHECK_EXTRACT_PATTERN, text)
            if match:
                fact_check = match.group(1).strip()
                # Clean up extra whitespace and trailing punctuation
                fact_check = ' '.join(fact_check.split())
                fact_check = fact_check.rstrip('.,;:!?')
                return fact_check
    
    return None


def extract_summary(soup: BeautifulSoup, title_tag: Optional[Tag]) -> str:
    """
    Extract summary/intro text from article.
    
    Args:
        soup: BeautifulSoup object of the article
        title_tag: The h1 title tag (can be None)
        
    Returns:
        Summary text
    """
    summary = ""
    
    # Extract summary from meta description (most reliable)
    meta_desc = (
        soup.find('meta', OG_DESCRIPTION_META) or 
        soup.find('meta', DESCRIPTION_META)
    )
    if meta_desc:
        content = meta_desc.get('content', '').strip()
        if content:
            return content
    
    # Fallback: Extract from first paragraph if no meta description
    # Try to find main article content area
    main_content = soup.find('article') or soup.find('main') or soup
    
    # Look for first substantial paragraph after h1
    if title_tag:
        # Use list comprehension for efficient text extraction
        candidates = [
            sibling.get_text(strip=True)
            for sibling in title_tag.find_next_siblings(['p', 'div'])
        ]
        for text in candidates:
            # Look for substantial content (intro paragraph is usually 200+ chars)
            if len(text) > MIN_SUMMARY_LENGTH and not text.startswith('Jump to') and not text.startswith('From '):
                return text
    
    # Last resort: first substantial paragraph anywhere
    paragraphs = main_content.find_all('p')
    # Use list comprehension for efficient text extraction
    paragraph_texts = [p.get_text(strip=True) for p in paragraphs]
    
    for text in paragraph_texts:
        if len(text) > MIN_SUMMARY_LENGTH and not text.startswith('Jump to') and not text.startswith('From '):
            return text
    
    # If no substantial paragraph found, return first non-empty paragraph
    for text in paragraph_texts:
        if text and len(text) > MIN_FALLBACK_SUMMARY_LENGTH:
            return text
    
    return ""


def clean_html_for_text_extraction(soup: BeautifulSoup) -> None:
    """
    Remove unwanted elements from soup for clean text extraction.
    
    Modifies the soup in place by decomposing unwanted elements.
    
    Args:
        soup: BeautifulSoup object to clean
    """
    for element in soup(SCRIPT_TAGS):
        element.decompose()
