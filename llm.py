# Used to store and search vectorized documents.
from langchain_chroma import Chroma

# Import HuggingFace embeddings wrapper for text embedding generation.
from langchain_huggingface import HuggingFaceEmbeddings

# Import ChatPromptTemplate to format prompts for LLM-based chat interactions.
from langchain.prompts import ChatPromptTemplate

# Built-in Python module for sending HTTP requests (used for API communication).
import requests

# Built-in Python module for handling JSON data (parse, generate, etc.).
import json

# Built-in module for interacting with the operating system (file paths, env vars).
import os

# Load environment variables from a .env file into the runtime environment.
from dotenv import load_dotenv

from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

load_dotenv()

messages = []

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
You are a knowledgeable assistant. Use only the information provided in the following context to answer the question. 
Do not use any outside knowledge. Respond in the same language as the input.

Context:
{context}

---

Question:
{question}

---

Instructions:
- Answer concisely and directly using only essential information from the context.
- Do not repeat the question.
- Do not include any information not explicitly present in the context.
- If the context does not contain enough information, respond with: "The context does not provide enough information to answer the question."

"""

def is_same_context(previous_messages, new_query, threshold=0.7):
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    previous_text = "\n".join([msg["content"] for msg in previous_messages if msg["role"] == "user"])
    
    # Get embeddings
    prev_embedding = embedding_function.embed_query(previous_text)
    new_embedding = embedding_function.embed_query(new_query)
    
    
    prev_embedding=normalize(prev_embedding)
    new_embedding=normalize(new_embedding)
    
    # Calculate similarity
    similarity = cosine_similarity([prev_embedding], [new_embedding])[0][0]
    
    return similarity > threshold

def normalize(vec):
    return vec / np.linalg.norm(vec)  # Divide vector by its magnitude

def main():
 
    query_text =  input("\n\nEnter your query: ")
    
    if( not query_text.strip()):
        return

    # Prepare the DB.
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
   
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

   # print("db count:",db._collection.count())  # Should return > 0
    
    merged_query_text="\n".join([msg["content"] for msg in messages if msg["role"]=="user"])+"\n"+query_text     #Wrap the previously made queries to the context
    if not is_same_context(messages,query_text):   
        merged_query_text=query_text
        messages.clear()
        print("Context history cleared - new topic detected.")
        
    
    # Search the DB.
    results = db.similarity_search_with_relevance_scores(merged_query_text, k=3)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
       
    },
    data=json.dumps({
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": messages,
    })
    )
    
    output =  response.json()
    response_text = output['choices'][0]['message']['content']
    
    
    messages.append({
        "role": "assistant",
        "content": response_text
    })
    
    if(len(messages)==6):
        del messages[:2]  #Only preserves the last 4 messages
    

    sources_pages = [(doc.page_content.replace("\n"," ").strip(),doc.metadata.get("source", None), doc.metadata.get("page", None)) for doc, _score in results]
    formatted_response = f"Response: {response_text}\n"
    print(formatted_response)
    for page_content,source, page in sources_pages:
        print(f"🧾 Content: {page_content or 'Unknown'} |📄 Source: {source or 'Unknown'} | 📘 Page: {page if page is not None else 'N/A'}")

if __name__ == "__main__":
    while(True):
        main()
        