"""Tool for performing web searches using Google Custom Search API."""

import os
from typing import List, Dict, Any
from googleapiclient.discovery import build
from ..base import Tool

class WebSearchTool(Tool):
    """
    A tool to perform web searches using the Google Custom Search JSON API. 
    
    To use this tool, you need to set up a Google Custom Search Engine (CSE)
    and have an API key. The following environment variables must be set:
    - GOOGLE_API_KEY: Your Google API key.
    - GOOGLE_CSE_ID: Your Custom Search Engine ID.
    """

    def __init__(self):
        super().__init__(
            name="web_search",
            description=(
                "Searches the web for a given query using Google Search. "
                "Returns a list of search results with titles, links, and snippets."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "The number of search results to return. Defaults to 5."
                    }
                },
                "required": ["query"]
            }
        )
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        if not self.api_key or not self.cse_id:
            self.is_configured = False
        else:
            self.is_configured = True
            self.service = build("customsearch", "v1", developerKey=self.api_key)

    def execute(self, query: str, num_results: int = 5) -> str:
        """
        Executes the web search.

        Args:
            query: The search query.
            num_results: The number of results to return.

        Returns:
            A formatted string of search results or an error message.
        """
        if not self.is_configured:
            return "Error: WebSearchTool is not configured. Please set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."

        try:
            res = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=num_results
            ).execute()

            items = res.get('items', [])
            if not items:
                return f"No results found for '{query}'."

            output = [f"Search results for '{query}':\n"]
            for i, item in enumerate(items, 1):
                output.append(f"{i}. {item['title']}\n   Link: {item['link']}\n   Snippet: {item['snippet']}\n")

            return "\n".join(output)
        except Exception as e:
            return f"An error occurred during the web search: {e}"
