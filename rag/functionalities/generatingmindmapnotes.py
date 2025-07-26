
import json
from pathlib import Path
import streamlit as st 
import subprocess
import pandas as pd
import sys 
sys.path.append("rag/")
from utils.utils import json_to_markdown
from dotenv import load_dotenv
import os
def render_mindmap_notes_mode():
    load_dotenv()
    st.info("🗺️ Upload your to generate mindmap notes")
    uploaded_file = st.file_uploader("Choose your notes file(JSON)", type="json")

    if uploaded_file is not None:
        st.success(f"Notes uploaded: {uploaded_file.name}")
        
        json_file=json.load(uploaded_file)

        markdown_output = "\n".join(json_to_markdown(json_file))
        
        cleaned_name=uploaded_file.name.replace(".json","")
        output_dir = Path(f"databases/mindmapsnotes/{cleaned_name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_md_path = output_dir / f"{cleaned_name}.md"
        

        # Save the uploaded file to a temporary location
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)
       
        subprocess.run([os.getenv('NPX_CMD_PATH'),"markmap-cli", output_md_path], check=True)
 
        