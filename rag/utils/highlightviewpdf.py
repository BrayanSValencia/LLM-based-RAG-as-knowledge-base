import sys
import fitz  # PyMuPDF
import os
import subprocess
import time
import threading



def highlight_and_view_pdf(input_path, search_text, page_num=1):
    """
    Highlights search_text on the given page, saves a temp copy, opens it, then deletes it.
    Args:
        input_path (str): Path to original PDF
        search_text (str): Text to highlight
        page_num (int): 1-based page number to highlight on & open
    Returns:
        bool: True on success, False on failure
    """
    output_path = os.path.join(
        os.path.dirname(input_path),
        f"temp_highlighted_{os.path.basename(input_path)}_{page_num}.pdf"
    )

    if not _highlight_pdf(input_path, output_path, search_text, page_num):
        print("Highlighting failed.", flush=True)
        return False

    _open_and_autodelete_pdf(output_path, page_num)
    return True

def _highlight_pdf(input_path, output_path, search_text, page_num):
    """Highlight all occurrences of search_text on the specified page."""
    try:
        with fitz.open(input_path) as doc:
           
            page_index = int(page_num) - 1
            if page_index < 0 or page_index >= len(doc):
                print(f"Invalid page number. PDF has {len(doc)} pages.", flush=True)
                return False

            page = doc.load_page(page_index)
            text_instances = page.search_for(search_text)

            if not text_instances:
                print(f"Text '{search_text}' not found on page {page_num}. Will still open the page.", flush=True)
            else:
                print(f"Found {len(text_instances)} instance(s) of '{search_text}' on page {page_num}. Highlighting...", flush=True)
                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors({"stroke": (1, 1, 0)})  # yellow highlight
                    highlight.update()

            doc.save(output_path)
            print(f"Temporary highlighted PDF saved: {output_path}", flush=True)
            return True

    except Exception as e:
        print(f"Error during highlighting: {e}", flush=True)
        return False

def _open_and_autodelete_pdf(file_path, target_page=1):
    """
    Opens PDF on a specific page (using Acrobat on Windows) and deletes the file after some time.
    """
    system = sys.platform

    def cleanup_temp_file():
        try:
            time.sleep(2)  # wait for viewer to start
            print("PDF opened. Will delete temporary file soon...", flush=True)
            time.sleep(5)  # wait before delete
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Temporary file deleted: {file_path}", flush=True)
                except Exception as e:
                    print(f"Failed to delete temp file immediately: {e}. Retrying...", flush=True)
                    time.sleep(5)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Deleted on retry: {file_path}", flush=True)
        except Exception as e:
            print(f"Cleanup thread error: {e}", flush=True)

    try:
        if system == "win32":
            # Adjust this path to your actual Acrobat.exe
            path_to_acrobat = r"C:/Program Files/Adobe/Acrobat DC/Acrobat/Acrobat.exe"
            subprocess.Popen([
                path_to_acrobat,
                '/A', f'page={target_page}',
                file_path
            ], shell=False)
        """
        elif system == "darwin":  # macOS
            subprocess.Popen([
                "open", "-a", "Preview",
                f"{file_path}#page={target_page}"
            ])

        else:  # Linux / Unix
            subprocess.Popen([
                "evince", f"--page-index={target_page-1}",
                file_path
            ])
        """
        # Start background cleanup
        threading.Thread(target=cleanup_temp_file, daemon=True).start()

    except Exception as e:
        print(f"Failed to open PDF: {e}", flush=True)
        # Try immediate delete on failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up after open failure: {file_path}", flush=True)
        except Exception as cleanup_error:
            print(f"Failed to delete temp file after open failure: {cleanup_error}", flush=True)
