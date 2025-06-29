import os
import httpx
from typing import Dict, Any, List, Optional
from markdownify import markdownify
#from langsmith import traceable
from duckduckgo_search import DDGS
from langchain_community.utilities import SearxSearchWrapper

#@traceable
def save_report_as_html(title: str, content: str) -> str:
    """
    Saves the given HTML content to a local file in the 'reports' directory.

    Args:
        title (str): The title of the report, used for the filename.
        content (str): The HTML content of the report.

    Returns:
        str: A confirmation message with the path to the saved file.
    """
    # Create a 'reports' directory if it doesn't exist
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    filename = f"reports/{title.replace(' ', '_').lower()}_report.html"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved report to '{os.path.abspath(filename)}'"
    except Exception as e:
        return f"Failed to save report. Error: {e}"

def fetch_raw_content(url: str) -> Optional[str]:
    """
    Fetch HTML content from a URL and convert it to markdown format.
    Uses a 10-second timeout to avoid hanging on slow sites.
    """
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
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
    print(f"Executing DuckDuckGo search for: {query}")
    try:
        with DDGS() as ddgs:
            results = []
            search_results = list(ddgs.text(query, max_results=max_results))
            for r in search_results:
                raw_content = r.get('body', '')
                if fetch_full_page and r.get('href'):
                    raw_content = fetch_raw_content(r.get('href'))
                result = {
                    "title": r.get('title'),
                    "url": r.get('href'),
                    "content": r.get('body'),
                    "raw_content": raw_content
                }
                results.append(result)
            return {"results": results}
    except Exception as e:
        print(f"Error in DuckDuckGo search: {str(e)}")
        return {"results": []}

#@traceable
def searxng_search(query: str, max_results: int = 3, fetch_full_page: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search the web using a SearXNG instance and return formatted results.
    The host URL is read from the SEARXNG_URL environment variable or defaults to a local instance.
    """
    print(f"Executing SearXNG search for: {query}")
    host = os.environ.get("SEARXNG_URL", "http://localhost:8888")
    search = SearxSearchWrapper(searx_host=host)
    
    try:
        results = []
        search_results = search.results(query, num_results=max_results)
        for r in search_results:
            raw_content = r.get('snippet', '')
            if fetch_full_page and r.get('link'):
                raw_content = fetch_raw_content(r.get('link'))
            result = {
                "title": r.get('title'),
                "url": r.get('link'),
                "content": r.get('snippet'),
                "raw_content": raw_content
            }
            results.append(result)
        return {"results": results}
    except Exception as e:
        print(f"Error in SearXNG search: {str(e)}")
        return {"results": []}
