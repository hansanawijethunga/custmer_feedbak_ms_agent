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
from typing import List
import uuid
from datetime import datetime
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
    name : str
    age : str
    companion : List[str]
    referralSource : str
    email :str

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
                    "content": query.review + " Feedback givers name is "+ query.name
                }
            ],
            response_format={
                "type": "json_object"
            },
        )


        data = json.loads(response.choices[0].message.content)
        # data = []
        print(data)
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
            feedback_sheet_range = 'FeedBack!A1'
            service = build("sheets", "v4", credentials=creds)
            unique_id = str(uuid.uuid4())
            print(unique_id)
            # sheet = service.spreadsheets()
            row = [
                unique_id,
                datetime.now().strftime("%Y"),
                datetime.now().strftime("%m"),
                query.overall_experience,
                query.room_rating,
                query.customer_service,
                query.dining_experience,
                query.food_variety,
                query.parking_convenience,
                query.location_accessibility,
                query.recommendation,
                query.stay_again,
                query.review,
                query.name,
                query.email,
                query.age,
                query.referralSource,
                data["emotion"],
                data["feedbackStory"],
                data["intent"],
                data["needImmediateAction"],
                data["response"],
                data["summary"],
                data["title"],
                data["translatedFeedback"]
                ]

            command = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=feedback_sheet_range,
                valueInputOption="RAW",  # Use "RAW" to input raw data, "USER_ENTERED" for Excel-like behavior
                insertDataOption="INSERT_ROWS",  # Optionally choose how to insert rows
                body={"values": [row]}
            )
            # Execute the request
            response = command.execute()
            companion_sheet_range = 'Companions!A1'
            for item in query.companion:
                row = [
                    unique_id,
                    item
                ]
                command = service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=companion_sheet_range,
                    valueInputOption="RAW",  # Use "RAW" to input raw data, "USER_ENTERED" for Excel-like behavior
                    insertDataOption="INSERT_ROWS",  # Optionally choose how to insert rows
                    body={"values": [row]}
                )
                # Execute the request
                response = command.execute()
            #positive comments
            positive_sheet_range = 'Positive!A1'
            for item in data["positiveFeedback"]:
                row = [
                    unique_id,
                    item
                ]
                command = service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=positive_sheet_range,
                    valueInputOption="RAW",  # Use "RAW" to input raw data, "USER_ENTERED" for Excel-like behavior
                    insertDataOption="INSERT_ROWS",  # Optionally choose how to insert rows
                    body={"values": [row]}
                )
                # Execute the request
                response = command.execute()

            # negative comments
            negative_sheet_range = 'Negative!A1'
            for item in data["negativeFeedback"]:
                row = [
                    unique_id,
                    item
                ]
                command = service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=negative_sheet_range,
                    valueInputOption="RAW",  # Use "RAW" to input raw data, "USER_ENTERED" for Excel-like behavior
                    insertDataOption="INSERT_ROWS",  # Optionally choose how to insert rows
                    body={"values": [row]}
                )
                # Execute the request
                response = command.execute()

            # suggestions
            suggestion_sheet_range = 'Suggestion!A1'
            for item in data["suggestions"]:
                row = [
                    unique_id,
                    item
                ]
                command = service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=suggestion_sheet_range,
                    valueInputOption="RAW",  # Use "RAW" to input raw data, "USER_ENTERED" for Excel-like behavior
                    insertDataOption="INSERT_ROWS",  # Optionally choose how to insert rows
                    body={"values": [row]}
                )
                # Execute the request
                response = command.execute()

            print(response)
        except Exception as e:
            print(e)
            traceback.print_exc()
            return jsonify({"error": str(e)}), 400
#send email to manager
        if data["needImmediateAction"]:
            send_email(
                subject="IMMEDIATE ACTION NEEDED",
                name=query.name,
                summary=data['summary'],
                feedback=query.review,
                emotion= data['emotion'],
                intent = data['intent'],
                recipient_email="rapidminds99@gmail.com"
            )

# send email to customer
        if data["needImmediateAction"]:
            send_email_customer(
                subject="IMMEDIATE ACTION NEEDED",
                body= data["response"],
                recipient_email="rapidminds99@gmail.com"
            )

        return jsonify(data)

    except Exception as e:
        print(e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


# Root endpoint for testing
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "OpenAI Chat API is running!"})


def send_email(subject, name,feedback,summary,emotion, intent, recipient_email):
    try:
        # Get email and app password from environment variables
        sender_email = os.getenv('GMAIL_EMAIL')  # Email from environment variable
        app_password = os.getenv('GMAIL_APP_PASSWORD')  # App Password from environment variable

        if not sender_email or not app_password:
            raise ValueError("Gmail email or app password not set in environment variables.")

        # Set up the SMTP server
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Create a MIME email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Formatting the email body to be cleaner and more readable
        email_body = f"""
        Dear Team,

        Please attend to the following customer request as soon as possible.

        Customer Name: {name}
        Customer is {emotion} and He wants to {intent}
        Request Summary: {summary}
        Original Feedback: {feedback}

        Regards,
        Your AI Assistance
        """

        # Attach the formatted email body
        msg.attach(MIMEText(email_body, "plain"))

        # Connect to Gmail's SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")



def send_email_customer(subject, body, recipient_email):
    try:
        # Get email and app password from environment variables
        sender_email = os.getenv('GMAIL_EMAIL')  # Email from environment variable
        app_password = os.getenv('GMAIL_APP_PASSWORD')  # App Password from environment variable

        if not sender_email or not app_password:
            raise ValueError("Gmail email or app password not set in environment variables.")

        # Set up the SMTP server
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Create a MIME email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Connect to Gmail's SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    # Start the Flask server
    app.run(debug=True)
