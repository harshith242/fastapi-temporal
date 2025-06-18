# This workflow extends the GenericTemporalWorkflow class from the fast_temporal package
# It demonstrates how to create a custom workflow that inherits all the functionality
# of the base class while adding specific workflow logic

from fast_temporal.workflow.workflow import GenericTemporalWorkflow
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
    """Test workflow that takes in a prompt and writes it to a text file and creates an audio file."""

    """ Signal that will used to initiate the workflow. The function name here should be the same as the START_SIGNAL_FUNCTION in the .env file. """
    @workflow.signal
    async def handle_llm_request(self, input_data: Dict[str, Any]) -> None:
        """
        Signal handler for initiating the workflow with input data.
        
        Args:
            input_data (Dict[str, Any]): The input data containing prompt and user_id
        """
        # Schedule activity and get result
        # The schedule_activity function is used to schedule an activity.
        # The activity_name is the name of the activity to schedule.
        # The args are the arguments to pass to the activity.
        # The callback is the function to call when the activity is complete.
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
        # The run function is the entry point for the workflow.
        # The super().run() is used to call the run function of the base class and its result is returned.
        result = await super().run()
        return result