import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from html2text import html2text
import re
import os
from typing import List, Dict, Optional, Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS
from mcp.server.sse import SseServerTransport

# Create an MCP server instance with an identifier ("wiki")
mcp = FastMCP("sample")

@mcp.tool()
def get_customer_info(name: Optional[str] = None) -> Dict[str, str]:
    """
    Retrieve customer information from the Customers.md file.
    
    Args:
        name: Optional name to filter for a specific customer
        
    Returns:
        A dictionary with customer information
        
    Usage:
        get_customer_info("Phạm Quang Thái")
        get_customer_info()  # Returns all customers
    """
    try:
        customers_path = os.path.join(os.path.dirname(__file__), "Documentation", "Customers.md")
        
        if not os.path.exists(customers_path):
            raise FileNotFoundError(f"Customer file not found at {customers_path}")
            
        with open(customers_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract customer information using regex
        customer_entries = re.findall(r'- ([^,]+), sinh năm (\d+)\. (.+)', content)
        
        result = []
        for entry in customer_entries:
            customer_name, birth_year, description = entry
            
            # If name is provided, filter for that specific customer
            if name and name.lower() not in customer_name.lower():
                continue
                
            result.append({
                "name": customer_name,
                "birth_year": birth_year,
                "description": description
            })
            
        if name and not result:
            return {"message": f"No customer found with name containing '{name}'"}
            
        return {"customers": result}
        
    except FileNotFoundError as e:
        raise McpError(ErrorData(INTERNAL_ERROR, str(e))) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

@mcp.tool()
def text_summarize(text: str, max_sentences: int = 3) -> str:
    """
    Summarize a text by extracting the most important sentences.
    
    Args:
        text: The text to summarize
        max_sentences: Maximum number of sentences to include in the summary (default: 3)
        
    Returns:
        A string containing the summarized text.
        
    Usage:
        text_summarize("Long article text here...", 2)
    """
    try:
        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")
            
        if max_sentences < 1:
            raise ValueError("max_sentences must be at least 1")
            
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if not sentences:
            return text
            
        # Calculate word frequency (simple algorithm)
        word_freq = {}
        for sentence in sentences:
            for word in re.findall(r'\w+', sentence.lower()):
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
        # Calculate sentence scores based on word frequency
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            score = 0
            for word in re.findall(r'\w+', sentence.lower()):
                if len(word) > 3:
                    score += word_freq.get(word, 0)
            # Normalize by sentence length with a minimum to avoid division by zero
            divisor = max(len(re.findall(r'\w+', sentence)), 1)
            sentence_scores.append((i, score / divisor))
            
        # Get the top N sentences
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original order
        
        # Combine the top sentences
        summary = " ".join([sentences[i] for i, _ in top_sentences])
        
        print(f"Summary: {summary}")

        return summary
        
    except ValueError as e:
        raise McpError(ErrorData(INVALID_PARAMS, str(e))) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

# Set up the SSE transport for MCP communication.
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> None:
    _server = mcp._mcp_server
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as (reader, writer):
        await _server.run(reader, writer, _server.create_initialization_options())

# Create the Starlette app with two endpoints:
# - "/sse": for SSE connections from clients.
# - "/messages/": for handling incoming POST messages.
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
