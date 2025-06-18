import asyncio
import sys
from temporalio.client import Client
from temporalio.worker import Worker
from fast_temporal.config.config import TEMPORAL_CLIENT, TEMPORAL_TASK_QUEUE
from temporal_workflow import TestWorkflow
from concurrent.futures import ThreadPoolExecutor
from activities.write_txt_file import write_txt_file
from activities.text_to_speech import text_to_speech
from activities.llm_call import llm_call
# Worker setup and registration
async def run_worker():
    # Initialize client
    """
    Creates and runs a Temporal worker that:
    1. Connects to the Temporal server
    2. Registers the example workflow
    3. Registers the workflow's activities
    4. Starts processing workflow and activity tasks
    """
    client = await Client.connect("localhost:7233")
    
    # Create a worker:
    worker = Worker(
        client,
        task_queue="test-task-queue",
        workflows=[TestWorkflow],
        activities=[
            write_txt_file, 
            text_to_speech,
            llm_call,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=100),
    )
    
    print("Worker started. Press Ctrl+C to exit.")
    # Start worker
    await worker.run()

if __name__ == "__main__":
    print("Running in worker mode...")
    asyncio.run(run_worker()) 
