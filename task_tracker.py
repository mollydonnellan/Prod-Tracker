import pandas as pd
from datetime import datetime
import streamlit as st
from supabase import create_client
import pytz

# --- Streamlit Config ---
st.set_page_config(page_title="Work Logger", layout="centered")
st.title("Prod")

# --- Supabase Connection ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Initialize session state ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "activity_type" not in st.session_state:
    st.session_state.activity_type = "Ticket"
if "ticket_number" not in st.session_state:
    st.session_state.ticket_number = ""
if "qa_name" not in st.session_state:
    st.session_state.qa_name = ""
if "description" not in st.session_state:
    st.session_state.description = ""

# --- User input section ---
st.session_state.user_name = st.text_input(
    "Your Name and Date (for tracking):", st.session_state.user_name
)

st.session_state.activity_type = st.selectbox(
    "What are you working on?",
    ["Ticket", "QA", "Ad Hoc / Other"],
    index=["Ticket", "QA", "Ad Hoc / Other"].index(st.session_state.activity_type)
)

# --- Dynamic prompts based on selection ---
if st.session_state.activity_type == "Ticket":
    st.session_state.ticket_number = st.text_input(
        "Enter Ticket Number:", st.session_state.ticket_number
    )
elif st.session_state.activity_type == "QA":
    st.session_state.qa_name = st.text_input(
        "Enter QA Person’s Name:", st.session_state.qa_name
    )
    st.session_state.ticket_number = st.text_input(
        "Enter Ticket Number:", st.session_state.ticket_number
    )
else:
    st.session_state.description = st.text_area(
        "Describe what you're working on:", st.session_state.description
    )

# --- Save to Supabase ---
if st.button("💾 Log Task"):
    user_name = st.session_state.user_name
    if not user_name.strip():
        st.warning("Please enter your name before logging.")
    else:
        entry = {
            "user_name": user_name,
            "activity_type": st.session_state.activity_type,
            "ticket_number": st.session_state.ticket_number,
            "qa_name": st.session_state.qa_name,
            "description": st.session_state.description,
            "timestamp": datetime.now().isoformat(),
        }
        supabase.table("work_logs").insert(entry).execute()
        st.success(f"✅ Logged {st.session_state.activity_type} for {user_name}!")

# --- Show Daily Summary ---
if st.button("📅 Show Daily Summary"):
    user_name = st.session_state.user_name
    if not user_name.strip():
        st.warning("Please enter your name first.")
    else:
        result = supabase.table("work_logs").select("*").eq("user_name", user_name).execute()
        df = pd.DataFrame(result.data)

        if not df.empty:
            # --- Convert timestamps to Eastern Time ---
            eastern = pytz.timezone("US/Eastern")
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(eastern)

            today = datetime.now(eastern).date()
            df_today = df[df["timestamp"].dt.date == today]

            if not df_today.empty:
                # --- Format hour ranges ---
                df_today["hour_range"] = df_today["timestamp"].dt.hour.apply(
                    lambda h: f"{h}:00–{h+1}:00"
                )

                # --- Build readable text per entry ---
                def summarize_row(row):
                    if row["activity_type"] == "Ticket":
                        return f"Ticket #{row.get('ticket_number', '')}"
                    elif row["activity_type"] == "QA":
                        return f"QA with {row.get('qa_name', '')} (Ticket #{row.get('ticket_number', '')})"
                    else:
                        return f"Ad Hoc: {row.get('description', '')}"

                df_today["summary"] = df_today.apply(summarize_row, axis=1)

                # --- Group by hour range ---
                grouped = df_today.groupby("hour_range")["summary"].apply(lambda x: " • ".join(x)).reset_index()

                # --- Create full workday hours (8 AM to 5 PM) ---
                all_hours = [f"{h}:00–{h+1}:00" for h in range(8, 18)]  # 8 to 17
                grouped = grouped.set_index("hour_range").reindex(all_hours, fill_value="No tasks logged").reset_index()

                st.subheader(f"📋 {user_name}’s Summary for Today (EST)")
                st.dataframe(grouped)

            else:
                # No tasks today
                all_hours = [f"{h}:00–{h+1}:00" for h in range(8, 18)]
                st.subheader(f"📋 {user_name}’s Summary for Today (EST)")
                st.dataframe(pd.DataFrame({"hour_range": all_hours, "summary": ["No tasks logged"]*len(all_hours)}))
        else:
            st.info("No logs found yet.")

if st.button("🔄 Resume Last Session"):
    if st.session_state.user_name:
        result = supabase.table("work_logs").select("*").eq("user_name", st.session_state.user_name).order("timestamp", desc=True).limit(1).execute()
        if result.data:
            last = result.data[0]
            st.session_state.activity_type = last["activity_type"]
            st.session_state.ticket_number = last.get("ticket_number", "")
            st.session_state.qa_name = last.get("qa_name", "")
            st.session_state.description = last.get("description", "")
            st.success("✅ Loaded your last session!")
    else:
        st.warning("Please enter your name first.")

