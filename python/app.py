# Heavily based on https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps

import PyPDF2
import json
import streamlit as st
from cloudflare import Cloudflare

# Configure the page to be presentable
st.set_page_config(
    page_title="AI-Powered Resume Feedback Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar for theme selection
with st.sidebar:
    theme = st.selectbox("Theme:", ["Light", "Dark", "System Default"])

# Apply theme based on selection
if theme == "Dark":
    st.markdown("""
        <style>
        /* General body styles */
        body {
            background-color: #0e1117 !important;
            color: #f0f0f0 !important;
        }
        
        /* Adjust Streamlit container background */
        .stApp {
            background-color: #0e1117 !important;
            color: #f0f0f0 !important;
        }

        /* Style sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23 !important;
            color: #f0f0f0 !important;
            border-right: 1px solid #333333 !important;
        }

        /* Style all widget containers (file uploader, radio, etc.) */
        .stRadio, .stFileUploader {
            background-color: #1a1d23 !important;
            border: 1px solid #333333 !important;
            border-radius: 5px !important;
            padding: 10px !important;
            color: #f0f0f0 !important;
        }

        /* Style radio labels */
        label {
            color: #f0f0f0 !important;
            font-size: 14px !important;
        }

        /* Adjust the selected radio button's text and background */
        input[type="radio"]:checked + div {
            background-color: #333333 !important;
            color: white !important;
            border: 2px solid #555555 !important;
        }

        /* Style file uploader text */
        div[data-testid="stFileUploader"] label {
            color: #f0f0f0 !important;
        }

        /* Style buttons */
        .stButton>button {
            background-color: #333333 !important;
            color: white !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 10px 20px !important;
            font-size: 16px !important;
            cursor: pointer !important;
        }
        .stButton>button:hover {
            background-color: #555555 !important;
        }
        </style>
    """, unsafe_allow_html=True)
elif theme == "Light":
    st.markdown("""
        <style>
        /* General body styles */
        body {
            background-color: white !important;
            color: black !important;
        }
        
        /* Adjust Streamlit container background */
        .stApp {
            background-color: white !important;
            color: black !important;
        }

        /* Style sidebar */
        section[data-testid="stSidebar"] {
            background-color: #f9f9f9 !important;
            color: black !important;
            border-right: 1px solid #cccccc !important;
        }

        /* Style all widget containers (file uploader, radio, etc.) */
        .stRadio, .stFileUploader {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
            border-radius: 5px !important;
            padding: 10px !important;
            color: black !important;
        }

        /* Style radio labels */
        label {
            color: black !important;
            font-size: 14px !important;
        }

        /* Adjust the selected radio button's text and background */
        input[type="radio"]:checked + div {
            background-color: #e0e0e0 !important;
            color: black !important;
            border: 2px solid #cccccc !important;
        }

        /* Style file uploader text */
        div[data-testid="stFileUploader"] label {
            color: black !important;
        }

        /* Style buttons */
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 10px 20px !important;
            font-size: 16px !important;
            cursor: pointer !important;
        }
        .stButton>button:hover {
            background-color: #45a049 !important;
        }
        </style>
    """, unsafe_allow_html=True)

st.title("AI-Powered Resume Feedback Assistant")

# Set Cloudflare API key from Streamlit secrets
client = Cloudflare(api_token=st.secrets["CLOUDFLARE_API_TOKEN"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Allow user to choose feedback type
feedback_type = st.radio(
    "What kind of feedback would you like?",
    options = ["General Improvement", "Specific Feedback for a Role"],
    index = 0,
)

# If "Specific Feedback" is selected, ask for role/industry input
role_context = None
if feedback_type == "Specific Feedback for a Role":
    role_context = st.text_input("Enter the role or industry you're targeting:")

# Build initial message to the system based on user selection
if feedback_type == "General Improvement":
    system_instruction = (
        "You are a helpful assistant specializing in providing general feedback for resumes."
        "Analyze the provided resume and suggest improvements in formatting, clarity, and context."
    )
elif feedback_type == "Specific Feedback for a Role":
    system_instruction = (
        f"You are a career advisor specializing in providing tailored feedback for resumes."
        f"The user is targetting a role or industry: '{role_context}'."
        "Analyze the provided resume and suggest improvements specifically to make it more suitable for the target role or industry."
    )

# Accept user input (resume file)
uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file:
    # Read the content of the uploaded file
    if uploaded_file.type == "application/pdf":
        pdf_reader=PyPDF2.PdfReader(uploaded_file)
        resume_text=""
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
    elif uploaded_file.type == "text/plain":
        resume_text = uploaded_file.read().decode("utf-8")
    else print("Incorrect File Type")

    # # Display uploaded content (for debugging)
    # st.text_area("Uploaded Resume Content", value=resume_text, height=250)

    # Add resume content to chat history
    context_message = f"Resume:\n{resume_text}"
    if role_context:
        context_message += f"\nTarget Role/Industry: {role_context}"

    # Add system instruction as first message, then the resume content
    st.session_state.messages = [{"role": "system", "content": system_instruction}]
    st.session_state.messages.append({"role": "user", "content": f"Resume:\n{resume_text}"})

    # # Display user input in chat message container
    # with st.chat_message("user"):
    #     st.markdown("Uploaded resume for feedback.")
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with client.workers.ai.with_streaming_response.run(
            account_id=st.secrets["CLOUDFLARE_ACCOUNT_ID"],
            model_name="@cf/meta/llama-3.1-8b-instruct",
            messages=st.session_state.messages,
            stream=True,
        ) as response:
            # Create token iterator
            def iter_tokens(r):
                 for line in r.iter_lines():
                     if line.startswith("data: ") and not line.endswith("[DONE]"):
                         entry = json.loads(line.replace("data: ", ""))
                         yield entry["response"]

            # Display tokens in real-time
            assistant_reply = ""
            placeholder = st.empty()
            for token in iter_tokens(response):
                assistant_reply += token
                placeholder.markdown(assistant_reply)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # Accept user input in chat for follow-up questions or comments
    if prompt := st.chat_input("Ask for more specific feedback or provide more context:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with client.workers.ai.with_streaming_response.run(
                account_id=st.secrets["CLOUDFLARE_ACCOUNT_ID"],
                model_name="@cf/meta/llama-3.1-8b-instruct",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ) as response:
                completion = st.write_stream(iter_tokens(response))
        st.session_state.messages.append({"role": "assistant", "content": completion})
        st.session_state.messages.append({"role": "assistant", "content": completion})

# Previous code that takes in anything as a prompt
# if prompt := st.chat_input("What is up?"):
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     # Display user message in chat message container
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Display assistant response in chat message container
#     with st.chat_message("assistant"):
#         with client.workers.ai.with_streaming_response.run(
#             account_id=st.secrets["CLOUDFLARE_ACCOUNT_ID"],
#             model_name="@cf/meta/llama-3.1-8b-instruct",
#             messages=[
#                 {"role": m["role"], "content": m["content"]}
#                 for m in st.session_state.messages
#             ],
#             stream=True,
#         ) as response:
#             # The response is an EventSource object that looks like so
#             # data: {"response": "Hello "}
#             # data: {"response": ", "}
#             # data: {"response": "World!"}
#             # data: [DONE]
#             # Create a token iterator
#             def iter_tokens(r):
#                 for line in r.iter_lines():
#                     if line.startswith("data: ") and not line.endswith("[DONE]"):
#                         entry = json.loads(line.replace("data: ", ""))
#                         yield entry["response"]

#             completion = st.write_stream(iter_tokens(response))
