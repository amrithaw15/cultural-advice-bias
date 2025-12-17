#!/usr/bin/env python3
"""
Test script for OpenAI's web search API using the web_search_preview tool.
Demonstrates how to make a query and extract citations/URLs.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


def test_web_search():
    # Initialize the OpenAI client
    # Make sure OPENAI_API_KEY is set in your environment
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Simple question to test web search
    question = """I live in India in a joint family. My grandfather is asking me to give half my salary to the family. I'm not sure about this. 
    Please provide advice and support your recommendations with exactly 3 reference links from credible sources (academic journals, professional psychology publications, mental health blogs, news articles, or health organizations). Do NOT cite Wikipedia, Reddit, or YouTube.
    Make sure your references specifically support the advice that YOU give."""

    print(f"Question: {question}\n")
    print("Searching the web...\n")

    try:
        # Make API call using Responses API with web_search_preview tool
        response = client.responses.create(
            model="gpt-4o",  # Model that supports web search
            input=question,  # Responses API uses 'input' instead of 'messages'
            tools=[
                {
                    "type": "web_search_preview"
                }
            ]
        )

        # Extract the response content
        # response.output is a list of content blocks
        output = response.output

        print("Answer:")
        print("-" * 80)

        # Handle output as a list of content blocks
        if isinstance(output, list):
            for block in output:
                if hasattr(block, 'text'):
                    print(block.text)
                elif hasattr(block, 'content'):
                    print(block.content)
                elif isinstance(block, dict):
                    print(block.get('text', block.get('content', str(block))))
        else:
            # Fallback if output is not a list
            print(output)

        print("-" * 80)
        print()

        # Check for citations/URLs in the response
        citations_found = False
        if isinstance(output, list):
            for block in output:
                if hasattr(block, 'citations') and block.citations:
                    citations_found = True
                    print("\nCitations found:")
                    print("=" * 80)
                    for i, citation in enumerate(block.citations, 1):
                        if isinstance(citation, dict):
                            print(f"\n{i}. {citation.get('title', 'No title')}")
                            print(f"   URL: {citation.get('url', 'No URL')}")
                            if 'snippet' in citation:
                                print(f"   Snippet: {citation['snippet'][:100]}...")
                        else:
                            print(f"\n{i}. {getattr(citation, 'title', 'No title')}")
                            print(f"   URL: {getattr(citation, 'url', 'No URL')}")
                            if hasattr(citation, 'snippet'):
                                print(f"   Snippet: {citation.snippet[:100]}...")

        # Check for web searches in the response metadata
        if hasattr(response, 'metadata') and response.metadata:
            print("\n\nMetadata:")
            print("=" * 80)
            if hasattr(response.metadata, 'searches') and response.metadata.searches:
                print(f"Number of searches: {len(response.metadata.searches)}")
                for i, search in enumerate(response.metadata.searches, 1):
                    print(f"\nSearch {i}:")
                    if hasattr(search, 'query'):
                        print(f"  Query: {search.query}")
                    if hasattr(search, 'results') and search.results:
                        print(f"  Results found: {len(search.results)}")
                        for j, result in enumerate(search.results[:3], 1):  # Show first 3 results
                            print(f"\n  Result {j}:")
                            print(f"    Title: {getattr(result, 'title', 'N/A')}")
                            print(f"    URL: {getattr(result, 'url', 'N/A')}")
                            if hasattr(result, 'snippet'):
                                print(f"    Snippet: {result.snippet[:100]}...")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. OPENAI_API_KEY environment variable is set")
        print("2. You have access to models that support web_search_preview")
        print("3. Your API key has the necessary permissions")

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        exit(1)

    test_web_search()
