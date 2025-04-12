import os
import asyncio
from google import genai
from dotenv import load_dotenv
import pandas as pd
def getData():
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    df = pd.read_csv("ads.csv")
    df["ai_comment"] = None

    for index, row in df.iterrows():
        result = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                row.to_json(),
                "I have this data entry from a F1 race. There is relevant data about a real F1 race. Based on the information, I want you to create a comment. Limit should be 350 characters. Embellish the commentary with adjectives as well. For example, if a racer goes up in position, say something like that was an amazing overtake by <player>",
            ],
        )
        print(result.text)
        df.loc[index, "ai_comment"] = result.text

    df.to_csv("output.csv", index=False)

getData()