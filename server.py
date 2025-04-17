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

# Register JLInternalAPIDocumentation as an MCP resource
@mcp.resource("api://jl-internal-api")
class JLInternalAPIDocumentation:
    """
    A resource that provides access to the Joblogic Internal API documentation.
    Parses the OpenAPI specification file and provides methods to query endpoints, paths, and schemas.
    """
    
    def __init__(self):
        """Initialize and load the Joblogic Internal API documentation file."""
        self.api_spec = {}
        self.paths = {}
        self.schemas = {}
        self.tags = set()
        self._load_documentation()
    
    def _load_documentation(self):
        """Load and parse the documentation file."""
        try:
            api_spec_path = os.path.join(os.path.dirname(__file__), "Documentation", "joblogic-internal-api.json")
            
            if not os.path.exists(api_spec_path):
                raise FileNotFoundError(f"Joblogic Internal API documentation file not found at {api_spec_path}")
            
            # Try different encodings to handle potential BOM or different encoding formats
            encodings_to_try = ['utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-8']
            api_spec = None
            
            for encoding in encodings_to_try:
                try:
                    with open(api_spec_path, "r", encoding=encoding) as f:
                        content = f.read()
                        # Remove any potential BOM from the beginning
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        api_spec = json.loads(content)
                    break  # If successful, break the loop
                except UnicodeDecodeError:
                    continue  # Try the next encoding
                except json.JSONDecodeError:
                    continue  # Try the next encoding
            
            if api_spec is None:
                # If all encodings fail, try binary mode + auto-detection
                with open(api_spec_path, "rb") as f:
                    raw_data = f.read()
                    # Try to detect BOM
                    if raw_data.startswith(b'\xff\xfe') or raw_data.startswith(b'\xfe\xff'):
                        content = raw_data.decode('utf-16')
                    else:
                        content = raw_data.decode('utf-8', errors='ignore')
                    
                    api_spec = json.loads(content)
            
            self.api_spec = api_spec
            
            # Process paths, schemas and tags
            if "paths" in api_spec:
                self.paths = api_spec["paths"]
                
                # Extract all tags from paths
                for path, methods in self.paths.items():
                    for method, details in methods.items():
                        if isinstance(details, dict) and "tags" in details:
                            for tag in details["tags"]:
                                self.tags.add(tag)
            
            if "components" in api_spec and "schemas" in api_spec["components"]:
                self.schemas = api_spec["components"]["schemas"]
                
        except Exception as e:
            print(f"Error loading Joblogic Internal API documentation: {str(e)}")
            # Don't raise here, just log the error
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get basic API information (title, version).
        
        Returns:
            A dictionary with API information.
        """
        if "info" in self.api_spec:
            return self.api_spec["info"]
        return {}
    
    def get_all_tags(self) -> List[str]:
        """
        Get all API tags/categories.
        
        Returns:
            A list of all tags.
        """
        return list(self.tags)
    
    def get_endpoints_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all endpoints for a specific tag.
        
        Args:
            tag: The tag to filter by.
            
        Returns:
            A list of endpoints (path, method, operationId) for the specified tag.
        """
        result = []
        
        for path, methods in self.paths.items():
            for method, details in methods.items():
                if isinstance(details, dict) and "tags" in details and tag in details["tags"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "operationId": details.get("operationId", ""),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", "")
                    }
                    result.append(endpoint)
        
        return result
    
    def get_endpoint_details(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific endpoint.
        
        Args:
            path: The API path.
            method: The HTTP method (GET, POST, etc.)
            
        Returns:
            A dictionary with endpoint details or None if not found.
        """
        method = method.lower()
        if path in self.paths and method in self.paths[path]:
            return self.paths[path][method]
        return None
    
    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema information for a specific schema name.
        
        Args:
            schema_name: The name of the schema to retrieve.
            
        Returns:
            A dictionary with schema details or None if not found.
        """
        if schema_name in self.schemas:
            return self.schemas[schema_name]
        return None
    
    def search_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for endpoints matching the query in path or operationId.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching endpoints.
        """
        query = query.lower()
        result = []
        
        for path, methods in self.paths.items():
            path_lower = path.lower()
            
            for method, details in methods.items():
                if not isinstance(details, dict):
                    continue
                    
                operation_id = details.get("operationId", "").lower()
                description = details.get("description", "").lower()
                summary = details.get("summary", "").lower()
                
                if (query in path_lower or 
                    query in operation_id or 
                    query in description or 
                    query in summary):
                    
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "operationId": details.get("operationId", ""),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", "")
                    }
                    result.append(endpoint)
        
        return result

# Register the tool to query Joblogic Internal API information
@mcp.tool()
def get_internal_api_info(tag: Optional[str] = None, search_query: Optional[str] = None, path: Optional[str] = None, method: Optional[str] = None) -> Dict[str, Any]:
    """
    Query information from the Joblogic Internal API documentation to help agents
    implement features that integrate with this microservice.
    
    Args:
        tag: Optional tag name to filter endpoints by a specific category (e.g., "Job", "Customer", "Invoice")
        search_query: Optional search term to find relevant endpoints
        path: Optional specific API path to get details for (e.g., "/api/tenancy/{tenantId}/job")
        method: Optional HTTP method to use with path parameter (e.g., "GET", "POST")
        
    Returns:
        A dictionary with information about the Joblogic Internal API
        
    Usage:
        get_internal_api_info(tag="Job")  # Return all Job-related endpoints
        get_internal_api_info(search_query="customer")  # Search for endpoints related to customers
        get_internal_api_info(path="/api/tenancy/{tenantId}/job", method="POST")  # Get details for a specific endpoint
        get_internal_api_info()  # Return general API information and available tags
    """
    try:
        # Create a JLInternalAPIDocumentation instance directly
        api_doc = JLInternalAPIDocumentation()
        
        # Handle different query types
        if path and method:
            # Get specific endpoint details
            endpoint_details = api_doc.get_endpoint_details(path, method)
            if not endpoint_details:
                return {"message": f"No endpoint found for {method} {path}"}
            return {"endpoint": endpoint_details}
        
        if tag:
            # Get endpoints for a specific tag
            endpoints = api_doc.get_endpoints_by_tag(tag)
            if not endpoints:
                return {"message": f"No endpoints found for tag '{tag}'"}
            return {"tag": tag, "endpoints": endpoints}
        
        if search_query:
            # Search for endpoints
            endpoints = api_doc.search_endpoints(search_query)
            if not endpoints:
                return {"message": f"No endpoints found matching '{search_query}'"}
            return {"search_query": search_query, "endpoints": endpoints}
        
        # Default: return API info and available tags
        api_info = api_doc.get_api_info()
        tags = api_doc.get_all_tags()
        
        return {
            "api_info": api_info,
            "available_tags": tags,
            "message": "Use the 'tag', 'search_query', or 'path'+'method' parameters to get more specific information."
        }
        
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

# Register the tool to guide code generation for Joblogic Internal API integration
@mcp.tool()
def guide_backend_implementation(feature_description: str, endpoints_needed: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Provides guidance for implementing new backend features that integrate with the 
    Joblogic Internal API microservice.
    
    Args:
        feature_description: Description of the feature to implement
        endpoints_needed: Optional list of specific endpoints that will be used
        
    Returns:
        A dictionary containing implementation guidance and best practices
        
    Usage:
        guide_backend_implementation("Create an endpoint to list all jobs with pagination")
        guide_backend_implementation("Implement invoice payment processing")
    """
    try:
        # Create a JLInternalAPIDocumentation instance
        api_doc = JLInternalAPIDocumentation()
        
        # Extract keywords from feature description to suggest relevant endpoints
        keywords = extract_keywords(feature_description.lower())
        
        suggested_endpoints = []
        relevant_tags = set()
        
        # Search for relevant endpoints based on keywords
        for keyword in keywords:
            endpoints = api_doc.search_endpoints(keyword)
            for endpoint in endpoints:
                # Check if this is a new endpoint suggestion
                is_new = True
                for existing in suggested_endpoints:
                    if (existing["path"] == endpoint["path"] and 
                        existing["method"] == endpoint["method"]):
                        is_new = False
                        break
                
                if is_new:
                    suggested_endpoints.append(endpoint)
                    
                    # Track relevant tags
                    endpoint_details = api_doc.get_endpoint_details(endpoint["path"], endpoint["method"])
                    if endpoint_details and "tags" in endpoint_details:
                        for tag in endpoint_details["tags"]:
                            relevant_tags.add(tag)
        
        # For specific endpoints requested, get their details
        specific_endpoints = []
        if endpoints_needed:
            for endpoint_str in endpoints_needed:
                if " " in endpoint_str:
                    method, path = endpoint_str.split(" ", 1)
                    endpoint_details = api_doc.get_endpoint_details(path.strip(), method.strip())
                    if endpoint_details:
                        specific_endpoints.append({
                            "path": path.strip(),
                            "method": method.strip(),
                            "details": endpoint_details
                        })
        
        # Compile guidance
        best_practices = [
            "Always include the tenantId parameter when calling tenancy-specific endpoints",
            "Use proper error handling to catch and process API errors",
            "Consider implementing a retry mechanism for transient failures",
            "Use DTOs to map between your application models and the API request/response models",
            "Log all API calls for debugging and monitoring purposes",
            "Cache responses when appropriate to reduce API calls"
        ]
        
        implementation_steps = [
            "1. Create interface/models that match the API request/response structures",
            "2. Implement a service to handle HTTP communication with the API",
            "3. Create controllers or handlers that use the service to fetch/send data",
            "4. Implement error handling and validation",
            "5. Add unit tests simulating API responses"
        ]
        
        result = {
            "feature": feature_description,
            "best_practices": best_practices,
            "implementation_steps": implementation_steps,
            "relevant_tags": list(relevant_tags)
        }
        
        if suggested_endpoints:
            result["suggested_endpoints"] = suggested_endpoints[:10]  # Limit to top 10
            
        if specific_endpoints:
            result["specific_endpoints"] = specific_endpoints
            
        return result
        
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

def extract_keywords(text):
    """Extract keywords from text, removing common words."""
    # Common words to exclude
    common_words = {"a", "an", "the", "to", "and", "or", "of", "in", "for", "with", "on", "at", "by", "from"}
    
    # Split text into words and filter out common words
    words = text.lower().split()
    keywords = [word for word in words if word not in common_words and len(word) > 2]
    
    return keywords

# Register the tool to fetch JL Design System information
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

# Register the tool to fetch frontend development guidelines
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

# Register the tool to fetch backend development guidelines
@mcp.tool()
def get_backend_guidelines() -> Dict[str, Any]:
    """
    Retrieve backend development guidelines to help code generation agents 
    like GitHub Copilot, Cursor, etc. follow the company's coding standards.
    
    Returns:
        A dictionary containing backend development guidelines and rules
        
    Usage:
        get_backend_guidelines()
    """
    try:
        # Path to the backend rules documentation
        rules_path = os.path.join(os.path.dirname(__file__), "Documentation", "BackendRules.md")
        
        if not os.path.exists(rules_path):
            raise FileNotFoundError(f"Backend rules documentation not found at {rules_path}")
            
        # Read the rules file
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_content = f.read()
        
        # Parse the rules from the markdown structure
        sections = {}
        current_section = "General"
        rules = []
        
        for line in rules_content.split('\n'):
            line = line.strip()
            
            # Handle section headers (## Section Name)
            if line.startswith('## '):
                current_section = line[3:].strip()
                sections[current_section] = []
            # Handle rules (- Rule text)
            elif line.startswith('- '):
                rule_text = line[2:]
                if current_section in sections:
                    sections[current_section].append(rule_text)
                else:
                    rules.append(rule_text)
        
        # Prepare the result
        result = {
            "rules": rules,
            "sections": sections,
            "source": "BackendRules.md"
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
