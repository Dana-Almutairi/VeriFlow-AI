
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.tokenfactory.nebius.com/v1/",
    timeout=60.0,
    max_retries=0,
)

MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an evidence verification assistant. "
                    "Never invent sources or evidence. "
                    "Clearly distinguish verified facts from claims."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyze this claim: "
                    "'Every AI-generated answer is factually correct.' "
                    "Explain whether the claim is reliable in 3 sentences."
                ),
            },
        ],
        temperature=0.2,
        max_tokens=350,
    )

    print("SUCCESS: NVIDIA Nemotron is running!")
    print()
    print("MODEL:", response.model)
    print()
    print("AI RESPONSE:")
    print(response.choices[0].message.content)

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))
