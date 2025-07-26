
import streamlit as st 
import sys
sys.path.append("rag/")
from utils.utils import display_content

def render_sum_up_website_mode():
    st.info("🌐 Enter a website URL to summarize")
    url = st.text_input("Paste website URL here:")
    if url:
        st.success(f"URL submitted: {url}")
        example_summary = [
            {"type": "header", "text": "Website Summary"},
            {"type": "paragraph", "text": f"Summary of content from {url}"},
            {"type": "annotation", "text": "Important Note", "note": "This is an automatically generated summary"}
        ]
        display_content({"content": example_summary})