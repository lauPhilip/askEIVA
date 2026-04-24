import streamlit as st
import base64
from src.askeiva.core.agent import AskEIVA

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="askEIVA | Engineering Intelligence",
    page_icon="⚓",
    layout="wide"
)

# --- EIVA BRANDING INJECTION ---
st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{
        background-color: #FFFFFF;
    }}
    
    /* Custom Header Bar to match EIVA Homepage */
    .nav-bar {{
        background-color: white;
        padding: 10px;
        border-bottom: 2px solid #f0f0f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
    }}

    /* EIVA Navy Blue Headers */
    h1, h2, h3 {{
        color: #003366 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }}

    /* Maritime Industrial Styling for Chat */
    .stChatMessage {{
        background-color: #f8f9fa;
        border-radius: 5px;
        border-left: 5px solid #003366;
    }}

    /* Safety Yellow for User Input Accent */
    .stChatInputContainer textarea {{
        border: 2px solid #FFCC00 !important;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #f4f4f4;
        border-right: 1px solid #e0e0e0;
    }}
    </style>
    """, unsafe_allow_init=True)

# --- SESSION INITIALIZATION ---
if "agent" not in st.session_state:
    with st.spinner("Connecting to EIVA Knowledge Graph..."):
        st.session_state.agent = AskEIVA()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- TOP NAVIGATION BAR ---
st.markdown("""
    <div class="nav-bar">
        <h2 style='margin:0;'>EIVA <span style='font-weight:300; font-size: 0.8em;'>askEIVA</span></h2>
        <div style='color: #666;'>Herning Engineering Hub | System Operational</div>
    </div>
""", unsafe_allow_init=True)

# --- SIDEBAR TOOLS ---
with st.sidebar:
    st.title("Settings")
    st.info("Mode: Full-Spectrum Retrieval (Manuals + Tickets)")
    if st.button("Reset Session Memory"):
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    st.markdown("**Core Model:** Mistral-Large-Latest")
    st.markdown("**Knowledge Nodes:** 100+ Tickets Ingested")

# --- MAIN CHAT INTERFACE ---
# Display historical messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Interaction Logic
if prompt := st.chat_input("Ask about ScanFish, NaviSuite, or recent support tickets..."):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Consulting internal technical debt..."):
            response = st.session_state.agent.generate_answer(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})