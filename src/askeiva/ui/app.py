import streamlit as st
from src.askeiva.core.agent import AskEIVA

# Branding Constants
EIVA_BLUE = "#003366"
EIVA_YELLOW = "#FFCC00"
EIVA_GRAY = "#F8F9FA"

st.set_page_config(
    page_title="askEIVA | Customer Service Agent",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed" # Hides sidebar by default
)

# Custom CSS for UI polish
st.markdown(f"""
    <style>
    /* Hide sidebar entirely */
    [data-testid="stSidebar"] {{ display: none; }}
    
    .stApp {{ background-color: #FFFFFF; }}
    
    /* Header Styling */
    .eiva-header {{
        color: {EIVA_BLUE};
        border-bottom: 2px solid {EIVA_YELLOW};
        padding-bottom: 10px;
        margin-bottom: 25px;
        font-family: 'Helvetica Neue', sans-serif;
    }}
    
    /* Maritime Themed Chat Bubbles */
    .stChatMessage {{ background-color: {EIVA_GRAY}; border-radius: 8px; }}
    
    /* Marine Yellow Accent for inputs */
    .stChatInputContainer textarea {{ border: 1px solid {EIVA_BLUE} !important; }}
    </style>
    <h1 class="eiva-header">⚓ askEIVA</h1>
    """, unsafe_allow_html=True)

# Persistent Session
if "agent" not in st.session_state:
    st.session_state.agent = AskEIVA()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History with Maritime Icons
for message in st.session_state.messages:
    # User = 👤 (Navigator) | Assistant = ⚓ (The Anchor/Support)
    avatar = "👤" if message["role"] == "user" else "⚓"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("How can I assist with EIVA operations today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="⚓"):
        # Real-time streaming response
        full_response = st.write_stream(st.session_state.agent.stream_answer(prompt))
        st.session_state.messages.append({"role": "assistant", "content": full_response})