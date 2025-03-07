from flask import Flask, request, jsonify
from pydantic import BaseModel
from openai import OpenAI
import os

# Set your OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Replace with your actual API key

print(OPENAI_API_KEY)

# Initialize Flask app
app = Flask(__name__)


# Define request model using Pydantic (Flask does not have native request validation like FastAPI)
class QueryRequest(BaseModel):
    prompt: str


@app.route("/chat", methods=["POST"])
def chat_with_ai():
    """
    API endpoint to send a prompt to OpenAI's API and return the response.
    """
    try:
        request_data = request.get_json()
        query = QueryRequest(**request_data)
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You a cutomer "},
                {
                    "role": "user",
                    "content": query.prompt
                }
            ]
        )
        print(response.choices[0].message)
        return jsonify({"response": response.choices[0].message.content})
        # print()
        # return query.prompt

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400


# Root endpoint for testing
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "OpenAI Chat API is running!"})


if __name__ == "__main__":
    # Start the Flask server
    app.run(debug=True)
