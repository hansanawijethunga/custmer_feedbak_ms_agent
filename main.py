from flask import Flask, request, jsonify
from pydantic import BaseModel
from openai import OpenAI
import os
import prompt
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1RDobTxzcJB5RBtKf1BibfBNTKV0W4anu3_jsYe7K00I"

# Set your OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Replace with your actual API key

print("OK")
print(OPENAI_API_KEY)

# Initialize Flask app
app = Flask(__name__)


# Define request model using Pydantic (Flask does not have native request validation like FastAPI)
class QueryRequest(BaseModel):
    overall_experience: int
    room_rating: int
    customer_service: int
    dining_experience: int
    food_variety: bool
    parking_convenience: bool
    location_accessibility: int
    recommendation: str
    stay_again: bool
    review: str


@app.route("/feedback", methods=["POST"])
def chat_with_ai():
    try:
        request_data = request.get_json()
        query = QueryRequest(**request_data)
        print(query)
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt.PROMPT},
                {
                    "role": "user",
                    "content": query.review
                }
            ],
            response_format={
                "type": "json_object"
            },
        )
        # print(response)
        data = json.loads(response.choices[0].message.content)
        print(type(data))
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secret.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

            try:
                service = build("sheets", "v4", credentials=creds)
                sheet = service.spreadsheets()
            except:
                pass

        return jsonify(data)

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
