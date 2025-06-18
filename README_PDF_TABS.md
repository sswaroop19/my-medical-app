# Medical PDF Assistant with Tabs

This application allows you to upload PDF files, process them with FAISS indexing, and chat with each PDF in separate tabs. The application stores all PDFs and their FAISS indexes in Azure Blob Storage for persistent access.

## Features

- Upload PDF files and automatically create FAISS indexes
- Store PDFs and indexes in Azure Blob Storage
- Create a separate tab for each PDF
- Chat with each PDF independently
- View and load previously uploaded PDFs

## Setup

1. Make sure you have all required dependencies installed:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:

```
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
BLOB_CONTAINER_NAME=your_blob_container_name
HUGGINGFACE_API_TOKEN=your_huggingface_token
```

## Running the Application

### Windows

```bash
run_pdf_tabs.bat
```

### Linux/Mac

```bash
streamlit run app_pdf_tabs.py
```

## How It Works

1. **PDF Upload**: When you upload a PDF, the application:
   - Processes the PDF and extracts text
   - Creates chunks of text
   - Generates embeddings using HuggingFace's sentence-transformers
   - Creates a FAISS index for efficient retrieval
   - Uploads both the PDF and FAISS index to Azure Blob Storage with a unique ID

2. **PDF Tabs**: Each PDF gets its own tab where you can:
   - View basic information about the PDF
   - Chat with the PDF using a question-answering interface
   - Close the tab when you're done

3. **Persistent Storage**: All PDFs and their FAISS indexes are stored in Azure Blob Storage, so you can:
   - Access previously uploaded PDFs
   - Load PDFs from storage without re-processing
   - Share PDFs and their indexes across different sessions

## Troubleshooting

- If you encounter issues with PDF processing, check that your PDF is readable and not password-protected
- If Azure Blob Storage connections fail, verify your connection string and container name in the `.env` file
- For HuggingFace API issues, ensure your API token is valid and has the necessary permissions

## Command-Line Tools

The `upload_faiss_to_blob.py` script provides command-line tools for managing PDFs and FAISS indexes:

```bash
# Upload a single PDF
python upload_faiss_to_blob.py upload path/to/pdf

# Upload all PDFs in a directory
python upload_faiss_to_blob.py upload_dir path/to/directory

# List all uploaded PDFs
python upload_faiss_to_blob.py list

# Download a FAISS index
python upload_faiss_to_blob.py download upload_id
```