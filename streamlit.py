import streamlit as st
import pandas as pd
import pyttsx3
from gtts import gTTS
import tempfile
import streamlit as st
import edge_tts
import asyncio
import tempfile

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('voice', engine.getProperty('voices')[82].id)

# def speak_text(text):
#     engine = pyttsx3.init()
#     engine.setProperty('rate', 180)
#     engine.setProperty('voice', engine.getProperty('voices')[82].id)
#     engxine.say(text)
#     engine.runAndWait()



# def speak_text(text):
#     tts = gTTS(text)
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
#         tts.save(tmp.name)
#         st.audio(tmp.name, format="audio/mp3")  # Streamlit audio widget

async def speak_text_edge_tts(text):
    # Use a temporary file to store audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        output_path = tmp.name

    # Create a communicator with desired voice
    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-GuyNeural",   # Try "en-US-JennyNeural" or others
        rate="+0%",                # You can try "+10%", "-10%" etc.
        volume="+0%"               # You can try "+20%", etc.
    )

    # Save audio
    await communicate.save(output_path)

    # Streamlit audio playback
    st.audio(output_path, format="audio/mp3")

# Wrapper to call from Streamlit
def speak_text(text):
    asyncio.run(speak_text_edge_tts(text))


st.title("F1 Commentary Generator")

# Load and sort the DataFrame
df = pd.read_csv("output_sample.csv")
df = df.sort_values(by='lap_number')

# Debug: Display column names in sidebar
st.sidebar.write("Available columns:", df.columns.tolist())

# Unique lap numbers
unique_laps = df['lap_number'].unique()

# Session state for lap index
if 'lap_index' not in st.session_state:
    st.session_state.lap_index = 0

# Function to update lap index and trigger rerun
def change_lap(delta):
    new_index = st.session_state.lap_index + delta
    if 0 <= new_index < len(unique_laps):
        st.session_state.lap_index = new_index
        st.rerun()

# Current lap
current_lap = unique_laps[st.session_state.lap_index]
lap_rows = df[df['lap_number'] == current_lap]

# Display lap header
st.header(f"Lap {current_lap}")

# Use the known driver column name
driver_column = 'driver_full_name'

# Create a filter for drivers in this lap
st.subheader("Driver Filter")
if driver_column in df.columns:
    # Get all drivers for this lap
    lap_drivers = lap_rows[driver_column].unique()
    
    # Create a dropdown to select drivers
    selected_driver = st.selectbox(
        "Select driver to view commentary:",
        options=["All Drivers"] + list(lap_drivers),
        key=f"driver_select_{current_lap}"
    )
    
    # Filter based on selection
    if selected_driver == "All Drivers":
        filtered_rows = lap_rows
    else:
        filtered_rows = lap_rows[lap_rows[driver_column] == selected_driver]
    
    # Display commentary text
    st.subheader("Commentary")
    if selected_driver == "All Drivers":
        # Show all commentaries
        for driver in lap_drivers:
            driver_row = lap_rows[lap_rows[driver_column] == driver]
            if not driver_row.empty:
                with st.expander(f"{driver}"):
                    ai_comment = driver_row.iloc[0]['ai_comment']
                    st.write(ai_comment)
                    if st.button(f"🔊 Audio", key=f"play_{driver}_{current_lap}"):
                        speak_text(ai_comment)
    else:
        # Show only selected driver's commentary
        if not filtered_rows.empty:
            ai_comment = filtered_rows.iloc[0]['ai_comment']
            st.markdown(f"**{selected_driver}**")
            st.write(ai_comment)
            if st.button(f"🔊 Play Commentary", key=f"play_{selected_driver}_{current_lap}"):
                speak_text(ai_comment)
else:
    # If driver column not found, show warning
    st.warning(f"Column '{driver_column}' not found in the data. Available columns: {', '.join(df.columns)}")
    filtered_rows = lap_rows
    
    # Display all commentaries
    st.subheader("Commentary")
    for i, row in lap_rows.iterrows():
        st.markdown(f"**Entry {i+1}**")
        st.write(row['ai_comment'])
        if st.button(f"🔊 Play", key=f"play_{i}"):
            speak_text(row['ai_comment'])

# Navigation buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ Previous Lap"):
        change_lap(-1)
with col2:
    if st.button("Next Lap ➡️"):
        change_lap(1)

# Final lap message
if st.session_state.lap_index == len(unique_laps) - 1:
    st.warning("This is the final lap.")