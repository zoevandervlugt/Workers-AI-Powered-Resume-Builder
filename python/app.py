# Heavily based on https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps

import PyPDF2
import json
import streamlit as st
from cloudflare import Cloudflare


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

    # # Display uploaded content (for debugging)
    # st.text_area("Uploaded Resume Content", value=resume_text, height=250)

    # Add resume content to chat history
    context_message = f"Resume:\n{resume_text}"
    if role_context:
        context_message += f"\nTarget Role/Industry: {role_context}"

    # Add user message to chat history
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