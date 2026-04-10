from django import template
import re
import html

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to look up dictionary values by key"""
    return dictionary.get(key, 0)

@register.filter
def markdown_to_plain_text(markdown_text):
    """Convert markdown text to plain text by removing formatting"""
    if not markdown_text:
        return ""
    
    # Unescape HTML entities first
    text = html.unescape(markdown_text)
    
    # Remove code blocks first (to avoid processing markdown inside them)
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    
    # Remove markdown formatting
    # Remove bold/italic: **text** or *text* (handle nested cases)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # Remove headers: # ## ### etc.
    text = re.sub(r'^#{1,6}\s*(.*)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove links: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove inline code: `code` -> code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    
    # Remove list markers: - * +
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    
    # Remove numbered list markers: 1. 2. etc.
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines -> double newline
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)  # Trim lines
    text = text.strip()
    
    return text