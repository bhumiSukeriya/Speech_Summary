import streamlit as st
import requests
import os
import tempfile
import json
import time
from datetime import datetime

st.set_page_config(
    page_title="Call Summary Generator",
    page_icon="🎙️",
    layout="wide"
)

def main():
    st.title("🎙️ Call Summary Generator")
    st.write("Upload an audio recording to generate a detailed summary with title suggestions.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_url = st.text_input(
            "API URL", 
            value="http://127.0.0.1:8000/api/generate-summary/",
            help="URL of the Call Summary API"
        )
        
        api_key = st.text_input(
            "OpenAI API Key (Optional)", 
            type="password",
            help="If not provided, will use the API key configured on the server"
        )
        
        st.divider()
        st.write("### About")
        st.write("""
        This tool uses AI to transcribe and summarize audio recordings of meetings, 
        calls, or presentations. Upload your audio file, and get a structured 
        summary and title suggestions in seconds.
        """)

    # File uploader
    uploaded_file = st.file_uploader("Upload an audio file", 
                                     type=["mp3", "wav", "m4a", "ogg"],
                                     help="Supported formats: mp3, wav, m4a, ogg")

    if uploaded_file is not None:
        # Display audio player
        st.audio(uploaded_file, format=f'audio/{uploaded_file.name.split(".")[-1]}')
        
        col1, col2 = st.columns([1, 3])
        with col1:
            process_btn = st.button("Generate Summary", type="primary", use_container_width=True)
        with col2:
            st.write("")  # Spacer
        
        if process_btn:
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Processing steps
            try:
                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_filename = tmp_file.name
                
                # Set up request
                headers = {}
                if api_key:
                    headers["X-API-Key"] = api_key
                
                status_text.text("Step 1/3: Transcribing audio...")
                progress_bar.progress(20)
                
                # Send request with file
                with open(temp_filename, "rb") as file_content:
                    files = {"audio_file": (uploaded_file.name, file_content, f"audio/{uploaded_file.name.split('.')[-1]}")}
                    
                    status_text.text("Step 2/3: Sending to API...")
                    progress_bar.progress(40)
                    
                    # Make request to the API
                    response = requests.post(api_url, headers=headers, files=files)
                
                status_text.text("Step 3/3: Processing response...")
                progress_bar.progress(80)
                
                # Clean up temp file
                try:
                    os.unlink(temp_filename)
                except Exception as e:
                    st.warning(f"Note: Could not remove temporary file. It will be deleted by your system later. ({str(e)})")
                
                # Handle response
                if response.status_code == 200:
                    result = response.json()
                    progress_bar.progress(100)
                    status_text.text("Complete! ✅")
                    time.sleep(1)
                    status_text.empty()
                    progress_bar.empty()
                    
                    # Display results in tabs
                    tab1, tab2, tab3 = st.tabs(["📝 Summary", "🎯 Suggested Titles", "📄 Full Transcript"])
                    
                    with tab1:
                        st.markdown(result["summary"])
                        
                        # Export button for summary
                        summary_text = result["summary"]
                        st.download_button(
                            label="Export Summary",
                            data=summary_text,
                            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                    
                    with tab2:
                        for i, title in enumerate(result["suggested_titles"], 1):
                            st.write(f"{i}. {title}")
                    
                    with tab3:
                        st.text_area("Full Transcript", result["full_transcript"], height=400)
                        
                        # Export button for transcript
                        transcript_text = result["full_transcript"]
                        st.download_button(
                            label="Export Transcript",
                            data=transcript_text,
                            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    progress_bar.empty()
                    status_text.empty()
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                progress_bar.empty()
                status_text.empty()
    
    # Instructions when no file is uploaded
    else:
        st.info("👆 Upload an audio file to get started!")
        
        # Example of what you'll get
        with st.expander("See example output"):
            st.write("### Example Summary")
            st.markdown("""
            ## Meeting Summary

            The team discussed the Q2 marketing strategy with a focus on digital campaigns. 
            Jane presented the budget allocation, showing 40% for social media, 30% for search, 
            20% for influencer partnerships, and 10% for email marketing. Tom raised concerns 
            about the limited allocation for email marketing given its high ROI last quarter.

            ## Key Points

            - Budget: $250,000 for Q2 marketing campaigns
            - Primary focus on Instagram and TikTok for the 18-24 demographic
            - New A/B testing framework to be implemented in April
            - Team agreed to review performance weekly instead of bi-weekly
            - Next meeting scheduled for April 15th to finalize creative assets
            """)
            
            st.write("### Example Suggested Titles")
            st.write("1. Q2 Digital Marketing Strategy & Budget Review")
            st.write("2. Marketing Budget Allocation & Campaign Planning")
            st.write("3. Digital Marketing Strategy for Q2: Planning Session")

if __name__ == "__main__":
    main()