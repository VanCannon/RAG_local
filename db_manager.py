# db_manager.py

import os
import glob
import getpass
from dotenv import load_dotenv
from typing import List

# We use the langchain_community library for document loading and text splitting.
# PyPDFLoader is for .pdf files.
# UnstructuredWordDocumentLoader is for .docx files (requires the `unstructured` library).
# TextLoader is for .txt files.
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Note: For .docx files, you may need to install the 'unstructured' library.
# To do so, run the following command:
# pip install "unstructured[local-inference]"

# --- Configuration ---
# Load environment variables from the .env file.
# This is a secure way to manage your API key.
load_dotenv()

# Check if the API key is set.
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    # If not in .env, prompt the user for it securely.
    google_api_key = getpass.getpass("Enter your Google API Key: ")
    os.environ["GOOGLE_API_KEY"] = google_api_key

# Define the file paths and model names.
DOCS_DIRECTORY = "docs"
CHROMA_DB_DIRECTORY = "chroma_db"
EMBEDDING_MODEL_NAME = "models/embedding-001"

# --- Helper Functions ---

def get_loader(file_path: str):
    """
    Returns the appropriate LangChain document loader based on the file extension.
    """
    extension = os.path.splitext(file_path)[1].lower()
    
    if extension == ".pdf":
        return PyPDFLoader(file_path)
    elif extension == ".docx":
        # UnstructuredWordDocumentLoader handles both .doc and .docx files.
        return UnstructuredWordDocumentLoader(file_path)
    elif extension == ".txt":
        return TextLoader(file_path)
    else:
        print(f"Warning: No loader found for file type '{extension}'. Skipping '{file_path}'.")
        return None

# --- Core Functions ---

def get_db_and_docs_from_disk():
    """
    Initializes or loads a persistent ChromaDB instance and returns it along
    with a list of all documents in the database.
    """
    print("1. Initializing Gemini embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL_NAME)

    # Check if the ChromaDB directory already exists.
    if not os.path.exists(CHROMA_DB_DIRECTORY):
        print("    -> ChromaDB directory not found. Creating a new database...")
        # If the directory doesn't exist, we start with an empty vector store
        # and create the persistence directory.
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIRECTORY
        )
        return vector_store, []
    else:
        print("    -> ChromaDB directory found. Loading existing database...")
        # If the directory exists, we load the database from disk.
        vector_store = Chroma(
            persist_directory=CHROMA_DB_DIRECTORY,
            embedding_function=embeddings
        )
        # Retrieve all documents currently in the database to compare with the file system.
        db_docs_with_ids = vector_store.get(include=['metadatas'])
        db_docs = db_docs_with_ids['metadatas']
        print(f"    -> Found {len(db_docs)} document chunks in the database.")
        return vector_store, db_docs

def add_new_documents(vector_store, new_docs_paths: List[str]):
    """
    Loads, splits, and adds new documents to the ChromaDB.
    This function now supports multiple file types using get_loader().
    """
    if not new_docs_paths:
        print("   -> No new documents to add.")
        return

    print(f"\n2. Found {len(new_docs_paths)} new documents to process:")
    for doc_path in new_docs_paths:
        print(f"   - Processing: {doc_path}")
        
        # Get the appropriate loader for the file type.
        loader = get_loader(doc_path)
        
        if not loader:
            continue
            
        try:
            # Load the document using the selected loader.
            documents = loader.load()
            
            # Use a text splitter to break the document into manageable chunks.
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                is_separator_regex=False,
            )
            chunks = text_splitter.split_documents(documents)
            
            # Add the original file path to each chunk's metadata. This is crucial
            # for later tracking and deletion.
            for chunk in chunks:
                chunk.metadata['source'] = doc_path
            
            print(f"     -> Split into {len(chunks)} chunks. Adding to database...")
            # Add the new documents to the vector store.
            vector_store.add_documents(chunks)
            print("     -> Done.")
        except Exception as e:
            print(f"     -> Error processing {doc_path}: {e}")

def remove_deleted_documents(vector_store, documents_to_delete_paths: List[str]):
    """
    Removes documents from the ChromaDB that no longer exist in the file system.
    """
    if not documents_to_delete_paths:
        print("   -> No documents to remove.")
        return

    print(f"\n3. Found {len(documents_to_delete_paths)} documents to remove from the database:")
    
    # Retrieve all documents in the database to get their IDs.
    db_docs = vector_store.get(include=['metadatas'])
    
    # Get a list of all IDs for documents that need to be deleted.
    ids_to_delete = []
    for doc_path in documents_to_delete_paths:
        print(f"   - Deleting embeddings for: {doc_path}")
        for i, metadata in enumerate(db_docs['metadatas']):
            if metadata.get('source') == doc_path:
                ids_to_delete.append(db_docs['ids'][i])
    
    # Perform the deletion if any IDs were found.
    if ids_to_delete:
        vector_store.delete(ids=ids_to_delete)
        print(f"     -> Deleted {len(ids_to_delete)} chunks.")
    print("   -> Done.")

def sync_vector_db():
    """
    Compares the files in the docs directory with the documents in the ChromaDB
    and updates the database accordingly.
    """
    # Get the current list of files in the docs directory.
    current_docs_paths = glob.glob(os.path.join(DOCS_DIRECTORY, "*.[pP][dD][fF]"))
    current_docs_paths.extend(glob.glob(os.path.join(DOCS_DIRECTORY, "*.[dD][oO][cC][xX]")))
    current_docs_paths.extend(glob.glob(os.path.join(DOCS_DIRECTORY, "*.[tT][xX][tT]")))
    
    # Get the existing database and its documents.
    vector_store, db_docs = get_db_and_docs_from_disk()

    # Create a set of all document paths currently in the database.
    db_doc_paths = set(metadata.get('source') for metadata in db_docs)
    
    # Find new documents to add.
    new_docs_paths = [path for path in current_docs_paths if path not in db_doc_paths]
    
    # Find documents to delete.
    current_docs_set = set(current_docs_paths)
    documents_to_delete_paths = [path for path in db_doc_paths if path not in current_docs_set]

    # Add new documents to the database.
    add_new_documents(vector_store, new_docs_paths)
    
    # Remove old documents from the database.
    remove_deleted_documents(vector_store, documents_to_delete_paths)
    
    print("\n--- Database sync complete. ---")

# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(DOCS_DIRECTORY):
        print(f"Error: The '{DOCS_DIRECTORY}' directory was not found.")
        print("Please create this folder and add your documents before running this script.")
    else:
        sync_vector_db()
