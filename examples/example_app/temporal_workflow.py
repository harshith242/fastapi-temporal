from fastapi_temporal.workflow.workflow import GenericTemporalWorkflow
from typing import Dict, Any, Set
from dataclasses import dataclass, field

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from activities.llm_call import llm_call
    from callbacks import callback_llm_response

@workflow.defn
class TestWorkflow(GenericTemporalWorkflow):
    """Test workflow that handles text file processing."""

    """ Siganl that will used to initiate the workflow """
    @workflow.signal
    async def handle_llm_request(self, input_data: Dict[str, Any]) -> None:
        """Handle an LLM request signal by scheduling the llm_call activity."""
        prompt = input_data["prompt"]
        user_id = input_data["user_id"]
        history = input_data.get("history")
        
        # Schedule activity and get result
        result = await self.schedule_activity(
            activity_name="llm_call",
            args=[prompt, history, user_id],
            callback=callback_llm_response
        )

    
    @workflow.run
    async def run(self):
        result = await super().run()
        return result