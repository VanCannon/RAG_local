# RAG_local
Put pdf, docx, and txt files in a local folder on your computer for use in a Gemini RAG. It is easy to upload a small number of documents to the Gemini web interface, but if you want to query a lot of documents and/or run several queries over time with a given set of documents, this approach is easier once you set it up.

There are two scripts, db_manager.py and query_rag.py

The first script creates a ChromaDB the first time it is run, converts the files to vectors and then saves them to the ChromaDB. It must be run anytime new files are added or old ones deleted to update the database.

The second script does the "Retrival-Augmented Generation'. It inputs your question and number of "chunks" you want to use, then converts the query into a vector.  It then queries the ChromaDB for the closest chunks to the query and sends them to Gemini's API for a response.

### Disclaimer
I only "vibe code" and in this case used Gemini, so this code could install ridiculus malware as far as I know.

# Setup
This was all done on Ubuntu desktop with a terminal in VScode, but just a terminal in any Debian-based Linux would work as well.

1. Ensure Python3, pip and git are installed  
`sudo apt update`  
`sudo apt python3 python3-pip git`  
`git config --global init.defaultBranch main`
 (Only if you want the initial branch of all future local repositories to be called "main" which lines up with Github and makes things easier. Otherwise it defaults to "Master". Only need to do this the first time.)  

3. Create a project folder and clone the repository  
```bash
git clone https://github.com/VanCannon/RAG_local.git myProjectName
cd myProjectName
# --OR--
mkdir myProjectName
cd myProjectName
git clone https://github.com/VanCannon/RAG_local.git .
```  


3. Create a virtual python environment and download all the dependencies listed in the requirements file.  
`python3 -m venv .venv`  
`source .venv/bin/activate`  
(The command line will start with ".venv" if active)  
`pip install -r requirements.txt`

5. Get your Gemini API key [here](https://makersuite.google.com/app/apikey)
(Requires a Google account, which you have if you have gmail.)
Edit the .env file and replace "api key" with the actual key (no quotes).

6. Create a docs folder and then put the reference documents in it.  They can be .pdf, .docx, or .txt  
`mkdir docs`

7. Run the db_manager script  
`python3 db_manager.py`

8. Run the query_rag script  
`python3 query_rag.py`  

### Misc notes  
When starting a new session, the terminal might not start in the virtual mode, so you need to activate it again. 
`source .venv/bin/activate`  
(The command line will start with ".venv" if active) 

Use `deactivate` to get out of the virtual environment.  

I was not sure how to choose the number of chunks to use. It helps to understand chunks in the first place. The text has to be broken up into mangeable pieces, or "chunks" and typical size in characters is 200 to 1500. "Overlap" means how much of corresponding chunks have the same data to prevent loss of context. This is typically 10-20% of the size. The defaults in the db_manger.py script is 1000/200.  1000 charaters is very roughly about 1/2 a page of single-spaced text.

If you want to modify them, you can find them in this spot in the db_manager script:  
```            # Use a text splitter to break the document into manageable chunks.
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                is_separator_regex=False,
            )
            chunks = text_splitter.split_documents(documents)
```

If you change these and have already run the script once on existing documents, then you would have to remove the documents from the docs file, run the script to remove the old chunks, and then put the documents back and run the script again to parse them with the new chunk sizes.
