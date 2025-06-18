import os
import uuid
import tempfile
import shutil
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Dictionary to store active PDF retrievers
active_pdf_retrievers = {}

def process_pdf(pdf_file, filename):
    """Process a PDF file and create a FAISS index for it"""
    # Generate a unique ID for this PDF
    pdf_id = str(uuid.uuid4())
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, filename)
    
    # Save the PDF file temporarily
    pdf_file.save(pdf_path)
    
    # Process the PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Create FAISS index
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    # Save the FAISS index locally
    faiss_dir = os.path.join(temp_dir, "faiss_index")
    vector_store.save_local(faiss_dir)
    
    # Upload to Azure Blob Storage
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        raise Exception("Azure Storage connection string or container name not found in .env file")
    
    # Create the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get container client
    container_client = blob_service_client.get_container_client(container_name)
    
    # Check if container exists, if not create it
    if not container_client.exists():
        container_client = blob_service_client.create_container(container_name)
    
    # Create a directory for this PDF in user_uploads
    user_upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_uploads', pdf_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Save PDF to user_uploads directory
    user_pdf_path = os.path.join(user_upload_dir, filename)
    with open(pdf_path, 'rb') as src, open(user_pdf_path, 'wb') as dst:
        dst.write(src.read())
    
    # Save FAISS index to user_uploads directory
    user_faiss_dir = os.path.join(user_upload_dir, 'faiss_index')
    os.makedirs(user_faiss_dir, exist_ok=True)
    for file_name in os.listdir(faiss_dir):
        src_path = os.path.join(faiss_dir, file_name)
        dst_path = os.path.join(user_faiss_dir, file_name)
        with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
            dst.write(src.read())
    
    # Upload PDF file to Azure Blob Storage
    with open(pdf_path, "rb") as data:
        blob_client = container_client.upload_blob(
            name=f"pdfs/{pdf_id}/{filename}",
            data=data,
            overwrite=True
        )
    
    # Upload FAISS index files to Azure Blob Storage
    for file_name in os.listdir(faiss_dir):
        file_path = os.path.join(faiss_dir, file_name)
        with open(file_path, "rb") as data:
            blob_client = container_client.upload_blob(
                name=f"pdfs/{pdf_id}/faiss_index/{file_name}",
                data=data,
                overwrite=True
            )
    
    # Create retriever and store in memory
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    active_pdf_retrievers[pdf_id] = retriever
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    
    # Return the PDF ID and metadata
    return {
        "id": pdf_id,
        "filename": filename,
        "page_count": len(documents)
    }

def get_pdf_retriever(pdf_id):
    """Get a retriever for a specific PDF"""
    # Check if retriever is in memory
    if pdf_id in active_pdf_retrievers:
        return active_pdf_retrievers[pdf_id]
    
    # If not in memory, try to load from Azure Blob Storage
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        raise Exception("Azure Storage connection string or container name not found in .env file")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    faiss_dir = os.path.join(temp_dir, "faiss_index")
    os.makedirs(faiss_dir, exist_ok=True)
    
    # Create the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get container client
    container_client = blob_service_client.get_container_client(container_name)
    
    try:
        # Download FAISS index files
        blobs = container_client.list_blobs(name_starts_with=f"pdfs/{pdf_id}/faiss_index/")
        for blob in blobs:
            file_name = os.path.basename(blob.name)
            file_path = os.path.join(faiss_dir, file_name)
            with open(file_path, "wb") as download_file:
                download_file.write(container_client.download_blob(blob.name).readall())
        
        # Create embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Load the FAISS index
        vector_store = FAISS.load_local(faiss_dir, embeddings)
        
        # Create retriever and store in memory
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        active_pdf_retrievers[pdf_id] = retriever
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return retriever
    
    except Exception as e:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        print(f"Error loading PDF retriever: {str(e)}")
        return None

def delete_pdf(pdf_id):
    """Delete a PDF and its FAISS index"""
    # Remove from memory
    if pdf_id in active_pdf_retrievers:
        del active_pdf_retrievers[pdf_id]
    
    # Remove from Azure Blob Storage
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        return False
    
    # Create the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get container client
    container_client = blob_service_client.get_container_client(container_name)
    
    try:
        # Delete all blobs with the PDF ID prefix
        blobs = container_client.list_blobs(name_starts_with=f"pdfs/{pdf_id}/")
        for blob in blobs:
            container_client.delete_blob(blob.name)
        
        return True
    
    except Exception as e:
        print(f"Error deleting PDF: {str(e)}")
        return False

def get_active_pdf_count():
    """Get the number of active PDFs"""
    return len(active_pdf_retrievers)

def list_pdfs_from_blob():
    """List all PDFs from Azure Blob Storage"""
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        return []
    
    # Create the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get container client
    container_client = blob_service_client.get_container_client(container_name)
    
    try:
        # Get all PDF directories
        pdf_ids = set()
        blobs = container_client.list_blobs(name_starts_with="pdfs/")
        
        for blob in blobs:
            # Extract PDF ID from path (pdfs/{pdf_id}/...)
            parts = blob.name.split('/')
            if len(parts) >= 2:
                pdf_ids.add(parts[1])
        
        # Get metadata for each PDF
        pdfs = []
        for pdf_id in pdf_ids:
            # Find the PDF file
            pdf_blobs = list(container_client.list_blobs(name_starts_with=f"pdfs/{pdf_id}/"))
            pdf_files = [blob for blob in pdf_blobs if not blob.name.startswith(f"pdfs/{pdf_id}/faiss_index/")]
            
            if pdf_files:
                # Get the filename
                filename = os.path.basename(pdf_files[0].name)
                
                pdfs.append({
                    "id": pdf_id,
                    "filename": filename,
                    "page_count": 0  # We don't know the page count without loading
                })
        
        return pdfs
    
    except Exception as e:
        print(f"Error listing PDFs: {str(e)}")
        return []