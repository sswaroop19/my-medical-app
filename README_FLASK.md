# Medical Gynecology Assistant - Flask Web Application

This is a Flask-based web application that uses a FAISS index stored in Azure Blob Storage to provide evidence-based answers to gynecology questions.

## Features

- Modern, user-friendly interface similar to popular AI chat applications
- Retrieves FAISS index from Azure Blob Storage
- Falls back to local FAISS index if Azure Blob Storage is not available
- Uses Azure OpenAI to generate responses based on retrieved documents
- Provides citations and sources for all information

## Prerequisites

1. An Azure account with:
   - Azure OpenAI service
   - Azure Blob Storage account
2. FAISS index already created locally (using preprocess.py)
3. Python 3.8+ installed

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure your `.env` file with Azure credentials:
   ```
   # Azure OpenAI settings
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_KEY=your-api-key
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name

   # Azure Storage settings
   AZURE_STORAGE_CONNECTION_STRING=your-connection-string
   BLOB_CONTAINER_NAME=medical-docs
   ```

3. Upload your FAISS index to Azure Blob Storage:
   ```
   python upload_faiss_to_blob.py
   ```

## Running the Application

Run the Flask application:

```
python app_flask.py
```

The application will:
1. Start a web server on http://localhost:5000
2. Download the FAISS index from Azure Blob Storage (or use local index if not available)
3. Initialize the Azure OpenAI client
4. Serve the web interface

## Using the Application

1. Open your browser and navigate to http://localhost:5000
2. You'll see a welcome screen with example questions
3. Type your question in the input field or click on an example question
4. Click "Ask" or press Enter to submit your question
5. The application will retrieve relevant documents and generate an answer
6. The answer will be displayed with citations and sources

## Deployment

To deploy this application to production, you can:

1. Use Azure App Service:
   - Create an App Service plan
   - Deploy the application using Azure CLI or Visual Studio Code
   - Configure environment variables in the Azure Portal

2. Use Docker:
   - Create a Dockerfile for the application
   - Build and push the Docker image to a registry
   - Deploy the container to Azure Container Instances or Azure Kubernetes Service

## Troubleshooting

- If you encounter errors related to Azure Blob Storage, check your connection string and container name
- If you encounter errors related to Azure OpenAI, check your endpoint, API key, and deployment name
- If the application falls back to local index, check the console output for details