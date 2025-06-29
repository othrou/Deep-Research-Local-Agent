# src/tools.py

import os
import httpx
import requests
from typing import Dict, Any, List, Union, Optional

from markdownify import markdownify
#from langsmith import traceable
from tavily import TavilyClient
from duckduckgo_search import DDGS

from langchain_community.utilities import SearxSearchWrapper

# --- [Existing code from your file] ---

def get_config_value(value: Any) -> str:
    """
    Convert configuration values to string format, handling both string and enum types.
    """
    return value if isinstance(value, str) else value.value

def strip_thinking_tokens(text: str) -> str:
    """
    Remove <think> and </think> tags and their content from the text.
    """
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>") + len("</think>")
        text = text[:start] + text[end:]
    return text

def deduplicate_and_format_sources(
    search_response: Union[Dict[str, Any], List[Dict[str, Any]]],
    max_tokens_per_source: int,
    fetch_full_page: bool = False
) -> str:
    """
    Format and deduplicate search responses from various search APIs.
    """
    if isinstance(search_response, dict):
        sources_list = search_response.get('results', [])
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and 'results' in response:
                sources_list.extend(response['results'])
            else:
                sources_list.extend(response)
    else:
        raise ValueError("Input must be either a dict with 'results' or a list of search results")

    unique_sources = {}
    for source in sources_list:
        if source.get('url') and source['url'] not in unique_sources:
            unique_sources[source['url']] = source

    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source: {source.get('title', 'No Title')}\n===\n"
        formatted_text += f"URL: {source.get('url')}\n===\n"
        formatted_text += f"Most relevant content from source: {source.get('content', '')}\n===\n"
        if fetch_full_page:
            char_limit = max_tokens_per_source * 4
            raw_content = source.get('raw_content', '') or ''
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"

    return formatted_text.strip()


def format_sources(search_results: Dict[str, Any]) -> str:
    """
    Format search results into a bullet-point list of sources with URLs.
    """
    results = search_results.get('results', [])
    return '\n'.join(
        f"* {source.get('title', 'No Title')} : {source.get('url', 'No URL')}"
        for source in results
    )

def fetch_raw_content(url: str) -> Optional[str]:
    """
    Fetch HTML content from a URL and convert it to markdown format.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return markdownify(response.text)
    except Exception as e:
        print(f"Warning: Failed to fetch full page content for {url}: {str(e)}")
        return None

#@traceable
def duckduckgo_search(query: str, max_results: int = 3, fetch_full_page: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search the web using DuckDuckGo and return formatted results.
    """
    try:
        with DDGS() as ddgs:
            results = []
            search_results = list(ddgs.text(query, max_results=max_results))
            for r in search_results:
                raw_content = r.get('body', '')
                if fetch_full_page:
                    raw_content = fetch_raw_content(r.get('href'))
                result = {
                    "title": r.get('title'), "url": r.get('href'),
                    "content": r.get('body'), "raw_content": raw_content
                }
                results.append(result)
            return {"results": results}
    except Exception as e:
        print(f"Error in DuckDuckGo search: {str(e)}")
        return {"results": []}

#@traceable
def searxng_search(query: str, max_results: int = 3, fetch_full_page: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search the web using SearXNG and return formatted results.
    """
    host = os.environ.get("SEARXNG_URL", "http://localhost:8888")
    s = SearxSearchWrapper(searx_host=host)
    results = []
    search_results = s.results(query, num_results=max_results)
    for r in search_results:
        raw_content = r.get('snippet', '')
        if fetch_full_page:
            raw_content = fetch_raw_content(r.get('link'))
        result = {
            "title": r.get('title'), "url": r.get('link'),
            "content": r.get('snippet'), "raw_content": raw_content
        }
        results.append(result)
    return {"results": results}

#@traceable
def tavily_search(query: str, fetch_full_page: bool = True, max_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search the web using the Tavily API and return formatted results.
    """
    tavily_client = TavilyClient()
    response = tavily_client.search(
        query, max_results=max_results, include_raw_content=fetch_full_page
    )
    # Ensure the response structure is consistent with other tools
    return {"results": response.get('results', [])}


#@traceable
def perplexity_search(query: str, perplexity_search_loop_count: int = 0) -> Dict[str, Any]:
    """
    Search the web using the Perplexity API and return formatted results.
    """
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "Search the web and provide factual information with sources."},
            {"role": "user", "content": query}
        ]
    }
    try:
        response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", ["https://perplexity.ai"])

        results = [{
            "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source 1",
            "url": citations[0], "content": content, "raw_content": content
        }]
        for i, citation in enumerate(citations[1:], start=2):
            results.append({
                "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source {i}",
                "url": citation, "content": "See above for full content", "raw_content": None
            })
        return {"results": results}
    except Exception as e:
        print(f"Error in Perplexity search: {str(e)}")
        return {"results": []}


# --- [NEW Tools added] ---

#@traceable
def save_report_as_html(title: str, content: str) -> str:
    """
    Saves the given HTML content to a local file.

    Args:
        title (str): The title of the report, used for the filename.
        content (str): The HTML content of the report.

    Returns:
        str: A confirmation message with the path to the saved file.
    """
    filename = f"{title.replace(' ', '_').lower()}_report.html"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved report to '{filename}'"
    except Exception as e:
        return f"Failed to save report. Error: {e}"




# --- [ADVANCED: Optional Google Docs Tool] ---
# Note: This requires significant setup:
# 1. `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
# 2. Enable the Google Docs API in your Google Cloud project.
# 3. Create OAuth 2.0 Client IDs and download the `credentials.json` file.
# 4. The first time you run it, you'll need to go through the browser-based auth flow.
#
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
#
# SCOPES = ["https://www.googleapis.com/auth/documents"]
#
# @traceable
# def create_google_doc(title: str, content: str) -> str:
#     """
#     Creates a new Google Doc with the given title and content.
#     Note: This is a simplified example; HTML to Google Docs conversion is complex.
#     This function will insert plain text.
#     """
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
#
#     try:
#         service = build("docs", "v1", credentials=creds)
#         document = service.documents().create(body={'title': title}).execute()
#         doc_id = document.get('documentId')
#
#         # Convert basic HTML to text for simplicity
#         from bs4 import BeautifulSoup
#         soup = BeautifulSoup(content, "html.parser")
#         text_content = soup.get_text()
#
#         requests = [
#             {
#                 'insertText': {
#                     'location': { 'index': 1 },
#                     'text': text_content
#                 }
#             }
#         ]
#         service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
#
#         doc_url = f"https://docs.google.com/document/d/{doc_id}"
#         return f"Successfully created Google Doc: {doc_url}"
#     except HttpError as err:
#         return f"An error occurred: {err}"