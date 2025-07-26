
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from utils.utils import call_openrouter_api, display_content_llm
from utils.highlightviewpdf import highlight_and_view_pdf
import os
import sys
sys.path.append("rag/")
from utils.prompt import const



CHROMA_PATH = "databases/chroma"  
MODEL_NAME = "all-MiniLM-L6-v2"


# Initialize embeddings and vector store once
@st.cache_resource(show_spinner=False)
def init_knowledge_base():
    embedding_fn = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    chroma_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_fn)
    return embedding_fn, chroma_db





embedding_fn, chroma_db = init_knowledge_base()


def normalize(vec):
    return vec / np.linalg.norm(vec)


def is_same_context(previous_messages, new_query, threshold=0.7):
    previous_text = "\n".join(msg["content"] for msg in previous_messages if msg["role"] == "user")
    if not previous_text.strip():
        return False

    prev_emb = normalize(embedding_fn.embed_query(previous_text))
    new_emb = normalize(embedding_fn.embed_query(new_query))
    similarity = cosine_similarity([prev_emb], [new_emb])[0][0]
    return similarity > threshold


def get_chat_history():
    """Get user-only messages as a merged query string."""
    user_msgs = [m for m in st.session_state.kb_messages if m["role"] == "user"]
    return "\n".join(m["content"] for m in user_msgs), user_msgs

def build_sources_chroma(results):
    """Format retrieved sources nicely."""
    return [
        {
            "content": doc.page_content.replace("\n", " ").strip(),
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "N/A")
        }
        for doc, _ in results
    ]

def build_response_content(sources):
    """Format chroma's answer for display."""
    #if 'pdf_clicked' not in st.session_state:
    #  st.session_state.pdf_clicked = None
   

    content = []
    for src in sources:
        group = [
            {"type": "annotation", "text": "Quote", "note": src['content']},
            {"type": "annotation", "text": "📄 Source", "note": src['source']},
            {"type": "annotation", "text": "📘 Page", "note": src['page']},
           # {"type": "annotation", "text": "📘 Page", "note": st.link_button(f"Open reading on {src['page']}",highlight_and_view_pdf(input_path=f"databases/pdfbooksarticles/{src['source']}.pdf",search_text=src['content'],page_num=int(src['page'])) )},
            {"type": "paragraph", "text": ""}
        ]
        content.append(group)
    return content

def render_knowledge_base_mode():
    st.info("💬 Chat with the Knowledge Base")
    
    # Initialize session state variables
    if "pdf_to_open" not in st.session_state:
        st.session_state.pdf_to_open = {}
    if "kb_messages" not in st.session_state:
        st.session_state.kb_messages = []
    if "buttons_citations" not in st.session_state:
        st.session_state.buttons_citations = []

    # Handle PDF viewer FIRST (before displaying messages)
    if st.session_state.pdf_to_open:
        pdf_info = st.session_state.pdf_to_open
        try:
            

            highlight_and_view_pdf(
                input_path=pdf_info['input_path'],
                search_text=pdf_info['search_text'],
                page_num=pdf_info['page_num']
            )
        except Exception as e:
            st.error(f"Error opening PDF: {str(e)}")
        finally:
            st.session_state.pdf_to_open = {}
            st.rerun()

    # Show ALL chat history - this recreates the entire interface after rerun
    for msg_idx, msg in enumerate(st.session_state.kb_messages):
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:  # assistant message
                # Use display_content_llm for ALL assistant messages (including sources)
                if isinstance(msg["content"], list):
                    display_content_llm({"content": msg["content"]})
                elif isinstance(msg["content"], dict):
                    display_content_llm(msg["content"])
                else:
                    # Handle string content
                    st.markdown(msg["content"])
                
                # Recreate buttons for source messages that have source_info
                if "source_info" in msg:
                    source_info = msg["source_info"]
                    pdf_path = f"databases/pdfbooksarticles/{source_info['filename']}.pdf"
                    
                    # Use the stored button key to ensure consistency
                    btn_key = source_info["btn_key"]
                    
                    if os.path.exists(pdf_path):
                        # Create button with unique key and check its state directly
                        button_clicked = st.button(
                            f"🔍 View PDF (Page {source_info['page_num']})", 
                            key=btn_key
                        )
                        
                        if button_clicked:
                            st.session_state.pdf_to_open = {
                                "input_path": pdf_path,
                                "search_text": source_info['search_text'],
                                "page_num": source_info['page_num']  # Use the specific page from this source
                            }
                            st.rerun()
                    else:
                        st.markdown(f"**PDF not found:** {pdf_path}")

    # Process new user input
    if prompt := st.chat_input("Ask the knowledge base..."):
        # Add user message to history
        st.session_state.kb_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Merge past user messages + new prompt for context
            merged_query, user_msgs = get_chat_history()
            merged_query += "\n" + prompt

            # If new topic detected → clear context
            if not is_same_context(user_msgs, prompt):
                merged_query = prompt
                st.session_state.kb_messages = [m for m in st.session_state.kb_messages if m["role"] != "user"]
                st.session_state.buttons_citations = []
                st.info("Context history cleared - new topic detected.")

            # Retrieve top 3 most relevant docs from Chroma
            results = chroma_db.similarity_search_with_relevance_scores(merged_query, k=3)
            context_text = "\n\n---\n\n".join(doc.page_content for doc, _ in results)

            # Build prompt for the LLM
            formatted_prompt = ChatPromptTemplate.from_template(const.PROMPT_TEMPLATE_KNOWLEDGE_BASE).format(
                context=context_text, question=prompt
            )

            # Show loading animation
            placeholder = st.empty()
            with placeholder.container():
                st.image("https://media.tenor.com/FawYo00tBekAAAAM/loading-thinking.gif", width=30)

            # Get response from LLM
            response_text = call_openrouter_api(prompt=formatted_prompt)
            placeholder.empty()

            # Show and store LLM response
            with st.chat_message("assistant"):
                display_content_llm(response_text)
            st.session_state.kb_messages.append({"role": "assistant", "content": response_text})

            # Build source cards to show
            sources = build_sources_chroma(results)
            if not sources:
                st.markdown("**No sources found for this query.**")
                return

            # Show highlighted title and store it
            highlight_content = [{"type": "highlight", "text": "Key context sources:"}]
            with st.chat_message("assistant"):
                display_content_llm({"content": highlight_content})
            st.session_state.kb_messages.append({"role": "assistant", "content": highlight_content})

            # Process and display each source
            source_content = build_response_content(sources)
            for idx, source in enumerate(source_content):
                
                # Extract info for PDF button BEFORE displaying
                source_info_item = next((i for i in source if i["type"] == "annotation" and i["text"] == "📄 Source"), None)
                page_info_item = next((i for i in source if i["type"] == "annotation" and i["text"] == "📘 Page"), None)
                content_info_item = next((i for i in source if i["type"] == "annotation" and i["text"] == "Quote"), None)

                # Display the source using display_content_llm (same as original interface)
                with st.chat_message("assistant"):
                    display_content_llm({"content": source})
                    
                    # Create and display button immediately after source display
                    if source_info_item and page_info_item and content_info_item:
                        try:
                            page_num = int(page_info_item['note'])
                        except (ValueError, TypeError):
                            page_num = 1

                        pdf_path = f"databases/pdfbooksarticles/{source_info_item['note']}.pdf"
                        
                        # Create unique button key for this specific source and page
                        current_msg_count = len(st.session_state.kb_messages)
                        btn_key = f"pdf_{source_info_item['note']}_{page_num}_{idx}_{current_msg_count}"

                        if os.path.exists(pdf_path):
                            if st.button(f"🔍 View PDF (Page {page_num})", key=btn_key):
                                st.session_state.pdf_to_open = {
                                    "input_path": pdf_path,
                                    "search_text": content_info_item['note'],  # Specific search text for this source
                                    "page_num": page_num  # Specific page number for this source
                                }
                                st.rerun()
                        else:
                            st.markdown(f"**PDF not found:** {pdf_path}")

                # Prepare message to store with source info for rerun recreation
                message_to_store = {
                    "role": "assistant", 
                    "content": source
                }

                # Store source info with the message for rerun recreation
                if source_info_item and page_info_item and content_info_item:
                    try:
                        page_num = int(page_info_item['note'])
                    except (ValueError, TypeError):
                        page_num = 1
                    
                    current_msg_count = len(st.session_state.kb_messages)
                    btn_key = f"pdf_{source_info_item['note']}_{page_num}_{idx}_{current_msg_count}"

                    message_to_store["source_info"] = {
                        "filename": source_info_item['note'],
                        "page_num": page_num,
                        "search_text": content_info_item['note'],
                        "btn_key": btn_key
                    }

                # Store the message with source info
                st.session_state.kb_messages.append(message_to_store)

        except Exception as e:
            st.error(f"An error occurred while processing your request: {str(e)}")
            # Add error message to chat history
            st.session_state.kb_messages.append({
                "role": "assistant", 
                "content": f"Sorry, I encountered an error: {str(e)}"
            })

        finally:
            # Keep only last 10 messages for memory management
            if len(st.session_state.kb_messages) > 10:
                st.session_state.kb_messages = st.session_state.kb_messages[-10:]