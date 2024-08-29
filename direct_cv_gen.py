import json
from docx_generator import generate_docx_cv
import streamlit as st # type: ignore
import anthropic # type: ignore
import os
from claude_utils import anthropic_models, TOOLS, UI_LLM_PROMPT
from utils_linux import convert_to_pdf, save_cv_data


def generate_cv(cv_data):
    # Save CV data
    json_filename = save_cv_data(cv_data)
    
    # Generate PDF CV
    filename = generate_docx_cv(cv_data)
    pdf_filename = convert_to_pdf(filename)
    
    st.session_state.cv_data = cv_data
    st.session_state.pdf_filename = pdf_filename
    
    return f"CV data saved to {json_filename} and PDF generated as {pdf_filename}"

def handle_tool_use(func_name, func_params):
    if func_name == "generate_cv":
        return generate_cv(func_params["cv_data"])
    else:
        return f"Unknown tool: {func_name}"
    

def get_message_content(message):
    content = message.get("content", "")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item.get("text", "")
        return content[0] if content else ""
    elif isinstance(content, dict):
        return content.get("text", json.dumps(content))
    return str(content)

def messages_to_anthropic(messages):
    return [
        {
            "role": message["role"],
            "content": get_message_content(message)
        }
        for message in messages
    ]

def stream_claude_response(model_params, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    response_message = ""
    current_tool_use = None
    partial_json = ""
    processing_message = st.empty()

    with client.messages.stream(
        model=model_params["model"],
        messages=messages_to_anthropic(st.session_state.messages),
        temperature=model_params["temperature"],
        max_tokens=2000,
        system=UI_LLM_PROMPT,
        tools=TOOLS,
    ) as stream:
        print("Stream opened")

        for event in stream:
            print(f"\nEvent type: {event.type}")
            
            if event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    current_tool_use = {"name": event.content_block.name, "parameters": {}}
                    print(f"Tool use started: {current_tool_use['name']}")
                    processing_message.info("Processing your information...")
            
            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    print(f"Text delta received: '{event.delta.text}'")
                    response_message += event.delta.text
                    yield event.delta.text
                elif event.delta.type == "input_json_delta" and current_tool_use:
                    print(f"Input JSON delta received: '{event.delta.partial_json}'")
                    partial_json += event.delta.partial_json
                    try:
                        current_tool_use["parameters"] = json.loads(partial_json)
                        print(f"Complete JSON parsed: {current_tool_use}")
                        partial_json = ""
                    except json.JSONDecodeError:
                        print(f"Incomplete JSON, accumulated so far: '{partial_json}'")
            
            elif event.type == "content_block_stop":
                print(f"Content block stopped: index={event.index}")
                if current_tool_use:
                    print(f"Executing tool: {current_tool_use['name']}")
                    processing_message.info(f"Finalizing your CV...")
                    result = handle_tool_use(current_tool_use['name'], current_tool_use['parameters'])
                    print(f"Tool execution result: {result}")
                    current_tool_use = None
                    partial_json = ""
                    processing_message.info(f"Finalizing your CV...")

            
            elif event.type == "message_stop":
                print(f"Message stopped: stop_reason={event.message.stop_reason}")
                processing_message.empty()
                break

    print("Stream ended")
    st.session_state.messages.append({
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": response_message,
        }]
    })
    return response_message

def main():
    st.set_page_config(page_title="Direct CV Generator Demo", layout="wide")
    st.title("Direct CV Generator Demo")

    # Sidebar for API key and model selection
    with st.sidebar:
        api_key = st.text_input("Enter your Anthropic API Key:", type="password")
        model = st.selectbox("Select Claude model:", anthropic_models)
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.1)


     # Use the entered API key if provided, otherwise use the default
    anthropic_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(get_message_content(message))

    # Chat input
    if prompt := st.chat_input("Let's create your CV!"):
        st.session_state.messages.append({
            "role": "user",
            "content": [{
                "type": "text",
                "text": prompt,
            }]
        })

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Get and display Claude's response
        with st.chat_message("assistant"):
            model_params = {
                "model": model,
                "temperature": temperature,
            }
            response_placeholder = st.empty()
            full_response = ""
            for response_chunk in stream_claude_response(model_params, anthropic_api_key):
                full_response += response_chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

    # Add a button to download the generated CV
    if 'pdf_filename' in st.session_state:
        with open(st.session_state.pdf_filename, "rb") as file:
            st.download_button(
                label="CV татах",
                data=file,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()