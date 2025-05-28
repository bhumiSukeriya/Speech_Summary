import os
import re
import openai
import random
from typing import List

def generate_titles(summary: str) -> List[str]:
    """
    Generate three title suggestions based on the meeting summary.
    
    Args:
        summary: The meeting summary text
        
    Returns:
        List of 3 suggested titles
    """
    # Try to use OpenAI for title generation if API key is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            return generate_titles_with_openai(summary)
        except Exception as e:
            print(f"OpenAI title generation failed: {str(e)}. Falling back to rule-based approach.")
    
    # Use rule-based approach as fallback
    return generate_titles_rule_based(summary)

def generate_titles_with_openai(summary: str) -> List[str]:
    """
    Generate titles using OpenAI's API.
    
    Args:
        summary: Meeting summary
        
    Returns:
        List of 3 suggested titles
    """
    # Create a prompt for title generation
    prompt = (
        "Below is a summary of a meeting or call. "
        "Generate 3 concise, professional titles for this meeting. "
        "Each title should be less than 8 words, capture the main topic, "
        "and be formatted for business context.\n\n"
        f"Summary:\n{summary}\n\n"
        "Titles:"
    )
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional title generator for business meetings."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    
    # Extract titles from response
    content = response.choices[0].message.content
    
    # Parse numbered or bulleted list
    titles = []
    lines = content.strip().split('\n')
    
    for line in lines:
        # Remove numbering, bullets and leading/trailing whitespace
        clean_line = re.sub(r'^[\d\.\-\*\•\○\□\s]+', '', line).strip()
        
        # Add non-empty lines that aren't too long
        if clean_line and len(clean_line) < 60:
            titles.append(clean_line)
    
    # Ensure we have exactly 3 titles
    while len(titles) < 3:
        titles.append(f"Meeting Summary {len(titles) + 1}")
    
    return titles[:3]  # Return only the first 3 titles

def generate_titles_rule_based(summary: str) -> List[str]:
    """
    Generate titles based on templates and key topics.
    
    Args:
        summary: Meeting summary
        
    Returns:
        List of 3 suggested titles
    """
    # Extract key topics
    topics = extract_key_topics(summary)
    
    # Ensure we have at least 2 topics
    if len(topics) < 2:
        topics = topics + ["Discussion", "Planning", "Review"]
    
    # Generate titles from templates
    templates = [
        "{topic1} Discussion Summary",
        "{topic1} and {topic2} Planning",
        "Meeting Notes: {topic1} Review",
        "{topic1} Strategy Session",
        "Quarterly {topic1} Update",
        "{topic1}: Analysis & Next Steps",
        "{topic1} Implementation Plan",
        "{topic1} and {topic2} Collaboration"
    ]
    
    titles = []
    random.shuffle(templates)
    
    for template in templates[:3]:
        if "{topic1}" in template and "{topic2}" in template:
            title = template.format(topic1=topics[0].capitalize(), topic2=topics[1].capitalize())
        else:
            title = template.format(topic1=topics[0].capitalize())
        
        titles.append(title)
    
    return titles

def extract_key_topics(summary: str) -> List[str]:
    """
    Extract key topics from the summary text.
    
    Args:
        summary: Meeting summary
        
    Returns:
        List of key topics
    """
    # Remove markdown formatting
    text = re.sub(r'#+\s+', '', summary)
    text = re.sub(r'\n+', ' ', text)
    
    # Get the most frequent words (simplified)
    words = text.lower().split()
    stop_words = set(['the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 
                     'by', 'of', 'is', 'was', 'were', 'be', 'as', 'that', 'this',
                     'key', 'point', 'points', 'meeting', 'summary'])
    
    # Filter out stop words and short words
    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Count word frequencies
    word_counts = {}
    for word in filtered_words:
        if word not in word_counts:
            word_counts[word] = 0
        word_counts[word] += 1
    
    # Get top topics
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    topics = [word for word, _ in sorted_words[:5]]
    
    if not topics:
        topics = ["Business", "Meeting", "Discussion"]
    
    return topics