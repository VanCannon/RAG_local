# RAG_local
Put pdf, docx, and txt files in a local folder on your computer for use in a Gemini RAG. It is easy to upload a small number of documents to the Gemini web interface, but if you wnat to query a lot of documents and/or run several queries over time with a given set of documents, this approach is easier once you set it up.

There are two scripts, db_manager.py and query_rag.py

The first script. creates a ChromaDB the first time it is run, converts the files to vectors and then saves them to the ChromaDB. It must be run anytime new files are added or old ones deleted to update the database.

The second script does the "Retrival-Augemtnetd Generation'. It inputs your quesiton and number of "chunks" you want to use, then converts the query into a vector.  It then queries the ChromaDB for the closest chunks to the query and sends them to Gemini's API for a response.

### Disclaimer
I only "vibe code" and in this case used Gemini, so this code could connect to China and upload every file on your computer as far as I know.

# Setup
This was all done on Ubuntu desktop with VScode, but any editor and problaby even just a terminal would work.

1. Ensure Python3 and pip are installed  
`sudo apt update`  
`sudo apt python3 python3-pip`

2. Create a project folder and clone the repository (Could skip creating the folder and do git clone... but it would keep the repository name.)  
`mkdir RAG_example`  
`cd RAG_example`  
`git pull https://github.com/VanCannon/RAG_local.git`

3. Create a virtual python environment and download all the dependencies listed in the requirements file.  
`python3 -m venv .venv`  
`source .venv/bin/activate`  
`pip install -r requirements.txt`

4. Get your Gemini API key [here](https://makersuite.google.com/app/apikey)  
Edit the .env file and replace "api key" with the actual key (no quotes).

5. Create a docs folder and then put the reference documents in it.  They can be .pdf, .docx, or .txt  
`mkdir docs`

6. Run the db_manager script  
`python3 db_manager.py`

7. Run the query_rag script  
`python3 query_rag.py`




