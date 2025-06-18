# FastAPI Temporal

A Python package that provides a FastAPI application with WebSocket support for real-time communication with Temporal workflows. This package enables streaming updates from Temporal workflows to clients through WebSocket connections.

## Features

- FastAPI server with WebSocket support
- Real-time workflow status updates
- Generic Temporal workflow base class
- Environment-based configuration
- CORS support
- Structured logging

## Installation

```bash
pip install .
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

### Starting the Server

After installation, you can start the FastAPI server using the provided script:

```bash
fastapi-temporal-run
```

Optional command-line arguments:
- `--host`: Server host (default: from .env)
- `--port`: Server port (default: from .env)
- `--reload`: Enable auto-reload (default: from .env)

Example:
```bash
fastapi-temporal-run --host 127.0.0.1 --port 8080 --reload
```

### WebSocket Communication

Connect to the WebSocket endpoint at `/ws/{user_id}` where `user_id` is a unique identifier for your client.

Example client connection:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Status: ${data.status}, Message: ${data.message}`);
};

// Send a message to start a workflow
ws.send(JSON.stringify({
    origin: "client",
    args: {
        // Your workflow arguments here
    }
}));
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

## Package Structure

```
fastapi-temporal/
├── fastapi_temporal/
│   ├── config/           # Configuration and logging
│   ├── workflow/         # Temporal workflow base class
│   └── api/             # FastAPI application and WebSocket handling
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

## License

This project is licensed under the MIT License - see the LICENSE file for details. 