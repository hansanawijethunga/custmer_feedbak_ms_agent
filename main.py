from openai import OpenAI
import os
from fastapi import FastAPI
from pydantic import BaseModel

# Set your OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")   # Replace with your actual API key
print(OPENAI_API_KEY)
# Initialize FastAPI app
app = FastAPI()

# Define request model
class QueryRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_with_ai(request: QueryRequest):
    """
    API endpoint to send a prompt to OpenAI's API and return the response.
    """
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        )
        return {"response": response.choices[0].message}

    except Exception as e:
        print(e)
        return {"error": str(e)}

# Root endpoint for testing
@app.get("/")
async def root():
    return {"message": "OpenAI Chat API is running!"}
