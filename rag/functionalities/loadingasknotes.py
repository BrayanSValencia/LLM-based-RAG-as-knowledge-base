import streamlit as st

from langchain.prompts import ChatPromptTemplate
import json
import time

import sys
sys.path.append("rag/")
from utils.utils import  display_content, json_to_text_flat,display_content_llm,call_openrouter_api
from utils.prompt import const


def last_query_validation():
    if "last_query_time" not in st.session_state:
        st.session_state.last_query_time = 0
        
    current_time = time.time()
    if current_time - st.session_state.last_query_time < 2:
        st.warning("Please wait a moment before sending another query")
        return None
    st.session_state.last_query_time = current_time

def ask_about_notes(query_text, notes):
    
    last_query_validation()
 
    prompt_template = ChatPromptTemplate.from_template(const.PROMPT_TEMPLATE_LOADING_ASK_NOTES)
    
    format_notes=""
    if isinstance(notes, dict):
        format_notes = json.dumps(notes,indent=2).strip().replace("'","")  # Convert dict → JSON string
        
    prompt = prompt_template.format(context=format_notes, question=query_text)
    
    st.session_state.loaded_notes_messages.append({"role": "user", "content": prompt})
    
    messages= st.session_state.loaded_notes_messages[:]
    
    #st.session_state.already_displayed_count+=len(messages)
    
    for msg in messages:
      if(isinstance(msg["content"],dict)):
        msg["content"]=json_to_text_flat( msg["content"])
        
    try:
        response = call_openrouter_api(messages=messages)
        return response
    except Exception as e:
        st.error(f"Error calling API: {e}")
        return None

def show_notes_content(notes):
    title="📝 Notes"
    st.subheader(title)
    display_content(notes)

def show_chat_history(messages):
    for message in messages:
        with st.chat_message(message["role"]):
            if message.get("filename"):
                st.caption(f"Regarding: {message['filename']}")
            if isinstance(message["content"], dict):
                display_content_llm(message["content"])
            else:
                st.markdown(message["content"])
                
def handle_chat_input(prompt_label, notes, messages_list, filename=None, key=None):
    if prompt := st.chat_input(prompt_label, key=key):
        # 1. Add user message to history
        user_msg = {"role": "user", "content": prompt}
        if filename:
            user_msg["filename"] = filename
        messages_list.append(user_msg)

        # 2. Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # 3. Create loading placeholder
        placeholder = st.empty()
        
        try:
            # Show loading indicator
            with placeholder.container():
                st.image("https://media.tenor.com/FawYo00tBekAAAAM/loading-thinking.gif", width=30)
                response_content = ask_about_notes(prompt, notes)

            # Clear loading FIRST
            placeholder.empty()

            if response_content:
                # 4. Add assistant response to history
                assistant_msg = {"role": "assistant", "content": response_content}
                if filename:
                    assistant_msg["filename"] = filename
                messages_list.append(assistant_msg)

                # 5. Display assistant response
                with st.chat_message("assistant"):
                    display_content_llm(response_content)
        
        except Exception as e:
            placeholder.empty()  # Ensure loading is cleared on error too
            st.error(f"Error: {str(e)}")          
                    
                    
def render_load_ask_notes_mode():
    st.info("📂 Upload JSON notes")
    uploaded_json = st.file_uploader("Choose a JSON file", type="json")

    if uploaded_json:
        try:
            notes = json.load(uploaded_json)
            if isinstance(notes, dict) and "content" in notes:
                if st.session_state.get("current_file") != uploaded_json.name:
                    st.session_state.loaded_notes = notes
                    st.session_state.loaded_notes_messages = []
                    st.session_state.loaded_notes_messages_queries = []
                    st.session_state.current_file = uploaded_json.name
                st.success("Notes loaded successfully!")

                view_option = st.radio("Select view:", ("Show Both", "Show Only Notes", "Show Only Chat"), horizontal=True)

                if view_option == "Show Both":
                    col1, col2 = st.columns(2)
                    with col1:
                        show_notes_content(notes)
                    with col2:
                        st.subheader("💬 Chat about these notes")
                        show_chat_history(st.session_state.loaded_notes_messages_queries)
                        handle_chat_input("Ask about the uploaded notes...", notes, st.session_state.loaded_notes_messages_queries)
                elif view_option == "Show Only Notes":
                    show_notes_content(notes)
                elif view_option == "Show Only Chat":
                    st.subheader("💬 Chat about these notes")
                    show_chat_history(st.session_state.loaded_notes_messages_queries)
                    handle_chat_input("Ask about the uploaded notes...", notes, st.session_state.loaded_notes_messages_queries)
            else:
                st.error("Invalid notes format. Expected a dict with a 'content' list.")
        except Exception as e:
            st.error(f"Error loading JSON: {e}")
    else:
        st.info("Upload a JSON file with 'content' list to start.")

def render_ask_about_multiple_notes_mode():
    st.info("❓ Ask questions about your uploaded notes")

    if "uploaded_notes_files" not in st.session_state:
        st.session_state.uploaded_notes_files = {}
    if "current_file" not in st.session_state:
        st.session_state.current_file = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    uploaded_json_files = st.file_uploader("Upload JSON notes files", type="json", accept_multiple_files=True)

    if uploaded_json_files:
        for f in uploaded_json_files:
            try:
                notes = json.load(f)
                if isinstance(notes, dict):
                    st.session_state.uploaded_notes_files[f.name] = notes
                    st.success(f"Loaded: {f.name}")
                else:
                    st.error(f"Invalid format in {f.name} - expected dict")
            except Exception as e:
                st.error(f"Error loading {f.name}: {e}")

    if st.session_state.uploaded_notes_files:
        selected_file = st.selectbox("Currently viewing:", list(st.session_state.uploaded_notes_files.keys()))
        st.session_state.current_file = selected_file
        notes = st.session_state.uploaded_notes_files[selected_file]

        view_option = st.radio("Select view:", ("Show Both", "Show Only Notes", "Show Only Chat"), horizontal=True)

        if view_option == "Show Both":
            col1, col2 = st.columns(2)
            with col1:
                show_notes_content(notes)
            with col2:
                st.subheader("💬 Chat")
                show_chat_history(st.session_state.chat_messages)
                handle_chat_input("Ask about any uploaded file...", notes, st.session_state.chat_messages, filename=selected_file, key="both_chat")
        elif view_option == "Show Only Notes":
            show_notes_content(notes)
        elif view_option == "Show Only Chat":
            st.subheader("💬 Chat")
            show_chat_history(st.session_state.chat_messages)
            handle_chat_input("Ask about any uploaded file...", notes, st.session_state.chat_messages, filename=selected_file, key="chat_only")
    elif uploaded_json_files:
        st.warning("Please upload valid JSON notes files")
    else:
        st.info("Upload JSON files to start out")