# Import a text splitter that recursively splits long texts into manageable chunks.
# Useful for preparing documents before embedding or processing with LLMs.
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import the Document schema used to define structured document objects in LangChain.
from langchain.schema import Document

# Import the Chroma vector store interface from LangChain's integration.
from langchain_chroma import Chroma

# Import HuggingFace embeddings wrapper to convert text into vector embeddings.
from langchain_huggingface import HuggingFaceEmbeddings

# Built-in Python modules for operating system interaction and file operations.
import sys

# Import Path for convenient file path handling (object-oriented interface).
from pathlib import Path

# PyMuPDF wrapper for LLMs (Apackage that allows extracting or formatting PDF data for use with LLMs).
import pymupdf4llm

# Progress bar utility for long-running loops with live terminal updates.
import alive_progress

import re

#Creates a vector database with Chroma for querying its documents.

CHROMA_PATH = "databases/chroma"
INPUT_FOLDER="databases/pdfbooksarticles"
PROCESSED_FILES_ARCHIVE="processedfiles.txt"
def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

def remove_processed_files(pdf_files):
    
    archive_path = Path(PROCESSED_FILES_ARCHIVE)

    if not archive_path.exists():
        archive_path.write_text("", encoding="utf-8")  # create empty file
        
    with open(PROCESSED_FILES_ARCHIVE, "r", encoding="utf-8") as file:
        processed_filenames = [line.strip().replace("\\", "/") for line in file]

    # Remove processed files
    remaining_pdf_files = [f for f in pdf_files if f.as_posix() not in processed_filenames]
    return remaining_pdf_files
    

def add_processed_files(pdf_files):
    with open(PROCESSED_FILES_ARCHIVE, "a", encoding="utf-8") as file:
        for pdf in pdf_files:
            file.write(f"{pdf}\n")  
    
def load_documents():
    #Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    pdf_files = list(Path(INPUT_FOLDER).glob("*.pdf"))
    
    pdf_files=remove_processed_files(pdf_files)
    
    add_processed_files(pdf_files)
    
    total_files=len(pdf_files)
    
    if( total_files==0):
        print("There are no new archives to process.")
        sys.exit(0)

    all_documents = []

    with alive_progress.alive_bar(total_files, title="📄 Converting PDFs", bar="classic") as bar:
        for file_path in pdf_files:
            try:
                # Extract per-page Markdown chunks with metadata
                pages = pymupdf4llm.to_markdown(
                    str(file_path),
                    page_chunks=True,
                    ignore_images=True,
                    ignore_graphics=True,
                    force_text=True,
                )

                # Convert each page into a LangChain Document
                for page in pages:
                    content = page["text"]
                    metadata = page["metadata"]
                    metadata["file_path"] = str(file_path)  #For traceability
                    metadata["source"] = f"{file_path.stem}"  # The name of the doucument

                    doc = Document(page_content=content, metadata=metadata)
                    all_documents.append(doc)

                bar()

            except Exception as e:
                print(f"\n⚠️ Failed to convert {file_path.name}: {str(e)}")
                continue

    print(f"\n✅ Processed {total_files} PDFs -> {len(all_documents)} pages as documents")
    return all_documents



def split_text(documents: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=180,
        length_function=len,
        add_start_index=True,
        # Try to split first by sentence-ending punctuation, then fallback to spaces, then characters
        separators=[".","!", "?"]
    )

    chunks = text_splitter.split_documents(documents)
    
    # Filter out short chunks
    min_length = 50  
    filtered_chunks = [chunk for chunk in chunks if len(chunk.page_content.strip()) >= min_length]

    for i, chunk in enumerate(filtered_chunks):
        # Clean the text: replace newlines with space and strip extra spaces
        clean_text = re.sub(r'\n', ' ', chunk.page_content)
        chunk.page_content = clean_text
        chunk.metadata["chunk_index"] = i
        # Ensure page_number and file_path metadata are present
        if "page_number" not in chunk.metadata:
            chunk.metadata["page_number"] = i + 1
        if "file_path" not in chunk.metadata:
            chunk.metadata["file_path"] = "unknown"

    print(f"✅ Split {len(documents)} pages into {len(filtered_chunks)} text chunks.")
    return filtered_chunks


def save_to_chroma(chunks: list[Document]):
    
    # Initialize Chroma
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Track embedding generation 
    print("🔧 Generating embeddings...")
    with alive_progress.alive_bar(len(chunks), title="Embedding chunks", bar="smooth", spinner="dots_waves") as bar:
        # Wrap embedding generation in progress bar
        embeddings_with_progress = []
        for chunk in chunks:
            embedding = embeddings.embed_documents([chunk.page_content])[0]
            embeddings_with_progress.append(embedding)
            bar()
            
            
    print("💾 Saving to Chroma...")
    with alive_progress.alive_bar(1, title="Persisting database", spinner="dots") as bar:
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings, 
            persist_directory=CHROMA_PATH
        )
        bar()
        
    print(f"✅ Saved {len(chunks)} chunks using HuggingFace embeddings")

if __name__ == "__main__":
    main()