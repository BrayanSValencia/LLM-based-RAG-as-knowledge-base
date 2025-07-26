import json
from pathlib import Path
import re
import streamlit as st
import os
import fitz  # PyMuPDF
import tempfile
from langchain.prompts import ChatPromptTemplate
import sys
import unicodedata
import time

sys.path.append("rag/")
from utils.utils import  display_content_llm,call_openrouter_api
from utils.prompt import  const

max_retries = 10


def sanitize_filename(title):
    """Replace invalid filename characters with underscores."""
    normalized = unicodedata.normalize('NFD', title)
    ascii_text = ''.join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r'[\\/*?:"<>|]', '_', ascii_text)

def is_chapter(level, title):
    title_lower = title.lower()
    
    # Common non-chapter sections to exclude
    non_chapters = {
        "contents", "acknowledgments", "introduction", 
        "preface", "foreword", "notes", 
        "bibliography", "index", "references","epilogue"
    }
    # Single letters (like "A", "B" in index) → Exclude
    if len(title_lower) == 1 and title_lower.isalpha():
        return False
    
    # Cases where we KNOW it's NOT a chapter:
    if any(nc in title_lower for nc in non_chapters):
        return False
    
    
    # Cases where we KNOW it's a chapter:
    if (
        "chapter" in title_lower or        # "Chapter 1"
        "appendix" in title_lower or       # "Appendix A"
        title_lower.startswith("part") or  # "Part I"
        (level >= 2 and not any(nc in title_lower for nc in non_chapters))  # "1. Introduction"
    ):
        return True
    
    
    
    
    # Fallback: Assume level-2 entries are chapters
    return level == 2


def find_next_chapter_or_appendix_page(toc, start_index):
    for j in range(start_index+1, len(toc)):
        _, title, page = toc[j]
        if is_chapter(_, title):
            return page
    return None

def summarize_text(text):
    prompt_template = ChatPromptTemplate.from_template(const.PROMPT_TEMPLATE_SUMMINGUP_BOOKS_ARTICLES)
    prompt = prompt_template.format(context=text)
    response=call_openrouter_api(prompt)
    return response

def extract_chapter_text(doc, start_page, end_page):
    """Extract text between pages without file permission issues."""
    text = ""
    
    # Use a context manager for the temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_file:
        tmp_path = tmp_file.name
        
        # Extract pages to temp file
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
        new_doc.save(tmp_path)
        new_doc.close()
        
        # Read text from temp file
        with fitz.open(tmp_path) as chapter_doc:
            text = "\n".join(page.get_text() or "" for page in chapter_doc)
    
    return text  # Temp file auto-deletes when 'with' block ends

def save_summary_json(summary, base_name, title):
    """Save chapter summary as JSON file in databases/jsonnotes/"""
    # Create safe directory and file names
    safe_base = sanitize_filename(base_name.replace(".pdf", "").replace(" ", "_"))
    safe_title =sanitize_filename(title.replace(" ", "_").replace("/", "_"))
    
    # Create directory path
    output_dir = Path("databases") / "jsonnotes" / safe_base
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file path
    file_name = f"{safe_title}.json"
    file_path = output_dir / file_name
    
    # Save JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return file_path


def render_sum_up_book_mode():
    st.info("📄 Upload a PDF to summarize (all chapters using one prompt, regardless the length) (it must have TOC)")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        st.success(f"PDF uploaded: {uploaded_file.name}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(uploaded_file.getbuffer())

        try:
            doc = fitz.open(tmp_path)
            toc = doc.get_toc()
            if not toc:
                st.error("The PDF does not contain TOC.")
                return
                
            chapter_summaries = []
            base_name = uploaded_file.name.replace(".pdf", "")

            for i, (level, title, page) in enumerate(toc):
                if is_chapter(level, title):
                    start_page = page - 1  # Convert to 0-based index
                    next_page = find_next_chapter_or_appendix_page(toc, i)
                    end_page = (next_page - 2) if next_page else (doc.page_count - 1)

                    # Ensure end_page is not before start_page
                    end_page = max(start_page, end_page)

                    chapter_text = extract_chapter_text(doc, start_page, end_page)
                    
                    if not chapter_text.strip():
                        st.warning(f"Skipping empty chapter: {title}")
                        continue

                    with st.spinner(f"Summarizing {title}..."):
                        for attempt in range(1, max_retries + 1):
                            try:
                                summary = summarize_text(chapter_text)
                                if summary is None:
                                    if attempt < max_retries:
                                        print(f"Attempt {attempt} failed with None, retrying...")
                                        continue
                                    else:
                                        st.error(f"Too many retries, the book couldn't be summarized")
                                        return
                                    
                                save_summary_json(summary, base_name, title)
                                chapter_summaries.append({"title": title, "summary": summary})
                                break  # success, exit the retry loop
                            except Exception as e:
                                if attempt < max_retries:
                                    st.warning(f"Attempt {attempt} failed, retrying...")
                                    time.sleep(1)  # small pause before retry
                                else:
                                    st.error(f"Failed to summarize {title} after {max_retries} attempts: {str(e)}")
                                    st.error(f"Too many retries, the book couldn't be summarized")
                                    return
            
            if not chapter_summaries:
                st.error("No chapters were processed. Check if the TOC contains valid chapter entries.")
                return

            # Summarize all chapters together
            final_notes = "\n\n".join(
                f"### {item['title']}\n{item['summary']}" for item in chapter_summaries
            )

            with st.spinner(f"Summarizing entire book: {uploaded_file.name}..."):
                for attempt in range(1, max_retries + 1):
                    try:
                        final_summary = summarize_text(final_notes)
                        display_content_llm(final_summary)
                        
                        # Save final summary
                        output_dir = Path("databases") / "jsonnotes" / base_name
                        output_dir.mkdir(parents=True, exist_ok=True)
                        final_json_path = output_dir / f"{base_name}_full.json"
                        
                        with open(final_json_path, "w", encoding="utf-8") as f:
                            json.dump(final_summary, f, indent=2)
                        
                        st.success("✅ All chapters processed and final notes generated!")
                        break  # success
                    except Exception as e:
                        if attempt < max_retries:
                            st.warning(f"Attempt {attempt} failed, retrying...")
                            time.sleep(1)  # optional pause before next attempt
                        else:
                            st.error(f"Failed to generate final summary after {max_retries} attempts: {str(e)}")

        finally:
            doc.close()
            try:
                os.remove(tmp_path)
            except:
                pass