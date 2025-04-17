import os
import streamlit as st
import pandas as pd
from collections import defaultdict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Constants
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = "1RDobTxzcJB5RBtKf1BibfBNTKV0W4anu3_jsYe7K00I"
RANGE_FEEDBACK = "FeedBack!A1:Y"
RANGE_POSITIVE = "Positive!A1:B"
RANGE_NEGATIVE = "Negative!A1:B"
RANGE_SUGGESTION = "Suggestion!A1:B"

# Google Sheets auth
def get_gsheet_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)

# Load data
@st.cache_data(show_spinner=True)
def load_data():
    service = get_gsheet_service()
    sheet = service.spreadsheets()

    # Main Feedback Sheet
    feedback = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_FEEDBACK).execute().get("values", [])
    feedback_df = pd.DataFrame(feedback[1:], columns=feedback[0]) if feedback else pd.DataFrame()

    # Additional Comment Sheets
    def load_sheet(range_name):
        data = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute().get("values", [])
        return pd.DataFrame(data[1:], columns=data[0]) if data else pd.DataFrame()

    return feedback_df, {
        "Positive": load_sheet(RANGE_POSITIVE),
        "Negative": load_sheet(RANGE_NEGATIVE),
        "Suggestion": load_sheet(RANGE_SUGGESTION),
    }

# UI Config
st.set_page_config(page_title="Feedback Viewer", layout="centered")
st.title("📝 Feedback Viewer")

# Load data
df, comment_data = load_data()

if df.empty:
    st.warning("No data found.")
    st.stop()

# Dropdown with unique names
name_map = defaultdict(list)
for idx, row in df.iterrows():
    name_map[row["name"]].append(idx)

display_names = []
index_map = {}
for name, indexes in name_map.items():
    for i, idx in enumerate(indexes):
        label = f"{name} ({i+1})" if len(indexes) > 1 else name
        display_names.append(label)
        index_map[label] = idx

selected_label = st.selectbox("Select a Name", display_names)
selected_index = index_map[selected_label]
selected = df.iloc[selected_index]

# Show title
st.markdown(f"<h2 style='text-align:center'>{selected.get('title', '')}</h2>", unsafe_allow_html=True)

# Need Immediate Action
if selected.get("needImmediateAction", "").strip().upper() == "TRUE":
    st.markdown(
        "<div style='background-color:red; color:white; padding:10px; font-weight:bold; text-align:center; "
        "border-radius:8px; animation: flash 1s infinite;'>🚨 NEED IMMEDIATE ACTION</div>"
        "<style>@keyframes flash { 0%{opacity:1;} 50%{opacity:0.4;} 100%{opacity:1;} }</style>",
        unsafe_allow_html=True
    )

# Emotion and Intent Icons
emotion_icon_map = {
    "Satisfied": ("😊", "#4CAF50"),
    "Excited": ("😃", "#2196F3"),
    "Frustrated": ("😖", "#FF9800"),
    "Disappointed": ("😞", "#FFC107"),
    "Angry": ("😠", "#F44336"),
    "Neutral": ("😐", "#9E9E9E"),
}

intent_icon_map = {
    "Positive Feedback": ("👍", "#4CAF50"),
    "Complaint & Dissatisfaction": ("❗", "#F44336"),
    "Service Improvement Request": ("🛠️", "#03A9F4"),
    "Support & Assistance Request": ("📞", "#9C27B0"),
}

emotion = selected.get("emotion", "Unknown")
intent = selected.get("intent", "Unknown")

emo_icon, emo_color = emotion_icon_map.get(emotion, ("❔", "#607D8B"))
intent_icon, intent_color = intent_icon_map.get(intent, ("❔", "#607D8B"))

# Show details
st.markdown("---")
st.markdown(f"**👤 Name:** {selected.get('name', 'N/A')}")
st.markdown(f"<span style='color:{emo_color}; font-weight:bold;'>{emo_icon} Emotion: {emotion}</span>", unsafe_allow_html=True)
st.markdown(f"<span style='color:{intent_color}; font-weight:bold;'>{intent_icon} Intent: {intent}</span>", unsafe_allow_html=True)

# Story & Summary
st.markdown(f"**🧾 Customer's Story:**<br>{selected.get('feedbackStory', 'N/A')}", unsafe_allow_html=True)
st.markdown(f"**📝 Summary:**<br>{selected.get('summary', 'N/A')}", unsafe_allow_html=True)

# Our Response
response_text = selected.get("response", "").strip()
if response_text:
    st.markdown(f"**📣 Our Response:**<br>{response_text}", unsafe_allow_html=True)

st.markdown("---")

# Show matched comments by Id
selected_id = selected.get("Id", "").strip()

for category, data in comment_data.items():
    if "Id" in data.columns and "Comment" in data.columns:
        filtered = data[data["Id"] == selected_id]
        if not filtered.empty:
            color = {
                "Positive": "#4CAF50",
                "Negative": "#F44336",
                "Suggestion": "#03A9F4"
            }.get(category, "#607D8B")
            st.markdown(f"#### <span style='color:{color};'>{category} Comments</span>", unsafe_allow_html=True)
            for _, row in filtered.iterrows():
                st.markdown(f"- {row['Comment']}")

# Original & Translated Comment
review = selected.get("review", "").strip()
if review:
    st.markdown("**💬 Original Comment:**")
    st.markdown(f"> {review}")

    translated = selected.get("translatedFeedback", "").strip()

    def normalize_first_3_words(text):
        words = text.lower().split()
        return "".join(words[:3])  # Join first 3 words with no spaces

    if translated and normalize_first_3_words(translated) != normalize_first_3_words(review):
        st.markdown("**🌐 Translated Comment:**")
        st.markdown(f"> {translated}")
