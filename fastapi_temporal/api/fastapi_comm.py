# fastapi_comm.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import asyncio
from temporalio.client import Client
from fastapi.middleware.cors import CORSMiddleware
import uuid
import websockets
import json
from fastapi_temporal.config.config import TEMPORAL_CLIENT, TEMPORAL_WORKFLOW, TEMPORAL_TASK_QUEUE, START_SIGNAL_FUNCTION, get_logger,POLLING_INTERVAL,ALLOWED_ORIGINS
app = FastAPI()
logger = get_logger(__name__)
connected_websockets = set()
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Connection Manager ---
class ConnectionManager:
    """
    Manages active WebSocket connections for multiple users.

    Attributes:
        active_connections (Dict[str, WebSocket]):
            A dictionary mapping user IDs to their WebSocket connections.
    """
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the active connections.

        Args:
            user_id (str): The unique identifier for the user.
            websocket (WebSocket): The WebSocket connection instance.
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        """
        Removes a user's WebSocket connection from the active connections.

        Args:
            user_id (str): The unique identifier for the user.
        """
        self.active_connections.pop(user_id, None)
        
    async def send_to_user(self, user_id: str, message: str, status: str):
        """
        Sends a message to a specific user via their WebSocket connection.

        Args:
            user_id (str): The unique identifier for the user.
            message (str): The message to send.
            status (str): The status of the message or activity.
        """
        websocket = self.active_connections.get(user_id)
        if websocket:
            response={"origin": "temporal", "message": message, "status": status}
            await websocket.send_text(json.dumps(response))
        else:
            logger.error(f"No active WebSocket for user {user_id}")

manager = ConnectionManager()

async def get_or_create_workflow(workflow_id,args):
    """
    Retrieves an existing Temporal workflow by ID or creates a new one if it does not exist.

    Args:
        workflow_id (str): The unique identifier for the workflow.
        args (Any): Arguments to pass to the workflow SIGNAL which will trigger the workflow execution.

    Returns:
        handle: The workflow handle if successful, otherwise None.
    """
    client = await get_temporal_client()
    if not client:
        return None
    
    try:
        # Try to create a new workflow first
        handle = await client.start_workflow(
            TEMPORAL_WORKFLOW,
            id=workflow_id,
            task_queue=TEMPORAL_TASK_QUEUE,
            start_signal=START_SIGNAL_FUNCTION,
            start_signal_args=[args]
        )
        return handle
    except Exception as e:
        try:
            # If workflow already exists, try to get its handle
            handle = client.get_workflow_handle(workflow_id)
            return handle
        except Exception as e:
            return None

async def get_temporal_client():
    """
    Connects to the Temporal server and returns a client instance.

    Returns:
        Client: The Temporal client if connection is successful, otherwise None.
    """
    try:
        client = await Client.connect(TEMPORAL_CLIENT) 
        return client
    except Exception as e:
        logger.error(f"[Streamlit] Error connecting to Temporal server: {str(e)}")
        return None

async def poll_temporal(workflow_handle, user_id, polling_interval):
    """
    Polls the Temporal workflow by querying the get_activity_result query handler for activity status and sends updates to the user via WebSocket.
    It does the polling based on the value defined in .env file. Default is 0.5 seconds.
    In case the workflow is Done, it will fetch the Result of the last activity and send it to the user.
    Args:
        workflow_handle: The handle to the Temporal workflow.
        user_id (str): The unique identifier for the user to send updates to.
        polling_interval (float): The interval in seconds between polling attempts. Default is 0.5 seconds.
    """
    last_activity = None
    last_activity_status = None
    while True:
        current_activity_status = await workflow_handle.query("get_current_activity")
        if current_activity_status:
            logger.info(f"Current activity: {current_activity_status['current_activity']}")
            logger.info(f"Current activity status: {current_activity_status['status']}")
            if current_activity_status["status"] == "Done":
                result=await workflow_handle.query("get_activity_result", current_activity_status["activity_id"])
                await manager.send_to_user(user_id, result, "Done")
                break
            if current_activity_status["current_activity"] != last_activity or current_activity_status["status"] != last_activity_status:
                last_activity = current_activity_status["current_activity"]
                last_activity_status = current_activity_status["status"]
                await manager.send_to_user(user_id, current_activity_status["current_activity"] + ": " + current_activity_status["status"], current_activity_status["status"])
            
        else:
            await manager.send_to_user(user_id, "No activity", "Done")
        await asyncio.sleep(polling_interval)

# --- WebSocket Endpoint ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for handling real-time communication with clients.
    Accepts incoming WebSocket connections, listens for messages, and interacts with Temporal workflows.

    Args:
        websocket (WebSocket): The WebSocket connection instance.
        user_id (str): The unique identifier for the user.
    """
    await manager.connect(user_id, websocket)
    try:
        while True:
            data_raw = await websocket.receive_text()
            data = json.loads(data_raw)
            
            if data.get("origin") != "temporal":
                # Simulate signal to Temporal here
                logger.info("Sending signal to Temporal")
                workflow_id = str(uuid.uuid4())
                args=data.get("args")
                workflow_handle = await get_or_create_workflow(workflow_id,args)
                asyncio.create_task(poll_temporal(workflow_handle, user_id, POLLING_INTERVAL))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

