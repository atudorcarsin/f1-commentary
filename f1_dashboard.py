

import streamlit as st
import pandas as pd
import asyncio
import tempfile
import edge_tts
import nest_asyncio
# import warnings

# -------------------------------------
# Page config
# -------------------------------------
st.set_page_config(
    page_title="F1 Commentary Generator",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)
#######
def custom_css():
    st.markdown("""
        <style>
        .driver-commentary .streamlit-expanderHeader {
            font-size: 1.2rem !important;
            font-weight: bold;
        }

        .driver-commentary .streamlit-expanderContent {
            background-color: #121212;
            padding: 1rem;
            border-radius: 10px;
        }

        .driver-commentary p {
            font-size: 1.1rem;
            color: #b8f5c6;
        }

        .stButton>button {
            font-size: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            background-color: #d32f2f;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

custom_css()


# Optional custom CSS styling
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("styles.css")

# -------------------------------------
# Edge TTS Wrapper
# -------------------------------------
# async def speak_text_edge_tts(text):
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
#         output_path = tmp.name
#     communicate = edge_tts.Communicate(
#         text=text,
#         voice="en-US-GuyNeural",
#         rate="+15%",
#         volume="+0%"
#     )
#     await communicate.save(output_path)
#     st.audio(output_path, format="audio/mp3")
#
# def speak_text(text):
#     asyncio.run(speak_text_edge_tts(text))

nest_asyncio.apply()

async def speak_text_edge_tts(text):
    try:
        if not text.strip():
            st.warning("No commentary to read.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            output_path = tmp.name

        communicate = edge_tts.Communicate(
            text=text,
            voice="en-US-GuyNeural",  # only 'voice' is supported here
            rate="+15%"
        )
        await communicate.save(output_path)
        st.audio(output_path, format="audio/mp3")

    except Exception as e:
        st.error(f"Error during TTS playback: {e}")

def speak_text(text):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(speak_text_edge_tts(text))
    else:
        loop.run_until_complete(speak_text_edge_tts(text))
# -------------------------------------
# Load data
# -------------------------------------
st.title(" F1 Commentary Generator")

df = pd.read_csv("output_sample.csv")
df = df.sort_values(by='lap_number')
driver_column = 'driver_full_name'

# Sidebar column list
st.sidebar.markdown("### 📄 Available Data Columns")
st.sidebar.write(df.columns.tolist())

# Lap navigation setup
unique_laps = df['lap_number'].unique()
if 'lap_index' not in st.session_state:
    st.session_state.lap_index = 0

def change_lap(delta):
    new_index = st.session_state.lap_index + delta
    if 0 <= new_index < len(unique_laps):
        st.session_state.lap_index = new_index
        st.rerun()

# Lap slider
current_lap = unique_laps[st.session_state.lap_index]
selected_lap = st.slider("🔄 Select Lap", int(unique_laps.min()), int(unique_laps.max()), int(current_lap))
if selected_lap != current_lap:
    st.session_state.lap_index = list(unique_laps).index(selected_lap)
    st.rerun()

lap_rows = df[df['lap_number'] == current_lap]

# -------------------------------------
# Lap Overview Section
# -------------------------------------
st.markdown(f"## 🏁 Lap {current_lap} Overview")
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.button("⬅️ Previous Lap", on_click=change_lap, args=(-1,))
with col2:
    st.markdown(f"### 📍 Current Lap: `{current_lap}`")
with col3:
    st.button("Next Lap ➡️", on_click=change_lap, args=(1,))

# Driver positions visual
lap_drivers = lap_rows[driver_column].unique() if driver_column in df.columns else []


# -------------------------------------
# Driver Selection & Commentary
# -------------------------------------
if lap_drivers.any():
    st.markdown("### 🔍 Driver Filter")
    selected_driver = st.selectbox(
        "Select driver to view commentary:",
        options=["All Drivers"] + list(lap_drivers),
        key=f"driver_select_{current_lap}"
    )

    st.markdown("### 🎙️ AI Commentary")

    if selected_driver == "All Drivers":
        for driver in lap_drivers:
            driver_row = lap_rows[lap_rows[driver_column] == driver]
            if not driver_row.empty:
                ai_comment = driver_row.iloc[0]['ai_comment']
                with st.expander(f"🏁 {driver}", expanded=False):
                    st.markdown("<div class='driver-commentary'>", unsafe_allow_html=True)
                    st.markdown(f"{ai_comment}")
                    if st.button(f"🔊 Listen", key=f"play_{driver}_{current_lap}"):
                        speak_text(ai_comment)
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        filtered_rows = lap_rows[lap_rows[driver_column] == selected_driver]
        if not filtered_rows.empty:
            ai_comment = filtered_rows.iloc[0]['ai_comment']
            st.markdown(f"#### 🧑‍✈️ {selected_driver}")
            st.write(ai_comment)
            if st.button(f"🔊 Play Commentary", key=f"play_{selected_driver}_{current_lap}"):
                speak_text(ai_comment)

# -------------------------------------
# Final Lap Message
# -------------------------------------
if st.session_state.lap_index == len(unique_laps) - 1:
    st.warning("📢 This is the final lap.")
