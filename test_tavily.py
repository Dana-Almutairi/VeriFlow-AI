
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv(override=True)

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise RuntimeError("TAVILY_API_KEY is missing")

client = TavilyClient(api_key=api_key)

try:
    response = client.search(
        query="Can artificial intelligence generate false information?",
        search_depth="basic",
        max_results=3,
    )

    print("SUCCESS: Tavily search is working!")

    for index, result in enumerate(response.get("results", []), 1):
        print()
        print(f"SOURCE {index}")
        print("Title:", result.get("title"))
        print("URL:", result.get("url"))
        print("Content:", result.get("content", "")[:400])

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))
