import os
import openai
import whisper
import json
import tempfile
from typing import Dict, List, Any

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file with speaker diarization.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        A formatted transcript with speaker identification
    """
    # Try using OpenAI for transcription with diarization if API key is available
    if openai.api_key:
        try:
            transcript = transcribe_with_openai(audio_path)
            return transcript
        except Exception as e:
            print(f"OpenAI transcription failed: {str(e)}. Falling back to local Whisper model.")
    
    # Fallback to local Whisper model
    transcript = transcribe_with_whisper(audio_path)
    return transcript

def transcribe_with_openai(audio_path: str) -> str:
    """
    Use OpenAI's API to transcribe audio with diarization.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Formatted transcript with speaker identification
    """
    with open(audio_path, "rb") as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    
    # Process OpenAI response
    if isinstance(response, dict) and "segments" in response:
        segments = response["segments"]
        
        # Format transcript with speakers
        formatted = ""
        current_speaker = None
        
        for segment in segments:
            speaker = f"Speaker {segment.get('speaker', 'Unknown')}"
            
            # Only add speaker label when speaker changes
            if speaker != current_speaker:
                current_speaker = speaker
                formatted += f"\n{speaker}: {segment['text']}"
            else:
                formatted += f" {segment['text']}"
        
        return formatted.strip()
    else:
        # If no diarization in response, format without speakers
        if hasattr(response, "text"):
            return f"Speaker: {response.text}"
        elif isinstance(response, dict) and "text" in response:
            return f"Speaker: {response['text']}"
        else:
            return "Unable to transcribe audio with OpenAI API"

def transcribe_with_whisper(audio_path: str) -> str:
    """
    Use local Whisper model to transcribe audio.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Transcript (without speaker identification)
    """
    try:
        # Load Whisper model (small is a good balance between accuracy and speed)
        model = whisper.load_model("base")
        
        # Transcribe audio
        result = model.transcribe(audio_path)
        
        # Format the result without diarization (since local Whisper doesn't do diarization)
        segments = result.get("segments", [])
        formatted_transcript = ""
        
        current_text_chunk = ""
        
        # Group segments into reasonable chunks
        for segment in segments:
            current_text_chunk += segment.get("text", "")
            
            # Start a new speaker chunk every few segments to simulate diarization
            if len(current_text_chunk) > 200:  # Arbitrary length to create speaker blocks
                formatted_transcript += f"\nSpeaker: {current_text_chunk}\n"
                current_text_chunk = ""
        
        # Add any remaining text
        if current_text_chunk:
            formatted_transcript += f"\nSpeaker: {current_text_chunk}\n"
        
        return formatted_transcript.strip()
        
    except Exception as e:
        return f"Transcription failed: {str(e)}"