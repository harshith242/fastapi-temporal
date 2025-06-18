from temporalio import activity
import google.generativeai as genai
from typing import Dict, Any
import os
from dotenv import load_dotenv

@activity.defn
async def llm_call(prompt: str, history: list = None, user_id: str = None) -> Dict[str, Any]:
    """Call the LLM (Gemini) and process its response.
    
    Args:
        prompt: The prompt to send to the LLM
        history: Optional chat history
        
    Returns:
        dict: Dictionary containing the LLM response and any extracted actions
    """
    try:
        # Initialize the model
        load_dotenv() 
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Format the system prompt with history
        system_prompt = """You are an AI agent with access to a file writing tool. You can write content to text files when appropriate.
When a user asks you to write content to a file, you should:
1. Determine if using the write_to_file tool is appropriate
2. If yes, generate the content and use the tool to write it
3. If no, respond normally to the user's query.
4. NEVER RETURN ONLY THE TOOL CALL RESPONSE. MAKE SURE TO INCLUDE SOME GENERIC TEXT ON TOP OF THE TOOL CALL SO THAT IT CAN BE DISPLAYED TO THE USER.
5. IN CASE THE USER DOES NOT PROVIDE AND CONTENT TO BE WRITTEN INTO THE FILE, WRITE DIRECTLY WITH YOUR OWN THINKING BASED ON THE USER INSTRUCTIONS.
6. Let the Content that is being written into the text file not be displayed except in the tool_call part.

To use the tool, format your response like this:
tool_call_start
{{"filename": "example.txt", "content": "The content to write"}}
tool_call_end

Make sure to use the tool call format exactly as specified. NO EXTRA CHARACTERS OR SPACES EXACTLY AS SHOWN.

"""

        # Format the full prompt with history if provided
        formatted_history = ""
        if history:
            for msg in history:
                formatted_history += f"{msg['role']}: {msg['content']}\n"
        
        full_prompt = f"{system_prompt}\n\nPrevious conversation:\n{formatted_history}\n\nUser: {prompt}\nAssistant:"
        
        # Get response from the model
        response = model.generate_content(full_prompt)
        # Process the response to extract any tool calls
        response_text = response.text
        tool_call = None
        
        if "tool_call_start" in response_text:
            # Extract tool call JSON
            start_idx = response_text.find("tool_call_start") + len("tool_call_start")
            end_idx = response_text.find("tool_call_end")
            if end_idx > start_idx:
                try:
                    tool_call = response_text[start_idx:end_idx].strip()
                    
                except:
                    tool_call = None
        result = {
            "response": response_text,
            "tool_call": tool_call,
            "user_id": user_id
        }
        return result
        
    except Exception as e:
        raise 