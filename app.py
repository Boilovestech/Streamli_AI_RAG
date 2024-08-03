import os
from typing import List
import streamlit as st
from groq import Groq
import PyPDF2
from dotenv import load_dotenv

load_dotenv()



groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
GROQ_MODELS = [
    "mixtral-8x7b-32768",
    "llama2-70b-4096",
    "gemma-7b-it",
]

def generate_response(query: str, model: str, context: str = "") -> str:
    try:
        prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.5,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def parse_pdf_sections(pdf_content):
    sections = {
        "abstract": "",
        "introduction": "",
        "methodology": "",
        "results": "",
        "discussion": "",
        "conclusion": "",
    }
    
    current_section = ""
    for line in pdf_content.split('\n'):
        lower_line = line.lower()
        if "abstract" in lower_line:
            current_section = "abstract"
        elif "introduction" in lower_line:
            current_section = "introduction"
        elif "methodology" in lower_line or "methods" in lower_line:
            current_section = "methodology"
        elif "results" in lower_line:
            current_section = "results"
        elif "discussion" in lower_line:
            current_section = "discussion"
        elif "conclusion" in lower_line:
            current_section = "conclusion"
        
        if current_section:
            sections[current_section] += line + "\n"
    
    return sections

def main():
    st.title("RAG based Chatbot 📝✨")
    st.sidebar.header("Reference Commands")
    st.sidebar.write("Use these prefixes to query specific sections:")
    st.sidebar.write("📌 abstract:")
    st.sidebar.write("📌 introduction:")
    st.sidebar.write("📌 methodology:")
    st.sidebar.write("📌 results:")
    st.sidebar.write("📌 discussion:")
    st.sidebar.write("📌 conclusion:")
    st.sidebar.write("Example: 'abstract: What is the main topic?'")
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = ""
    if "pdf_sections" not in st.session_state:
        st.session_state.pdf_sections = {}

    # PDF upload
    uploaded_file = st.file_uploader("Choose a PDF file for analysis", type="pdf")
    if uploaded_file is not None:
        pdf_content = extract_text_from_pdf(uploaded_file)
        st.session_state.pdf_content = pdf_content
        st.session_state.pdf_sections = parse_pdf_sections(pdf_content)
        st.success("PDF uploaded and processed successfully!")

    # Model selection
    model = st.selectbox("Choose a model:", GROQ_MODELS)

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the PDF (e.g., 'abstract: What is the main topic?'):"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        with st.spinner("Generating response..."):
            section, query = prompt.split(": ", 1) if ": " in prompt else ("all", prompt)
            context = st.session_state.pdf_sections.get(section.lower(), st.session_state.pdf_content)
            response = generate_response(query, model, context)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").markdown(response)

if __name__ == "__main__":
    main()
