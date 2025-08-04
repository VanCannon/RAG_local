# query_rag.py

import os
import getpass
from dotenv import load_dotenv

# We use the langchain_community library for document loading, embeddings, and vector stores.
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA

# --- Configuration ---
# Load environment variables from the .env file.
load_dotenv()

# Check if the API key is set.
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    # If not in .env, prompt the user for it securely.
    google_api_key = getpass.getpass("Enter your Google API Key: ")
    os.environ["GOOGLE_API_KEY"] = google_api_key

# Define the file paths and model names.
CHROMA_DB_DIRECTORY = "chroma_db"
EMBEDDING_MODEL_NAME = "models/embedding-001"
GENERATION_MODEL_NAME = "models/gemini-2.5-flash"


# --- Core Functions ---

def load_vector_store():
    """
    Loads the persistent ChromaDB from disk using the specified directory.
    """
    try:
        print("1. Initializing Gemini embeddings...")
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL_NAME)

        print("2. Loading vector store from disk...")
        # Load the existing database using the same persistence directory.
        vector_store = Chroma(
            persist_directory=CHROMA_DB_DIRECTORY,
            embedding_function=embeddings
        )
        print("   -> Vector store successfully loaded!")
        return vector_store
    
    except Exception as e:
        print(f"Error: Could not load the vector store. Have you run 'db_manager.py' yet?")
        print(f"Reason: {e}")
        return None


def ask_question_with_rag(query: str, vector_store, k_chunks: int = 4):
    """
    Performs a RAG process:
    1. Retrieves relevant documents from the vector store.
    2. Constructs a prompt with the query and the retrieved documents.
    3. Uses a Gemini model to generate a final answer.
    """
    if not vector_store:
        return "Cannot proceed without a valid vector store."
        
    print("\n--- RAG Process Starting ---")
    print(f"User Question: '{query}'")
    print(f"Retrieving top {k_chunks} relevant chunks...")

    # Configure the retriever to use the vector store and return a specific number of chunks (k).
    retriever = vector_store.as_retriever(search_kwargs={"k": k_chunks})

    # Initialize the Gemini model for content generation.
    llm = GoogleGenerativeAI(model=GENERATION_MODEL_NAME)

    # Use LangChain's RetrievalQA chain to combine the retrieval and generation steps.
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    print("Generating response with Gemini...")
    result = qa_chain.invoke({"query": query})
    
    answer = result.get("result")
    
    print("\n--- Gemini's Answer ---")
    return answer

# --- Main Execution ---
if __name__ == "__main__":
    # Load the vector store from your document.
    vector_store = load_vector_store()
    
    if vector_store:
        while True:
            # Get user input for the question and number of chunks.
            user_question = input("\nEnter your question (or 'exit' to quit): ")
            if user_question.lower() == 'exit':
                break
            
            try:
                num_chunks = int(input("How many chunks should be included in the context (e.g., 2, 4, 6): "))
            except ValueError:
                print("Invalid input. Using default of 4 chunks.")
                num_chunks = 4

            # Run the RAG process and print the answer.
            answer = ask_question_with_rag(user_question, vector_store, k_chunks=num_chunks)
            print(answer)

    print("\nScript finished.")
