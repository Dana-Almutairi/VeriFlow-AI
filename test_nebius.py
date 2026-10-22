
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.tokenfactory.nebius.com/v1/",
    timeout=30.0,
    max_retries=0
)

try:
    models = client.models.list()
    print("SUCCESS: Connected to Nebius!")

    for model in models.data:
        if "nemotron" in model.id.lower():
            print("NVIDIA Model:", model.id)

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))
