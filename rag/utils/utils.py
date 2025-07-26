
import json
import os
import requests
import streamlit as st
import contextlib
import io
import time
from dotenv import load_dotenv
def clean_json_response(response_text):
    """Clean and prepare JSON response for parsing."""
    # Remove markdown code fences if present
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    
    return cleaned

def display_content(notes):
    """Display content in the specified format."""
    for part in notes["content"]:
        if part["type"] == "header":
            st.markdown(f"### {part['text']}")
        elif part["type"] == "paragraph":
            st.write(part["text"])
        elif part["type"] == "highlight":
            st.markdown(
                f"<span style='background-color: rgba(255, 243, 176, 0.3); font-weight: 600;'>{part['text']}</span>",
                unsafe_allow_html=True,
            )
        elif part["type"] == "annotation":
            with st.expander(f"ℹ️ {part['text']}"):
                st.write(part["note"])
        elif part["type"] == "code":
            st.code(part["code"], language=part["language"])
        elif part["type"] == "code_executable":
            st.code(part["code"], language=part["language"])
            run = st.button(f"▶️ Run code: {part['code']}", key=part["code"])
            if run:
                if part["language"] == "python":
                    f = io.StringIO()
                    try:
                        with contextlib.redirect_stdout(f):
                            exec(part["code"])
                            
                               
                        output = f.getvalue()
                        st.success(f"Output:\n{output}")
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    st.error("Only Python execution supported right now.")

def display_content_llm(notes):
    """Display content with animation effect."""
    for part in notes["content"]:
        if part["type"] == "header":
            placeholder = st.empty()
            words = part['text'].split()
            text_so_far = ""
            for word in words:
                text_so_far += word + " "
                placeholder.markdown(f"### {text_so_far}")
                time.sleep(0.05)

        elif part["type"] == "paragraph":
            placeholder = st.empty()
            words = part['text'].split()
            text_so_far = ""
            for word in words:
                text_so_far += word + " "
                placeholder.write(text_so_far)
                time.sleep(0.05)

        elif part["type"] == "highlight":
            placeholder = st.empty()
            words = part['text'].split()
            text_so_far = ""
            for word in words:
                text_so_far += word + " "
                placeholder.markdown(
                    f"<span style='background-color: rgba(255, 243, 176, 0.3); font-weight: 600;'>{text_so_far}</span>",
                    unsafe_allow_html=True,
                )
                time.sleep(0.05)

        elif part["type"] == "annotation":
            with st.expander(f"ℹ️ {part['text']}"):
                st.write(part["note"])

        elif part["type"] == "code":
            st.code(part["code"], language=part["language"])

        elif part["type"] == "code_executable":
            st.code(part["code"], language=part["language"])
            run = st.button(f"▶️ Run code: {part['code']}", key=part["code"])
            if run:
                if part["language"] == "python":
                    f = io.StringIO()
                    try:
                        with contextlib.redirect_stdout(f):
                            exec(part["code"])
                            
                                
                        output = f.getvalue()
                        st.success(f"Output:\n{output}")
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    st.warning("Only Python execution supported right now.")

def json_to_text_flat(json_obj):
    """
    Converts a nested JSON/dict object into a single plain text string,
    concatenating all keys and values, handling lists as comma-separated.
    """
    parts = []
    for key, value in json_obj.items():
        # If the value is a list, join its items with commas
        if isinstance(value, list):
            value_str = ', '.join(str(item) for item in value)
        # If the value is another dict, recurse and flatten it
        elif isinstance(value, dict):
            value_str = json_to_text_flat(value)
        else:
            value_str = str(value)
        parts.append(f"{key}: {value_str}")
    # Join all parts with a space (or newline if you prefer)
    return ' '.join(parts)

def json_to_markdown(json_data):
    md_lines = []

    for item in json_data['content']:
        item['text']=item['text'].replace("•","-")
        t = item['type']
        if t == 'header':
            md_lines.append(f"\n## {item['text']}\n")
        elif t == 'paragraph':
            md_lines.append(f"{item['text']}\n")
        elif t == 'annotation':
            md_lines.append(f"**{item['text']}**\n- {item['note']}\n")
        else:
            # fallback if unknown type
            md_lines.append(f"{item.get('text', '')}\n")
    return md_lines


def call_openrouter_api(prompt=None,messages=None)->json:


    """
    Calls the OpenRouter API with the given prompt.
    """
    
    if not prompt and not messages:
        raise ValueError("Provide either prompt or messages")
    
    

    load_dotenv()
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek/deepseek-r1-0528:free",
            "messages": [{"role": "user", "content": prompt}] if prompt else messages
        })
    )
    
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")
    
    response.raise_for_status()
    resp_json = response.json()
    response_text = resp_json["choices"][0]["message"]["content"]
    
    # Remove possible code fences
    str_result = clean_json_response(response_text)
    
    try:
        parsed_response= json.loads(str_result)

        if not isinstance(parsed_response, dict) or "content" not in parsed_response:
            print("LLM returned invalid format - missing 'content' key")
            return None
        return parsed_response
    
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}")
        return None
    except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                st.warning("Too many requests! Please wait a few seconds before asking again.")
                st.session_state.loaded_notes_messages_queries.append({"role": "assistant", "content": "Too many requests! Please wait a few seconds before asking again."})
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    