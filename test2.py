import sys
from google import genai
from google.genai import types
from duckduckgo_search import DDGS
from googlesearch import search as google_search

# 1. Initialize the client with your free Gemini API key
client = genai.Client(api_key='AIzaSyAhv_TR59bqrtmpNjeTWR0aWNOVzKaBXb8')


def get_duckduckgo_results(search_query: str, max_results: int = 4):
    """Fetch snippets from DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=max_results))
        return [f"[DuckDuckGo] {r['title']}\nSnippet: {r['body']}" for r in results]
    except Exception as e:
        print(f"⚠️ DuckDuckGo search failed ({e}).")
        return []


def get_google_results(search_query: str, max_results: int = 4):
    """Fetch result URLs/titles from the googlesearch-python library."""
    try:
        results = []
        # advanced=True returns SearchResult objects with title/description/url
        for r in google_search(search_query, num_results=max_results, advanced=True):
            results.append(f"[Google] {r.title}\nSnippet: {r.description}\nURL: {r.url}")
        return results
    except Exception as e:
        print(f"⚠️ Google search failed ({e}).")
        return []


def get_live_web_context(user_prompt: str) -> str:
    """Combines DuckDuckGo and Google search results into one context block."""
    search_query = f"trending music songs charts 2026 {user_prompt}"
    print(f"\n🔍 [REAL-TIME] Searching the web right now for: '{search_query}'...")

    ddg_snippets = get_duckduckgo_results(search_query)
    google_snippets = get_google_results(search_query)

    all_snippets = ddg_snippets + google_snippets

    if not all_snippets:
        return "No recent web articles found. Fall back to current 2026 popular tracks."

    return "\n\n".join(all_snippets)


def run_music_assistant():
    print("=" * 60)
    print("🎵 Live Music Assistant Loaded! 🎵")
    print("Enter your query below for a real-time web search.")
    print("Type 'exit' to stop.")
    print("=" * 60)

    while True:
        user_request = input("\n👤 Enter your query: ").strip()
        if user_request.lower() in ['exit', 'quit']:
            print("Goodbye! 🎧")
            break
        if not user_request:
            continue

        # RUN REAL-TIME SEARCH (DuckDuckGo + Google) FOR THIS QUERY
        live_web_context = get_live_web_context(user_request)

        # Inject the combined live data into the system prompt
        SYSTEM_INSTRUCTION = f"""You are a knowledgeable, enthusiastic music recommendation assistant. 
When a user describes a mood, genre, artist, occasion, or activity, recommend songs that fit. 
CRITICAL REAL-TIME CONTEXT (Use this fresh data to build your answer):
{live_web_context}

For every recommendation:
- Give the song title and artist
- One short sentence on why it fits the request
- Mention if it's a very recent/trending release"""

        print("🚀 Sending live context to Gemini...")
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=user_request,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )
            print("\n✨ Gemini's Live Response:")
            print(response.text)
            print("-" * 40)
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    run_music_assistant()