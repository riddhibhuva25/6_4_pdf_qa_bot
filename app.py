import hashlib
import os
import streamlit as st

from rag_utility import answer_question, process_document_to_chroma_db

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="DocuMind AI | PDF Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

working_dir = os.path.dirname(os.path.abspath(__file__))

# ---------------- SESSION STATE ----------------

if "processed_hash" not in st.session_state:
  st.session_state.processed_hash = None

if "document_ready" not in st.session_state:
  st.session_state.document_ready = False

if "document_name" not in st.session_state:
  st.session_state.document_name = None

if "messages" not in st.session_state:
  st.session_state.messages = []

# ---------------- CUSTOM CSS ----------------

st.markdown(
    """
<style>
    .stApp {
        background-color: #F8FAFC;
    }

    .main .block-container {
        max-width: 950px;
        padding-top: 1.5rem;
        padding-bottom: 5rem;
    }

    .hero-banner {
        background: linear-gradient(135deg, #3B4CCA 0%, #6366F1 50%, #8B5CF6 100%);
        padding: 30px 36px;
        border-radius: 20px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.25);
    }
    .hero-banner h1 {
        color: #FFFFFF !important;
        font-size: 28px;
        font-weight: 700;
        margin: 8px 0 6px 0;
    }
    .hero-banner p {
        color: #E0E7FF;
        font-size: 15px;
        margin: 0;
        max-width: 650px;
        line-height: 1.5;
    }
    .badge-hero {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        letter-spacing: 0.5px;
    }

    .tech-pill {
        display: inline-block;
        background-color: #EEF2FF;
        color: #4F46E5;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin: 3px 2px;
        border: 1px solid #E0E7FF;
    }

    button[kind="primary"] {
        background-color: #6366F1 !important;
        border-color: #6366F1 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- SIDEBAR: UPLOAD & CONFIG ----------------

with st.sidebar:
  st.markdown("### 📄 **DocuMind AI**")
  st.caption("Context-Aware Document Intelligence")
  st.divider()

  st.markdown("#### 📁 **Document Source**")
  uploaded_file = st.file_uploader(
      "Upload a PDF",
      type=["pdf"],
      help="Upload a PDF document to index into ChromaDB.",
  )

  # Auto-detect removal via (x) vs processing a new file
  if uploaded_file is None:
    st.session_state.document_ready = False
    st.session_state.document_name = None
    st.session_state.processed_hash = None
    st.session_state.messages = []
  else:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()

    if st.session_state.processed_hash != file_hash:
      safe_filename = os.path.basename(uploaded_file.name)
      save_path = os.path.join(working_dir, safe_filename)

      try:
        with open(save_path, "wb") as f:
          f.write(file_bytes)

        with st.spinner("🔄 Indexing document into vector store..."):
          process_document_to_chroma_db(safe_filename)

        st.session_state.processed_hash = file_hash
        st.session_state.document_ready = True
        st.session_state.document_name = safe_filename
        st.session_state.messages = []
        st.success("✅ Ready to analyze!")
      except Exception as e:
        st.session_state.document_ready = False
        st.error(f"Error processing file: {e}")

  # Status Badge & Chat Reset
  if st.session_state.document_ready:
    st.info(f"🟢 **Indexed:** `{st.session_state.document_name}`")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
      st.session_state.messages = []
      st.rerun()
  else:
    st.warning("🟡 Awaiting document upload.")

  st.divider()

  st.markdown("#### ⚙️ **Stack & Architecture**")
  st.markdown(
      """
        <div>
            <span class="tech-pill">Python</span>
            <span class="tech-pill">LangChain</span>
            <span class="tech-pill">ChromaDB</span>
            <span class="tech-pill">Groq LLM</span>
            <span class="tech-pill">Streamlit</span>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.divider()
  st.caption("DocuMind AI • Built with RAG")


# ---------------- MAIN HERO BANNER ----------------

st.markdown(
    """
<div class="hero-banner">
    <div class="badge-hero">GROQ + CHROMADB RAG</div>
    <h1>Chat with your PDF</h1>
    <p>Ask natural questions about your uploaded documents and get grounded, context-aware answers in real-time.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------- CHAT WORKSPACE ----------------

if not st.session_state.document_ready:
  st.info("👈 Please upload a PDF document in the sidebar to start.")
else:
  # Quick Starter Prompts
  st.caption("💡 **Quick Actions:**")
  col1, col2, col3 = st.columns(3)
  quick_prompt = None

  with col1:
    if st.button("📝 Summarize Document", use_container_width=True):
      quick_prompt = "Provide a concise summary of the entire document with key takeaways."
  with col2:
    if st.button("🔑 Key Takeaways", use_container_width=True):
      quick_prompt = (
          "What are the top 5 most important points or findings in this"
          " document?"
      )
  with col3:
    if st.button("❓ Recommended Questions", use_container_width=True):
      quick_prompt = (
          "Based on this document, what are 3 important questions a reader"
          " should ask?"
      )

  st.write("")

  # Render conversation history
  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.markdown(msg["content"])

  # Handle chat input from the bar or quick action chips
  chat_input_val = st.chat_input("Ask a question about this document...")
  user_input = chat_input_val or quick_prompt

  if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
      st.markdown(user_input)

    with st.chat_message("assistant"):
      with st.spinner("Analyzing document..."):
        try:
          response = answer_question(user_input)
          st.markdown(response)
          st.session_state.messages.append(
              {"role": "assistant", "content": response}
          )
        except Exception as e:
          error_msg = f"⚠️ Could not generate an answer: {e}"
          st.error(error_msg)
          st.session_state.messages.append(
              {"role": "assistant", "content": error_msg}
          )