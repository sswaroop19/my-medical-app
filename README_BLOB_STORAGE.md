# Using Azure Blob Storage with FAISS Index

This guide explains how to upload your FAISS index to Azure Blob Storage and use it in your Streamlit application.

## Prerequisites

1. An Azure account with a Storage Account
2. FAISS index already created locally (using preprocess.py)
3. Python 3.8+ installed

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure your `.env` file with Azure Storage credentials:
   ```
   # Azure OpenAI settings
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_KEY=your-api-key
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name

   # Azure Storage settings
   AZURE_STORAGE_CONNECTION_STRING=your-connection-string
   BLOB_CONTAINER_NAME=medical-docs
   ```

   You can get your connection string from the Azure Portal:
   - Go to your Storage Account
   - Navigate to "Access keys" under "Security + networking"
   - Copy the connection string

## Uploading FAISS Index to Azure Blob Storage

Run the upload script:

```
python upload_faiss_to_blob.py
```

This will:
1. Create a zip file of your FAISS index
2. Upload the zip file to your Azure Blob Storage container
3. Also upload the individual files for direct access

## Running the Streamlit App

After uploading the index, you can run the Streamlit app:

```
streamlit run app_azure_updated.py
```

The app will:
1. Check if Azure Blob Storage credentials are available
2. If available, download the FAISS index from Blob Storage
3. If not available or if download fails, fall back to local FAISS index
4. Use the index for retrieval in the RAG system

## Troubleshooting

- If you encounter errors related to Azure Blob Storage, check your connection string and container name
- Make sure your container exists or has proper permissions to be created
- If the app falls back to local index, check the error message in the sidebar for details

## Benefits of Using Azure Blob Storage

- Centralized storage accessible from multiple deployment environments
- No need to rebuild the index on each deployment
- Easier to update the index without redeploying the application
- Better scalability for larger indices