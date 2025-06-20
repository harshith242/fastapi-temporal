# This Streamlit UI demonstrates how to:
# 1. Connect to the FastAPI WebSocket endpoint
# 2. Send workflow requests
# 3. Receive real-time updates about workflow progress
# 4. Display the results to the user

import streamlit as st
import uuid
import os
import asyncio
import websockets
import json
import asyncio

# Set page configuration
st.set_page_config(
    page_title="Simple AI Chatbot",
    layout="centered"
)

# Title
st.title("💬 Simple AI Chatbot")
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

user_id = st.session_state["user_id"]
st.write(f"Your session user ID: {user_id}")
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Get user input
if prompt := st.chat_input("Enter your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Sending and receiving messages from the temporal workflow through FastAPI websockets.
    async def send_message():
        try:
            # Each open session has a unique user ID. The user ID is used to identify the user in the temporal workflow.
            ws_url = f"ws://localhost:8000/ws/{user_id}"
            async with websockets.connect(ws_url) as ws:
                # Send the workflow request
                data = {
                    "args": {"prompt": prompt, "user_id": user_id},
                    "origin": "streamlit_ui",
                    "workflow":{"workflow_name":"TestWorkflow", "workflow_task_queue":"test-task-queue","start_signal_function":"handle_llm_request"}
                }
                await ws.send(json.dumps(data))
                
                # Receive and process updates
                while True:
                    response = await ws.recv()
                    data = json.loads(response)
                    # If the status is not Done, we are streaming the response
                    if data["status"] !="Done":
                        st.session_state.messages.append({"role": "assistant", "content": data["message"],"completed": False})
                        response_placeholder = st.empty()
                        streamed_response = ""
                        with response_placeholder:
                            for char in data["message"]:
                                streamed_response += char
                                response_placeholder.write(streamed_response, unsafe_allow_html=True)
                                await asyncio.sleep(0.025)
                            await asyncio.sleep(0.5)
                    else:
                        # If the status is Done, we are displaying the final response from the final activity.
                        response=data.get("message").get("response")
                        st.session_state.messages.append({"role": "assistant", "content": response,"completed": True})
                        st.session_state.messages  = [entry for entry in st.session_state.messages if entry.get("role") == "user" or (entry.get("role") == "assistant" and entry.get("completed") is not False)]
                        st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    asyncio.run(send_message())
    # Display assistant message
    

    
# Sidebar: File Upload & File Browser
with st.sidebar:
    st.title("📁 File Upload")
    uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "doc", "docx"])

    if uploaded_file:
        file_name = uploaded_file.name + "_" + user_id
        save_path = os.path.join("txtfiles", file_name)
        os.makedirs("txtfiles", exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File saved to: {save_path}")
        st.session_state.current_file = file_name

    st.markdown("---")
    st.subheader("📄 Uploaded Files:")
    files = os.listdir("txtfiles") if os.path.exists("txtfiles") else []
    for file in files:
        st.write(f"- {file}")

# Footer
st.markdown("---")
st.markdown("🧠 Powered by Streamlit · Chat session persists until refresh")
