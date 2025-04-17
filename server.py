import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from html2text import html2text
import re
import os
import datetime
from typing import List, Dict, Optional, Any
import json

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

# Dictionary to store cached webpage data
webpage_cache = {}

# Register CustomerData as an MCP resource
@mcp.resource("customers://data")
def get_customer_data() -> List[Dict[str, str]]:
    """
    A resource that provides access to customer data in JSON format.
    """
    return [
        {
            "name": "Phạm Quang Thái",
            "age": "24 tuổi",
            "role": "Frontend"
        },
        {
            "name": "Lê Lân",
            "age": "24 tuổi",
            "role": "Fullstack"
        },
    ]

# Register JLDesignDocumentation.md as an MCP resource
@mcp.resource("design://jl-components")
class JLDesignDocumentation:
    """
    A resource that provides access to the JL Design System documentation.
    Parses the JSON file and provides methods to query components and categories.
    """
    
    def __init__(self):
        """Initialize and load the JL Design documentation file."""
        self.components = []
        self.categories = {}
        self.colors = {}
        self.typography = {}
        self._load_documentation()
    
    def _load_documentation(self):
        """Load and parse the documentation file."""
        try:
            jl_design_path = os.path.join(os.path.dirname(__file__), "Documentation", "joblogic-design-system.json")
            
            if not os.path.exists(jl_design_path):
                raise FileNotFoundError(f"JL Design documentation file not found at {jl_design_path}")
            
            # Try different encodings to handle potential BOM or different encoding formats
            encodings_to_try = ['utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-8']
            design_system = None
            
            for encoding in encodings_to_try:
                try:
                    with open(jl_design_path, "r", encoding=encoding) as f:
                        content = f.read()
                        # Remove any potential BOM from the beginning
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        design_system = json.loads(content)
                    break  # If successful, break the loop
                except UnicodeDecodeError:
                    continue  # Try the next encoding
                except json.JSONDecodeError:
                    continue  # Try the next encoding
            
            if design_system is None:
                # If all encodings fail, try binary mode + auto-detection
                with open(jl_design_path, "rb") as f:
                    raw_data = f.read()
                    # Try to detect BOM
                    if raw_data.startswith(b'\xff\xfe') or raw_data.startswith(b'\xfe\xff'):
                        content = raw_data.decode('utf-16')
                    else:
                        content = raw_data.decode('utf-8', errors='ignore')
                    
                    design_system = json.loads(content)
            
            # Process categories and components
            if "categories" in design_system:
                self.categories = design_system["categories"]
                
                # Extract all components from categories
                for category_key, category in design_system["categories"].items():
                    if "components" in category:
                        for component in category["components"]:
                            # Add category key to component for reference
                            component["category"] = category["name"]
                            self.components.append(component)
            
            # Store colors and typography information
            if "colors" in design_system:
                self.colors = design_system["colors"]
                
            if "typography" in design_system:
                self.typography = design_system["typography"]
                
        except Exception as e:
            print(f"Error loading JL Design documentation: {str(e)}")
            # Don't raise here, just log the error
            # The resource will have empty components list
    
    def get_component(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific component.
        
        Args:
            component_name: The name of the component to retrieve.
            
        Returns:
            The component information or None if not found.
        """
        for component in self.components:
            if component["name"].lower() == component_name.lower():
                return component
        return None
    
    def get_components_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all components in a specific category.
        
        Args:
            category: The category to filter by.
            
        Returns:
            A list of components in the specified category.
        """
        result = []
        for component in self.components:
            if component["category"] and component["category"].lower() == category.lower():
                result.append(component)
        return result
    
    def get_all_components(self) -> List[Dict[str, Any]]:
        """
        Get all components.
        
        Returns:
            A list of all components.
        """
        return self.components
    
    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.
        
        Returns:
            A list of all categories.
        """
        return [category["name"] for category in self.categories.values()]
    
    def get_colors(self) -> Dict[str, Any]:
        """
        Get color definitions.
        
        Returns:
            A dictionary of color information.
        """
        return self.colors
    
    def get_typography(self) -> Dict[str, Any]:
        """
        Get typography definitions.
        
        Returns:
            A dictionary of typography information.
        """
        return self.typography

@mcp.tool()
async def get_customer_info(name: Optional[str] = None, context=None) -> Dict[str, Any]:
    """
    Retrieve customer information from the customers://data resource.
    
    Args:
        name: Optional name to filter for a specific customer
        context: The MCP context (automatically injected)
        
    Returns:
        A dictionary with customer information
        
    Usage:
        get_customer_info("Phạm Quang Thái")
        get_customer_info()  # Returns all customers
    """
    try:
        # Get customer data from the MCP resource using read_resource
        customers_data = get_customer_data()
        
        # Filter by name if provided
        if name:
            filtered_customers = []
            for customer in customers_data:
                if name.lower() in customer["name"].lower():
                    filtered_customers.append(customer)
            
            if not filtered_customers:
                return {"message": f"No customer found with name containing '{name}'"}
            
            return {"customers": filtered_customers}
        
        # Return all customers if no name filter
        return {"customers": customers_data}
        
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

@mcp.tool()
def get_jl_design_info(component_name: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract information from the JL Design System documentation.
    
    Args:
        component_name: Optional name to filter for a specific component (e.g., "Button", "Table")
        category: Optional category to filter components by category (e.g., "Form Components", "Layout Components")
        
    Returns:
        A dictionary with JL Design System information
        
    Usage:
        get_jl_design_info("Button")  # Return information about Button component
        get_jl_design_info(category="Form Components")  # Return all form components
        get_jl_design_info()  # Return all components
    """
    try:
        # Instead of trying to access the resource through the registry,
        # recreate the parsing logic directly in the tool
        jl_design_path = os.path.join(os.path.dirname(__file__), "Documentation", "joblogic-design-system.json")
        
        if not os.path.exists(jl_design_path):
            raise FileNotFoundError(f"JL Design documentation file not found at {jl_design_path}")
            
        # Create a JLDesignDocumentation instance directly
        jl_design_doc = JLDesignDocumentation()
        
        if component_name:
            component_info = jl_design_doc.get_component(component_name)
            if not component_info:
                return {"message": f"No component found with name '{component_name}'"}
            return {"component": component_info}
        
        if category:
            components = jl_design_doc.get_components_by_category(category)
            if not components:
                return {"message": f"No components found in category '{category}'"}
            return {"components": components}
        
        return {"components": jl_design_doc.get_all_components()}
        
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

@mcp.tool()
def get_frontend_guidelines() -> Dict[str, Any]:
    """
    Retrieve frontend development guidelines to help code generation agents 
    like GitHub Copilot, Cursor, etc. follow the company's coding standards.
    
    Returns:
        A dictionary containing frontend development guidelines and rules
        
    Usage:
        get_frontend_guidelines()
    """
    try:
        # Path to the frontend rules documentation
        rules_path = os.path.join(os.path.dirname(__file__), "Documentation", "FrontendRules.md")
        
        if not os.path.exists(rules_path):
            raise FileNotFoundError(f"Frontend rules documentation not found at {rules_path}")
            
        # Read the rules file
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_content = f.read()
        
        # Parse the rules (currently it's a simple format with bullet points)
        rules = []
        for line in rules_content.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                rules.append(line[2:])
            
        # Simply return the rules as defined in the documentation
        result = {
            "rules": rules,
            "source": "FrontendRules.md"
        }
        
        return result
        
    except FileNotFoundError as e:
        raise McpError(ErrorData(INTERNAL_ERROR, str(e))) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

# Helper functions for webpage fetching and parsing
async def fetch_webpage(url: str) -> Dict[str, Any]:
    """
    Fetch and parse a webpage, returning its contents and metadata
    """
    try:
        # Check if we already have a cached version
        if url in webpage_cache:
            return webpage_cache[url]
            
        # Fetch the webpage
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        html_content = response.text
        
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else None
        
        # Convert HTML to plain text
        text_content = html2text(html_content)
        
        # Cache the results
        webpage_data = {
            "url": url,
            "html_content": html_content,
            "text_content": text_content,
            "title": title,
            "fetch_time": datetime.datetime.now().isoformat()
        }
        
        webpage_cache[url] = webpage_data
        return webpage_data
        
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Failed to fetch webpage: {str(e)}"))

@mcp.tool()
async def get_company_info() -> Dict[str, Any]:
    """
    Retrieve information about Joblogic company from its website.
    
    Returns:
        A dictionary containing extracted company information
        
    Usage:
        get_company_info()
    """
    try:
        # Fixed URL for Joblogic
        url = "https://www.joblogic.com/"
        
        # Fetch the webpage (or get from cache)
        webpage = await fetch_webpage(url)
        
        # Extract company information from the webpage
        html_content = webpage["html_content"]
        text_content = webpage["text_content"]
        title = webpage["title"]
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Company name (usually in title or specific elements)
        company_name = title
        if company_name and " - " in company_name:
            company_name = company_name.split(" - ")[0].strip()
        
        # Extract contact information (common patterns)
        contact_info = {}
        
        # Look for email addresses
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
        if emails:
            contact_info["emails"] = list(set(emails))
        
        # Look for phone numbers (simple pattern)
        phones = re.findall(r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1,2}\d{3,4}[-.\s]?\d{3,4}', 
                          text_content)
        if phones:
            contact_info["phones"] = list(set(phones))
        
        # Extract meta description for company description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else None
        
        # Extract social media links
        social_media = {}
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(platform in href for platform in ['facebook.com', 'twitter.com', 'linkedin.com', 
                                                    'instagram.com', 'youtube.com']):
                for platform in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']:
                    if platform in href:
                        social_media[platform] = href
                        break
        
        # Create summary of website content
        summary = text_summarize(text_content[:10000], 3)  # Limit to first 10000 chars
        
        result = {
            "url": url,
            "title": title,
            "company_name": company_name,
            "description": description,
            "summary": summary,
            "fetch_time": webpage["fetch_time"]
        }
        
        if contact_info:
            result["contact_info"] = contact_info
            
        if social_media:
            result["social_media"] = social_media
        
        return result
        
    except McpError:
        raise
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
