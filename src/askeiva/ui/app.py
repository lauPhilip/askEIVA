import streamlit as st
import pandas as pd
from src.askeiva.core.agent import AskEIVA

# --- EIVA BRANDING ---
EIVA_BLUE = "#003366"
EIVA_YELLOW = "#FFCC00"
EIVA_GRAY = "#F8F9FA"

st.set_page_config(page_title="askEIVA", page_icon="⚓", layout="wide")

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ display: none; }}
    .stApp {{ background-color: #FFFFFF; }}
    .eiva-title {{ color: {EIVA_BLUE}; font-family: 'Helvetica Neue', sans-serif; }}
    .stChatMessage {{ background-color: {EIVA_GRAY}; border-radius: 8px; }}
    div.stButton > button {{ border: 1px solid {EIVA_BLUE}; color: {EIVA_BLUE}; }}
    div.stButton > button:hover {{ border: 1px solid {EIVA_YELLOW}; color: {EIVA_YELLOW}; }}
    </style>
    """, unsafe_allow_html=True)

if "agent" not in st.session_state:
    st.session_state.agent = AskEIVA()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HEADER & CLEAR ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown(f'<h1 class="eiva-title">⚓ askEIVA</h1>', unsafe_allow_html=True)
with col2:
    st.write("##")
    if st.button("🧹 Clear Deck"):
        st.session_state.messages = []
        st.rerun()

def display_reference_table(sources):
    if sources:
        st.write("---")
        st.caption("TECHNICAL EVIDENCE POOL")
        df = pd.DataFrame(sources)
        df.columns = ["Category", "Source Title", "Resource URL"]
        st.dataframe(
            df,
            column_config={
                "Resource URL": st.column_config.LinkColumn("Access Link", display_text="View Source"),
                "Category": st.column_config.TextColumn("Type", width="small")
            },
            hide_index=True, width="stretch"
        )

# --- CHAT LOOP ---
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "⚓"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if "sources" in message:
            display_reference_table(message["sources"])

if prompt := st.chat_input("Ask about EIVA systems or support cases..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="⚓"):
        full_response = st.write_stream(st.session_state.agent.stream_answer(prompt))
        sources = st.session_state.agent.get_sources(prompt)
        display_reference_table(sources)
        
        st.session_state.messages.append({
            "role": "assistant", "content": full_response, "sources": sources
        })