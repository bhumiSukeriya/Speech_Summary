from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from tempfile import NamedTemporaryFile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import modules
from transcription import transcribe_audio
from summarization import generate_summary
from title_generation import generate_titles

# Get OpenAI API key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key
    logger.info("OpenAI API key found in environment variables")
else:
    logger.warning("No OpenAI API key found. Some features may be limited.")

app = FastAPI(
    title="Call Summary API",
    description="API for generating summaries from audio recordings with speaker diarization",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummaryResponse(BaseModel):
    summary: str
    suggested_titles: List[str]
    full_transcript: str

@app.post("/api/generate-summary/", response_model=SummaryResponse)
async def generate_call_summary(
    audio_file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None)
):
    """
    Generate a summary from an audio recording with speaker diarization.
    
    Args:
        audio_file: The audio file to transcribe and summarize
        x_api_key: Optional API key in header
        
    Returns:
        A JSON object containing:
        - summary: A concise summary of the key points
        - suggested_titles: 3 potential titles for the call
        - full_transcript: The complete transcript with speaker identification
    """
    # Set API key from header if provided
    if x_api_key:
        os.environ["OPENAI_API_KEY"] = x_api_key
        logger.info("Using API key from request header")
    
    try:
        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[-1]) as temp_file:
            temp_file_path = temp_file.name
            content = await audio_file.read()
            temp_file.write(content)
        
        logger.info(f"Processing audio file: {audio_file.filename}")
        
        # Process the audio file
        try:
            # Step 1: Transcribe audio with speaker diarization
            logger.info("Starting transcription")
            transcript = transcribe_audio(temp_file_path)
            logger.info("Transcription completed")
            
            # Step 2: Generate summary from transcript
            logger.info("Generating summary")
            summary = generate_summary(transcript)
            logger.info("Summary generation completed")
            
            # Step 3: Generate title suggestions
            logger.info("Generating title suggestions")
            titles = generate_titles(summary)
            logger.info("Title generation completed")
            
            # Return the results
            return SummaryResponse(
                summary=summary,
                suggested_titles=titles,
                full_transcript=transcript
            )
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
                logger.info("Temporary file deleted")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to the Call Summary API. Use /api/generate-summary/ to process audio files."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)