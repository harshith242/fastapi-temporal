from temporalio import activity
import os

@activity.defn
def write_txt_file(path: str, content: str, response_text: str, user_id: str) -> dict:
    """Read a text file and return its contents.
    
    Args:
        path: Path to the text file
        
    Returns:
        dict: Dictionary containing the file path and content
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            
        with open(path, "w") as f:
            f.write(content)
            print(f"Activity: Writing file {path}")
            print(f"Content:\n{content}")
            return {
                "path": path,
                "text": content,
                "response": response_text,
                "user_id": user_id
            }
    except Exception as e:
        print(f"Activity Error: {str(e)}")
        raise

def get_description() -> dict:
    """
    Returns the tool's description for the AI agent.
    """
    return {
        "name": "write_txt_file",
        "description": "Write content to a text file in the txtfiles directory",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to write to (will be saved in txtfiles directory)"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["filename", "content"]
        }
    }