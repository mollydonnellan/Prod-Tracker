import pandas as pd
from datetime import datetime
from pathlib import Path
import streamlit as st

LOG_FILE = Path("work_log.csv")

st.set_page_config(page_title="Work Logger", layout="centered")
st.title("🧠 Work Productivity Logger")

# --- Input selection ---
activity_type = st.selectbox(
    "What are you working on?",
    ["Ticket", "QA", "Ad Hoc / Other"]
)

# --- Dynamic prompts based on activity ---
details = {}
if activity_type == "Ticket":
    details["Ticket #"] = st.text_input("Enter Ticket Number:")
elif activity_type == "QA":
    details["QA Name"] = st.text_input("Enter QA Person’s Name:")
    details["Ticket #"] = st.text_input("Enter Ticket Number:")
else:
    details["Description"] = st.text_area("Describe what you're working on:")

# --- Save button ---
if st.button("💾 Log Task"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"timestamp": now, "type": activity_type, **details}
    df = pd.DataFrame([data])
    if LOG_FILE.exists():
        df.to_csv(LOG_FILE, mode="a", index=False, header=False)
    else:
        df.to_csv(LOG_FILE, index=False)
    st.success(f"Logged {activity_type} at {now}")

# --- Show summary ---
if st.button("📅 Show Daily Summary"):
    if LOG_FILE.exists():
        df = pd.read_csv(LOG_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        today = datetime.now().date()
        df = df[df["timestamp"].dt.date == today]
        if not df.empty:
            df["hour"] = df["timestamp"].dt.hour
            grouped = df.groupby("hour")["type"].apply(lambda x: ", ".join(x)).reset_index()
            st.subheader("Today’s Summary")
            st.dataframe(grouped)
        else:
            st.info("No entries logged today.")
    else:
        st.info("No log file found yet.")
