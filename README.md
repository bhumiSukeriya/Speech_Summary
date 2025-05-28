# Call Summary Generator - Setup Instructions

## Quick Setup

1. **Set Environment Variables**

First, set up your OpenAI API key as an environment variable:

```bash
# On Windows (PowerShell):
$env:OPENAI_API_KEY = "your_openai_api_key_here"

# On macOS/Linux:
export OPENAI_API_KEY="your_openai_api_key_here"
```

2. **Install Dependencies**

Install the core dependencies:

```bash
pip install fastapi uvicorn python-multipart openai
```

For better performance (optional):
```bash
pip install torch whisper
```

3. **Run the Application**

```bash
uvicorn main:app --reload
```

The API will be available at http://127.0.0.1:8000

## API Usage

### Generate Summary Endpoint

**Endpoint**: `POST /api/generate-summary/`

**Using curl**:
```bash
curl -X POST "http://127.0.0.1:8000/api/generate-summary/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@/path/to/your/recording.mp3"
```

**Using Python**:
```python
import requests

url = "http://127.0.0.1:8000/api/generate-summary/"
files = {"audio_file": open("recording.mp3", "rb")}
headers = {"X-API-Key": "your_openai_api_key"}  # Optional, can set in environment instead

response = requests.post(url, files=files, headers=headers)
data = response.json()

print(data["summary"])
print(data["suggested_titles"])
```

## Troubleshooting

If you encounter the error `'tuple' object has no attribute 'start'`, make sure:

1. You've updated to the latest version of the code
2. Your OpenAI API key is correctly set
3. The audio file is in a supported format (mp3, wav, m4a)

For any issues with the OpenAI API, check that:
- Your API key is valid and has sufficient credits
- You have properly formatted the request
- The API service is not experiencing downtime

## Alternative Setup (Docker)

If you prefer using Docker:

```bash
# Build the Docker image
docker build -t call-summary-api .

# Run the container
docker run -p 8000:8000 -e OPENAI_API_KEY="your_openai_api_key_here" call-summary-api
```