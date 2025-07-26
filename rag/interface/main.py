import streamlit as st

import sys



sys.path.append("rag/")   # adjust path as needed
from functionalities.loadingasknotes import   render_ask_about_multiple_notes_mode, render_load_ask_notes_mode
from functionalities.knowledgebase import render_knowledge_base_mode
from functionalities.summingupbookarticle import render_sum_up_book_mode
from functionalities.generatingmindmapnotes import render_mindmap_notes_mode
from functionalities.summingupwebsite import render_sum_up_website_mode

# -----------------------
# Initialize session state
# -----------------------
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Generate Mindmap Notes"

if "kb_messages" not in st.session_state:
    st.session_state.kb_messages = []

if "notes_messages" not in st.session_state:
    st.session_state.notes_messages = []

if "loaded_notes" not in st.session_state:
    st.session_state.loaded_notes = None

if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

if "loaded_notes_messages" not in st.session_state:
    st.session_state.loaded_notes_messages = []

if "current_file" not in st.session_state:
    st.session_state.current_file = None
    
if "loaded_notes_messages_queries" not in st.session_state:
    st.session_state.loaded_notes_messages_queries = []

#if 'already_displayed_count' not in st.session_state:
   #  st.session_state.already_displayed_count = 0
     
if "buttons_citations" not in st.session_state:
    st.session_state.buttons_citations = []
# -----------------------
# Mode selector
# -----------------------
selected_mode = st.selectbox(
    "Choose mode:",
    [
        "Knowledge Base",
        "Ask About Multiple Notes",
        "Load And Ask About Notes",
        "Sum Up Book/Article",
       # "Sum Up Website",
        "Generate Mindmap Notes"
    ]
)

# -----------------------
# Detect mode change & reset session state
# -----------------------

# -----------------------
# Mode render functions
# -----------------------

# -----------------------
# Execute only the selected mode
# -----------------------
if selected_mode == "Knowledge Base":
    render_knowledge_base_mode()
elif selected_mode == "Ask About Multiple Notes":
    render_ask_about_multiple_notes_mode()
elif selected_mode == "Load And Ask About Notes":
    render_load_ask_notes_mode()
elif selected_mode == "Sum Up Book/Article":
    render_sum_up_book_mode()
#elif selected_mode == "Sum Up Website":
#    render_sum_up_website_mode()
elif selected_mode == "Generate Mindmap Notes":
    render_mindmap_notes_mode()