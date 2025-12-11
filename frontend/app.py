import streamlit as st
import requests
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.set_page_config(page_title="AI PPT/PDF Compressor", layout="wide")

st.title("AI PPT/PDF Compressor")

st.markdown(
    "Upload your PowerPoint or PDF. The app will:\n"
    "- If the file is **≤ 50 MB** → return it **unchanged**.\n"
    "- If the file is **> 50 MB** → convert PPT/PPTX to PDF (if needed) and compress "
    "the PDF using smart settings chosen by the app.\n\n"
    "You can adjust the prompt to ask for *max compression* or *print quality*."
)

st.header("Compress a file")

with st.form("compress-form"):
    uploaded_file = st.file_uploader(
        "Choose a PPT/PPTX/PDF file", type=["ppt", "pptx", "pdf"]
    )
    prompt = st.text_input(
        "Compression prompt",
        value="Compress to small size file and keep charts/text clear.",
    )
    submitted = st.form_submit_button("Run")

if submitted:
    if uploaded_file is None:
        st.error("Please upload a file before running.")
    else:
        with st.spinner("Compressing, please wait..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }
            data = {"prompt": prompt}

            try:
                resp = requests.post(
                    f"{API_BASE}/optimize", files=files, data=data, timeout=600
                )
            except Exception as e:
                st.error(f"Error calling backend: {e}")
            else:
                if resp.status_code != 200:
                    st.error(f"Backend returned {resp.status_code}: {resp.text}")
                else:
                    headers = resp.headers
                    original_size = headers.get("X-Original-Size-MB", "N/A")
                    final_size = headers.get("X-Final-Size-MB", "N/A")
                    ratio = headers.get("X-Compression-Ratio", "N/A")
                    compressed_flag = headers.get("X-Compressed", "false")
                    explanation = headers.get("X-Explanation", "")

                    st.success("Processing completed.")

                    st.write(f"**Original size:** {original_size} MB")
                    st.write(f"**Final size:** {final_size} MB")
                    st.write(f"**Compression ratio:** {ratio}")

                    if compressed_flag.lower() == "true":
                        st.info(
                            "The file was larger than 50 MB and has been converted "
                            "and compressed to PDF."
                        )
                        download_name = f"compressed_{os.path.splitext(uploaded_file.name)[0]}.pdf"
                    else:
                        st.info(
                            "The file was at or below the 50 MB threshold. "
                            "No compression was applied; returning the original file."
                        )
                        download_name = uploaded_file.name

                    if explanation:
                        with st.expander("How was this handled? (Explanation)"):
                            st.write(explanation)

                    st.download_button(
                        label="Download Compressed File",
                        data=resp.content,
                        file_name=download_name,
                        mime=resp.headers.get("content-type", "application/octet-stream"),
                    )
