import streamlit as st
import pandas as pd
from datetime import datetime
from src.askeiva.core.agent import AskEIVA

# --- EIVA BRANDING CONSTANTS ---
EIVA_BLUE = "#003366"
EIVA_YELLOW = "#FFCC00"
EIVA_GRAY = "#F8F9FA"

st.set_page_config(page_title="askEIVA", page_icon="⚓", layout="centered")

# --- UI STYLING ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ display: none; }}
    .stApp {{ background-color: #FFFFFF; }}
    .header-container {{ border-bottom: 2px solid {EIVA_YELLOW}; margin-bottom: 25px; }}
    .eiva-title {{ color: {EIVA_BLUE}; font-family: 'Helvetica Neue', sans-serif; }}
    .stChatMessage {{ background-color: {EIVA_GRAY}; border-radius: 8px; }}
    /* Clear button styling */
    div.stButton > button {{ border: 1px solid {EIVA_BLUE}; color: {EIVA_BLUE}; }}
    div.stButton > button:hover {{ border: 1px solid {EIVA_YELLOW}; color: {EIVA_YELLOW}; }}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if "agent" not in st.session_state:
    st.session_state.agent = AskEIVA()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HEADER & CLEAR BUTTON ---
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
            column_config={  # Use single braces here
                "Resource URL": st.column_config.LinkColumn(
                    "Access Link", 
                    display_text="View Source"
                ),
                "Category": st.column_config.TextColumn(
                    "Type", 
                    width="small"
                )
            }, # And single brace here
            hide_index=True, 
            width='stretch'
        )

# --- CHAT HISTORY ---
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "⚓"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if "sources" in message:
            display_reference_table(message["sources"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Query EIVA Support History & Manuals..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="⚓"):
        # This will now find the stream_answer method in your agent
        full_response = st.write_stream(st.session_state.agent.stream_answer(prompt))
        sources = st.session_state.agent.get_sources(prompt)
        display_reference_table(sources)
        
        st.session_state.messages.append({
            "role": "assistant", "content": full_response, "sources": sources
        })