# Free Web Search Integration

This application now includes free web search functionality alongside the FAISS index retrieval, providing more comprehensive answers to user questions.

## How It Works

1. When a user asks a question, the application:
   - Retrieves relevant documents from the FAISS index
   - Performs a web search using Google Search
   - Combines both sources of information
   - Generates a comprehensive answer using Azure OpenAI

2. The web search results are:
   - Limited to 3 results by default (configurable)
   - Displayed with blue citation links in the sources section
   - Integrated into the context provided to the AI model

## No API Keys Required

This implementation uses a free approach to web search:
- Directly queries Google Search with a user-agent header
- Parses the HTML response using BeautifulSoup
- Extracts titles, snippets, and URLs from the search results

## Installation

Make sure to install the required dependencies:

```
pip install -r requirements.txt
```

This will install BeautifulSoup4 which is needed for HTML parsing.

## Limitations

Please note that this free web search approach has some limitations:

1. It may be less reliable than using official APIs
2. Google may occasionally block requests if too many are made in a short time
3. The HTML structure of search results may change, requiring updates to the parsing logic

## Configuration

You can adjust the web search functionality in the `app_flask.py` file:

- Change the number of web search results by modifying the `max_results` parameter in the `search_web` function
- Adjust how web results are weighted compared to document results by modifying the prompt in the `generate_answer` function
- Modify the search query formatting in the `search_web` function to improve relevance