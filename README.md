# Fast Temporal

A Python package that provides a FastAPI application with WebSocket support for real-time communication with Temporal workflows. This package enables streaming updates from Temporal workflows to clients through WebSocket connections.

## Features

- FastAPI server with WebSocket support
- Real-time workflow status updates
- Generic Temporal workflow base class with activity scheduling functions and query handler.
- Environment-based configuration
- CORS support
- Structured logging

## Installation

```bash
pip install fast-temporal
```

## Configuration

Create a `.env` file in your project root with the following variables:

```env
TEMPORAL_CLIENT=localhost:7233
TEMPORAL_WORKFLOW=your_workflow_name
TEMPORAL_TASK_QUEUE=your_task_queue
START_SIGNAL_FUNCTION=your_signal_function
POLLING_INTERVAL=0.5
ALLOWED_ORIGINS=*
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_RELOAD=true
```

## Usage

### GenericTemporalWorkflow Class

The `GenericTemporalWorkflow` class provides a robust foundation for building Temporal workflows with built-in activity scheduling, state management, and real-time status updates. The current version only supports one workflow and task queue.

#### Key Functions

1. **Activity Scheduling**
   ```python
   async def schedule_activity(
       self,
       activity_name: str,
       callback: Optional[Callable] = None,
       args: List[Any] = None,
       kwargs: Dict[str, Any] = None,
       timeout: int = 60,
       retry_policy: Optional[RetryPolicy] = None
   ) -> Any
   ```
   - Schedules and executes a Temporal activity
   - Supports optional callback for result processing
   - Configurable timeout and retry policy
   - Returns activity result or None if failed

2. **Workflow Result Management**
   ```python
   def set_workflow_result(self, result: Any, status: str = "Done") -> None
   ```
   - Sets the final workflow result
   - Updates workflow status (default: "Done")
   - Triggers workflow completion
   - Sends final result through WebSocket

3. **Query Handlers**
   ```python
   @workflow.query
   async def get_current_activity(self) -> Dict[str, str]
   ```
   - Returns current activity name, status, and ID
   - Used for real-time status tracking
   - Format: `{"current_activity": name, "status": status, "activity_id": id}`

   ```python
   @workflow.query
   async def get_activity_result(self, activity_id: str) -> Any
   ```
   - Retrieves result of a completed activity
   - Used for accessing activity outputs
   - Returns None if activity not found

4. **State Management**
   ```python
   def set_state(self, key: str, value: Any) -> None
   def get_state(self, key: str, default: Any = None) -> Any
   ```
   - Stores and retrieves workflow state
   - Useful for sharing data between activities
   - Supports custom key-value pairs

#### Usage Example

```python
@workflow.defn
class MyWorkflow(GenericTemporalWorkflow):
    @workflow.run
    async def run(self, input_data: Dict[str, Any]):
        # Schedule an activity with callback
        result = await self.schedule_activity(
            "process_data",
            args=[input_data],
            callback=self.handle_result
        )
        return result

    async def handle_result(self, result):
        # Process activity result
        processed = do_something(result)
        # Set workflow result
        self.set_workflow_result(processed)
        return processed
```

### Starting the Server

After installation, you can start the FastAPI server using the provided script:

```bash
fast-temporal-run
```

Optional command-line arguments:
- `--host`: Server host (default: from .env)
- `--port`: Server port (default: from .env)
- `--reload`: Enable auto-reload (default: from .env)

Example:
```bash
fast-temporal-run --host 127.0.0.1 --port 8080 --reload
```

### WebSocket Communication

Connect to the WebSocket endpoint at `/ws/{user_id}` where `user_id` is a unique identifier for your client.

Example client connection:
```python
ws_url = f"ws://localhost:8000/ws/{user_id}"
async with websockets.connect(ws_url) as ws:
    data={"args": {"prompt": prompt, "user_id": user_id}, "origin": "streamlit_ui"}
    await ws.send(json.dumps(data))
    
    while True:
        response = await ws.recv()
        data = json.loads(response)
```

### Workflow Updates

The server will send real-time updates about workflow activities in the following format:
```json
{
    "origin": "temporal",
    "message": "activity_name: status",
    "status": "Running|Completed|Failed|Done"
}
```

### Final Response

The final response will be sent when the status becomes `Done`. `Done` indicates that the workflow is complete and will be set when the workflow result is set.

Therefore, the **workflow result** must be set using the `set_workflow_result` method, ideally in your CALLBACK functions of your final activity. This action sets the workflow result, marks the current status as `Done`, and completes the workflow.

Optionally, you can set the status as any other status using the `set_workflow_result(result,"Failed")`. 

The workflow will still be **completed** if you dont want retries. The example contains both the scenarios - Activity task failures that will fail the workflow and Activity task failure that are handled and won't fail the workflow.

The result of the final activity/callback (if a callback was defined), that was run will be sent through the websocket in the following JSON format:

```json
{
    "origin": "temporal",
    "message": final_activity_result/final_callback_result,
    "status": "Done"
}
```

## Example Application

The package includes an example application in the `examples/example_app` directory that demonstrates the integration of FastAPI, Temporal, and Streamlit. The example shows how to:

1. Define Temporal activities and workflows
2. Set up a Temporal worker
3. Create a FastAPI server with WebSocket support
4. Build a Streamlit UI that communicates with the workflow

In this example, we are taking in input from the user, where he uploads a txt file. Then according to user instructions, we generate the content by calling an LLM(Activity 1), write it into the text file (Activity 2), and create an audio file(Activity 3).

### Running the Example

1. Start the Temporal worker:
```bash
python examples/example_app/temporal_worker.py
```

2. Start the FastAPI server:
```bash
fast-temporal-run
```

3. Launch the Streamlit UI:
```bash
streamlit run examples/example_app/streamlit_ui.py
```

The example demonstrates:
- Real-time workflow status updates
- Activity scheduling and management
- WebSocket communication
- Streamlit UI integration

## Package Structure

```
fast_temporal/
├── fast_temporal/
│   ├── config/
│   ├── workflow/
│   └── api/
│
├── examples/
│   └── example_app/
│       └── activities/
│
├── pyproject.toml
└── README.md
```

### Key Components

1. **Config Module**
   - Environment variable management
   - Logger configuration
   - Configuration validation

2. **Workflow Module**
   - Generic Temporal workflow base class
   - Activity scheduling and management
   - State management
   - Error handling

3. **API Module**
   - FastAPI application setup
   - WebSocket connection management
   - Temporal client integration
   - Real-time status updates

## Dependencies

- fastapi
- uvicorn[standard]
- python-dotenv
- temporalio
- websockets

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
