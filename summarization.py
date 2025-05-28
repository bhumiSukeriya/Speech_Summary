import os
import re
import openai
from typing import Dict, List, Any

# Try to import transformers, but provide fallback if not available
try:
    from transformers import pipeline
    has_transformers = True
except ImportError:
    has_transformers = False

def generate_summary(transcript: str) -> str:
    """
    Generate a concise summary of the meeting transcript.
    
    Args:
        transcript: The transcribed meeting with speaker identification
        
    Returns:
        A structured summary with key points
    """
    # Clean the transcript
    cleaned_transcript = clean_transcript(transcript)
    
    # Try to use OpenAI for summarization if API key is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            return summarize_with_openai(cleaned_transcript)
        except Exception as e:
            print(f"OpenAI summarization failed: {str(e)}. Falling back to local model.")
    
    # Fallback to local model or rule-based approach
    if has_transformers:
        return summarize_with_transformers(cleaned_transcript)
    else:
        return simple_extractive_summary(cleaned_transcript)

def clean_transcript(transcript: str) -> str:
    """
    Clean the transcript by removing unnecessary elements.
    
    Args:
        transcript: The raw transcript with speaker identification
        
    Returns:
        Cleaned transcript
    """
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', transcript)
    
    # Remove any non-textual markers
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    
    return cleaned.strip()

def summarize_with_openai(transcript: str) -> str:
    """
    Generate summary using OpenAI's API.
    
    Args:
        transcript: The cleaned transcript
        
    Returns:
        Formatted summary
    """
    system_prompt = (
        "You are a professional meeting summarizer. "
        "Summarize the provided meeting transcript into a concise, structured summary "
        "that captures the key points of the discussion. "
        "Include a 'Key Points' section that extracts the most important takeaways."
    )
    
    # Split transcript if it's too large for context window
    max_chunk_size = 10000  # Adjust based on model being used
    if len(transcript) > max_chunk_size:
        chunks = [transcript[i:i+max_chunk_size] for i in range(0, len(transcript), max_chunk_size)]
        
        # Summarize each chunk
        chunk_summaries = []
        for chunk in chunks:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Summarize this part of the transcript: {chunk}"}
                ],
                max_tokens=500
            )
            chunk_summaries.append(response.choices[0].message.content)
        
        # Combine chunk summaries for final summary
        combined = " ".join(chunk_summaries)
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a final summary combining these partial summaries: {combined}"}
            ],
            max_tokens=800
        )
    else:
        # Summarize the entire transcript at once
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize this meeting transcript: {transcript}"}
            ],
            max_tokens=800
        )
    
    return response.choices[0].message.content

def summarize_with_transformers(transcript: str) -> str:
    """
    Generate summary using Hugging Face transformers.
    
    Args:
        transcript: The cleaned transcript
        
    Returns:
        Structured summary
    """
    # Initialize the pipeline
    summarizer = pipeline(
        "summarization", 
        model="facebook/bart-large-cnn",
        device=-1  # Use CPU
    )
    
    # Handle long transcripts by chunking
    chunks = chunk_text(transcript, max_length=1000)
    chunk_summaries = []
    
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=150, min_length=50, do_sample=False)
            chunk_summaries.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"Error summarizing chunk: {str(e)}")
    
    # Combine chunk summaries
    combined_summary = " ".join(chunk_summaries)
    
    # Format the structured summary
    structured_summary = "## Meeting Summary\n\n"
    structured_summary += combined_summary + "\n\n"
    structured_summary += "## Key Points\n\n"
    
    # Extract key points based on important sentences
    sentences = re.split(r'(?<=[.!?])\s+', combined_summary)
    for i, sentence in enumerate(sentences[:5]):  # Limit to top 5 key points
        if len(sentence) > 10:  # Skip very short sentences
            structured_summary += f"- {sentence}\n"
    
    return structured_summary

def simple_extractive_summary(transcript: str) -> str:
    """
    Create a simple extractive summary when no ML models are available.
    
    Args:
        transcript: The cleaned transcript
        
    Returns:
        Simple summary
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    
    # Extract speaker turns
    speaker_pattern = r'(Speaker [^:]+):'
    speaker_turns = re.findall(speaker_pattern, transcript)
    
    # Count unique speakers
    unique_speakers = set(speaker_turns)
    
    # Select key sentences based on position and speaker changes
    selected_sentences = []
    
    # Take first 3 sentences
    selected_sentences.extend(sentences[:3])
    
    # Take middle 2 sentences
    mid_point = len(sentences) // 2
    selected_sentences.extend(sentences[mid_point:mid_point+2])
    
    # Take last 3 sentences
    selected_sentences.extend(sentences[-3:])
    
    # Format the summary
    summary = "## Meeting Summary\n\n"
    summary += " ".join(selected_sentences) + "\n\n"
    summary += "## Key Points\n\n"
    
    # Add basic info about meeting
    summary += f"- Meeting included {len(unique_speakers)} participants\n"
    summary += f"- The transcript contains {len(sentences)} sentences\n"
    summary += f"- Total of {len(speaker_turns)} speaker changes occurred\n"
    
    return summary

def chunk_text(text: str, max_length: int = 1000) -> list:
    """
    Split text into chunks of specified maximum length.
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        
    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks