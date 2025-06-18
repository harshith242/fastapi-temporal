import json
from typing import Any, Dict
from temporalio.common import datetime
from gtts import gTTS
import os
import streamlit as st
import json
import uuid
import asyncio

async def callback_text_to_speech(workflow, result: Any) -> None:
    """Handle the result of text-to-speech conversion.
    
    Args:
        workflow: The workflow instance
        result: Dictionary containing the audio file path
    """
    audio_path = result["audio_path"]
    response_text = result["response"]
    user_id = result["user_id"]
    response_text = response_text + "\n\n\nAudio file saved to " + audio_path
    # Here we are setting the workflow result. This will mark the current status as Done and complete the workflow.
    # The result here is the audio file path.
    workflow.set_workflow_result(audio_path)
    
    result["response"] = response_text
    # Here we are returning the result to the workflow. FastAPI will use this result as this is the final callback and send it to the client.
    return result

async def callback_write_txt_file(workflow, result: Any) -> None:
    """Handle the result of reading a text file by converting it to speech.
    
    Args:
        workflow: The workflow instance
        result: Dictionary containing the text file content
    """
    text = result["text"]
    response_text = result["response"]
    user_id = result["user_id"]
    
    await asyncio.sleep(3)
    # Schedule text-to-speech conversion
    audio_result = await workflow.schedule_activity(
        activity_name="text_to_speech",
        args=[text,response_text, user_id],
        callback=callback_text_to_speech
    )
    
async def callback_llm_response(workflow, result: Any) -> Dict[str, Any]:
    """Handle the result of an LLM call.
    
    Args:
        workflow: The workflow instance
        result: Dictionary containing the LLM response and any tool calls
        
    Returns:
        dict: The processed result containing response and any tool calls
    """
    user_id = result["user_id"]
    # Extract the text response without tool call if it exists
    response_text = result["response"]
    if "tool_call_start" in response_text:
        # If there's a tool call, extract just the text part before it
        tool_start = response_text.find("tool_call_start")
        if tool_start > 0:
            response_text = response_text[:tool_start].strip()
        
        try:
            # Clean up the JSON string by finding actual JSON object boundaries
            json_str = result["tool_call"]
            json_start = json_str.find("{")
            json_end = json_str.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = json_str[json_start:json_end]
                tool_data = json.loads(json_str)
                if "filename" in tool_data and "content" in tool_data:
                    # Ensure the file path is in the txtfiles directory
                    filename = tool_data["filename"]+"_"+user_id
                    
                if not filename.startswith("txtfiles/"):
                    filename = os.path.join("txtfiles", filename)
                
                response_text = response_text + "\n "+tool_data["content"]
                # Schedule file writing activity - don't set workflow result yet
                await workflow.schedule_activity(
                    activity_name="write_txt_file",
                    args=[filename, tool_data["content"],response_text, user_id],
                    callback=callback_write_txt_file
                )
            return result  # Return full result for state tracking
        except json.JSONDecodeError as e:
            # Setting the workflow to Failed as the tool call parsing failed.
            workflow.set_workflow_result(response_text, status="Failed")  # Set result if tool call parsing fails
            # This will still complete the workflow, but the final status will be Failed.
            return result
    else:
        # No tool call, set the workflow result immediately
        workflow.set_workflow_result(response_text)
        return result

