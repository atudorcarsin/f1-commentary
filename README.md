# f1-commentary
Bit Camp 2025 Project

## Description

Generate F1 commentary based on data provided through a CSV file. 

## Usage

1. Create a Python virtual environment
2. Install the required packages (requirements.txt)
3. Create a .env file with the GEMINI_API_KEY field
3. Add an input CSV file to the root project directory called "ads.csv"
4. Run gemini.py to generate short commentary for each row in the CSV file
5. Run streamlit.py to generate a streamlit app that displays the commentary (`streamlit run streamlit.py`)