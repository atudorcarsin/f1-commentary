import os
from google import genai
from dotenv import load_dotenv
import pandas as pd

def getData():
    load_dotenv()

    df = pd.read_csv("ads.csv")
    df["ai_comment"] = None

    for index, row in df.iterrows():
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        try:
            result = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=[
                    row.to_json(),
                    "I have this data entry from a F1 race. There is relevant data about a real F1 race. Based on the information, I want you to create a comment. Limit should be 350 characters. Embellish the commentary with adjectives as well. For example, if a racer goes up in position, say something like that was an amazing overtake by <player>. Give me just the commentary, and nothing else.",
                ],
            )
            print(result.text)
            df.loc[index, "ai_comment"] = result.text
        except Exception as e:
            print(e)
            break

    df.to_csv("output.csv", index=False)

getData()