import os
import uuid
import shutil
import tempfile
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

def process_and_upload_pdf(pdf_path, filename=None):
    """
    Process a PDF file, create a FAISS index, and upload both to Azure Blob Storage
    
    Args:
        pdf_path: Path to the PDF file
        filename: Optional filename to use (if not provided, uses basename of pdf_path)
        
    Returns:
        dict: Information about the uploaded PDF including ID and blob URLs
    """
    # Load environment variables
    load_dotenv()
    
    # Get Azure Storage connection string and container name from environment variables
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        print("Error: Azure Storage connection string or container name not found in .env file")
        print("Please ensure AZURE_STORAGE_CONNECTION_STRING and BLOB_CONTAINER_NAME are set")
        return None
    
    # Generate a unique ID for this upload
    upload_id = str(uuid.uuid4())
    
    # Use provided filename or extract from path
    if not filename:
        filename = os.path.basename(pdf_path)
    
    try:
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        print(f"Processing PDF: {filename}")
        
        # Load and process the PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        print(f"Loaded {len(documents)} pages from PDF")
        
        # Split the documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Created {len(chunks)} text chunks")
        
        # Create embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create FAISS index
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save the FAISS index locally in the temp directory
        faiss_dir = os.path.join(temp_dir, "faiss_index")
        vector_store.save_local(faiss_dir)
        
        print(f"Created FAISS index in {faiss_dir}")
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Check if container exists, if not create it
        if not container_client.exists():
            print(f"Container {container_name} does not exist. Creating...")
            container_client = blob_service_client.create_container(container_name)
        
        # Upload the PDF file
        pdf_blob_name = f"pdfs/{upload_id}/{filename}"
        with open(pdf_path, "rb") as data:
            blob_client = container_client.upload_blob(
                name=pdf_blob_name,
                data=data,
                overwrite=True
            )
        
        print(f"Uploaded PDF to {pdf_blob_name}")
        
        # Upload FAISS index files
        faiss_blobs = []
        for file_name in os.listdir(faiss_dir):
            file_path = os.path.join(faiss_dir, file_name)
            blob_name = f"pdfs/{upload_id}/faiss_index/{file_name}"
            
            with open(file_path, "rb") as data:
                blob_client = container_client.upload_blob(
                    name=blob_name,
                    data=data,
                    overwrite=True
                )
            
            faiss_blobs.append(blob_name)
        
        print(f"Uploaded FAISS index files: {', '.join(os.listdir(faiss_dir))}")
        
        # Create metadata file with information about the PDF
        metadata = {
            "id": upload_id,
            "filename": filename,
            "page_count": len(documents),
            "chunk_count": len(chunks),
            "pdf_blob": pdf_blob_name,
            "faiss_blobs": faiss_blobs
        }
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        print(f"Successfully processed and uploaded PDF with ID: {upload_id}")
        return metadata
        
    except Exception as e:
        print(f"Error processing and uploading PDF: {str(e)}")
        # Clean up temporary directory if it exists
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        return None

def upload_directory_pdfs(directory_path):
    """
    Process all PDFs in a directory and upload them to Azure Blob Storage
    
    Args:
        directory_path: Path to directory containing PDFs
        
    Returns:
        list: Information about all uploaded PDFs
    """
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory")
        return []
    
    results = []
    
    # Find all PDF files in the directory
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return []
    
    print(f"Found {len(pdf_files)} PDF files in {directory_path}")
    
    # Process each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        result = process_and_upload_pdf(pdf_path)
        
        if result:
            results.append(result)
    
    print(f"Successfully processed and uploaded {len(results)} out of {len(pdf_files)} PDFs")
    return results

def download_faiss_index(upload_id):
    """
    Download a FAISS index from Azure Blob Storage
    
    Args:
        upload_id: ID of the uploaded PDF
        
    Returns:
        str: Path to the downloaded FAISS index directory
    """
    # Load environment variables
    load_dotenv()
    
    # Get Azure Storage connection string and container name from environment variables
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        print("Error: Azure Storage connection string or container name not found in .env file")
        return None
    
    try:
        # Create a temporary directory for downloading
        temp_dir = tempfile.mkdtemp()
        faiss_dir = os.path.join(temp_dir, "faiss_index")
        os.makedirs(faiss_dir, exist_ok=True)
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Download FAISS index files
        blobs = container_client.list_blobs(name_starts_with=f"pdfs/{upload_id}/faiss_index/")
        
        for blob in blobs:
            file_name = os.path.basename(blob.name)
            file_path = os.path.join(faiss_dir, file_name)
            
            with open(file_path, "wb") as download_file:
                download_file.write(container_client.download_blob(blob.name).readall())
        
        print(f"Downloaded FAISS index for upload ID: {upload_id}")
        return faiss_dir
        
    except Exception as e:
        print(f"Error downloading FAISS index: {str(e)}")
        # Clean up temporary directory if it exists
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        return None

def list_uploaded_pdfs():
    """
    List all PDFs uploaded to Azure Blob Storage
    
    Returns:
        list: Information about all uploaded PDFs
    """
    # Load environment variables
    load_dotenv()
    
    # Get Azure Storage connection string and container name from environment variables
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        print("Error: Azure Storage connection string or container name not found in .env file")
        return []
    
    try:
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Get all PDF directories
        pdf_ids = set()
        blobs = container_client.list_blobs(name_starts_with="pdfs/")
        
        for blob in blobs:
            # Extract PDF ID from path (pdfs/{pdf_id}/...)
            parts = blob.name.split('/')
            if len(parts) >= 2:
                pdf_ids.add(parts[1])
        
        # Get information for each PDF
        pdfs = []
        for pdf_id in pdf_ids:
            # Find the PDF file
            pdf_blobs = list(container_client.list_blobs(name_starts_with=f"pdfs/{pdf_id}/"))
            pdf_files = [blob for blob in pdf_blobs if not blob.name.startswith(f"pdfs/{pdf_id}/faiss_index/")]
            
            if pdf_files:
                # Get the filename
                filename = os.path.basename(pdf_files[0].name)
                
                # Check if FAISS index exists
                faiss_blobs = list(container_client.list_blobs(name_starts_with=f"pdfs/{pdf_id}/faiss_index/"))
                has_faiss = len(faiss_blobs) > 0
                
                pdfs.append({
                    "id": pdf_id,
                    "filename": filename,
                    "has_faiss_index": has_faiss
                })
        
        return pdfs
        
    except Exception as e:
        print(f"Error listing PDFs: {str(e)}")
        return []

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upload_faiss_to_blob.py <command> [args]")
        print("Commands:")
        print("  upload <pdf_path> - Process and upload a single PDF")
        print("  upload_dir <directory_path> - Process and upload all PDFs in a directory")
        print("  list - List all uploaded PDFs")
        print("  download <upload_id> - Download a FAISS index")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "upload" and len(sys.argv) >= 3:
        pdf_path = sys.argv[2]
        result = process_and_upload_pdf(pdf_path)
        if result:
            print(f"Successfully uploaded PDF with ID: {result['id']}")
    
    elif command == "upload_dir" and len(sys.argv) >= 3:
        directory_path = sys.argv[2]
        results = upload_directory_pdfs(directory_path)
        print(f"Uploaded {len(results)} PDFs")
    
    elif command == "list":
        pdfs = list_uploaded_pdfs()
        print(f"Found {len(pdfs)} uploaded PDFs:")
        for pdf in pdfs:
            print(f"  {pdf['id']} - {pdf['filename']} (FAISS index: {'Yes' if pdf['has_faiss_index'] else 'No'})")
    
    elif command == "download" and len(sys.argv) >= 3:
        upload_id = sys.argv[2]
        faiss_dir = download_faiss_index(upload_id)
        if faiss_dir:
            print(f"Downloaded FAISS index to {faiss_dir}")
    
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)