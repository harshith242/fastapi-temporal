# workflow.py
from datetime import timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from temporalio import workflow
from temporalio.common import RetryPolicy
from fast_temporal.config.config import get_logger

logger = get_logger(__name__)

class GenericTemporalWorkflow:
    """
    GenericTemporalWorkflow provides a high-level, reusable base class for building Temporal workflows in Python.

    This class simplifies the management of workflow state, activity scheduling, and result handling. It is designed to be subclassed or used directly for workflows that require dynamic activity execution, custom state management, and robust error handling.

    Attributes:
        workflow_id (str): The unique identifier for the workflow instance.
        _activity_queue (list): Internal queue for scheduled activities.
        _current_activity (str): The name of the currently running activity.
        _current_activity_status (str): The status of the current activity (e.g., 'Running', 'Completed', 'Failed', 'Done').
        _current_activity_id (str): The unique identifier for the current activity.
        _active_activities (dict): Tracks currently active activities by their IDs.
        _completed_activities (dict): Tracks completed activities by their IDs.
        _workflow_result (Any): The final result of the workflow, if set.
        _state (dict): Custom state storage for arbitrary workflow data and activity results.
        _complete_workflow (bool): Whether the workflow should complete after the next activity result is set.
    """
    
    def __init__(self):
        """
        Initialize a new GenericTemporalWorkflow instance.
        Sets up internal state, activity tracking, and workflow metadata.
        """
        self.workflow_id = workflow.info().workflow_id
        
        #queues for activities and child workflows
        self._activity_queue = []
        
        # Current activity being executed
        self._current_activity = None
        self._current_activity_status = None
        self._current_activity_id = None
        # Active task tracking
        self._active_activities = {}
        self._completed_activities = {}
        
        # Result storage
        self._workflow_result = None
        
        # Custom state storage
        self._state = {}
 
        #Complete workflow if all tasks are completed
        self._complete_workflow = False

    def set_state(self, key: str, value: Any) -> None:
        """
        Store a custom key-value pair in the workflow's state.

        Args:
            key (str): The key under which to store the value.
            value (Any): The value to store.
        """
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the workflow's custom state storage.

        Args:
            key (str): The key to look up.
            default (Any, optional): The value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the key, or the default if not found.
        """
        return self._state.get(key, default)

    def set_complete_workflow(self, value: bool) -> None:
        """
        Set whether the workflow should complete after the next activity result is set.

        Args:
            value (bool): True to complete the workflow, False to continue processing.
        """
        self._complete_workflow = value

    def get_complete_workflow(self) -> bool:
        """
        Check whether the workflow is set to complete after the next activity result.

        Returns:
            bool: True if the workflow should complete, False otherwise.
        """
        return self._complete_workflow

    async def schedule_activity(
        self,
        activity_name: str,
        callback: Optional[Callable] = None,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        timeout: int = 60,
        retry_policy: Optional[RetryPolicy] = None
    ) -> Any:
        """
        Schedule and execute a Temporal activity within the workflow.

        This method starts the specified activity immediately, tracks its status, and optionally processes its result with a callback. Results and errors are stored in the workflow's state for later retrieval.

        Args:
            activity_name (str): The name of the activity to execute (must be registered with Temporal).
            callback (Callable, optional): An async function to process the activity result. Receives (self, result) as arguments.
            args (List[Any], optional): Positional arguments to pass to the activity. Defaults to None.
            kwargs (Dict[str, Any], optional): Keyword arguments to pass to the activity. Defaults to None.
            timeout (int, optional): Timeout for the activity in seconds. Defaults to 60.
            retry_policy (RetryPolicy, optional): Custom retry policy for the activity. Defaults to one attempt.

        Returns:
            Any: The result of the activity, possibly processed by the callback, or None if the activity failed.
        """
        activity_id = f"{activity_name}_{workflow.info().workflow_id}_{len(self._activity_queue)}"
        logger.info(f"Scheduling activity: {activity_id}")
        if activity_id not in self._active_activities and activity_id not in self._completed_activities:
            self._active_activities[activity_id] = activity_name
            # Start the activity immediately
            activity_handle = workflow.start_activity(
                activity_name,
                args=args or [],
                **kwargs or {},
                start_to_close_timeout=timedelta(seconds=timeout),
                retry_policy=retry_policy or RetryPolicy(maximum_attempts=1)
            )
            self._current_activity = activity_name
            self._current_activity_status = "Running"
            self._current_activity_id = activity_id
            # Wait for activity to complete
            try:
                result = await activity_handle
                self._completed_activities[activity_id] = activity_name
                del self._active_activities[activity_id]
                self._state[activity_id] = result
                self._current_activity_status = "Completed"
                
                if callback:
                    # Process result through callback
                    result_callback = await callback(self, result)
                self._state[activity_id + str("_callback")] = result_callback
                # Store result in state
                #if not self._active_activities:
                #    self.set_workflow_result(result)
                print(self._state)
                if self._complete_workflow:
                    self.set_workflow_result(result)
                return result
            except Exception as e:
                logger.error(f"Activity error for {activity_id}: {str(e)}")
                await self._handle_activity_error(e, activity_id)
                self._current_activity_status = "Failed"
                return None
        else:
            logger.info(f"Activity {activity_id} already completed or active")

    def set_workflow_result(self, result: Any, status: str = "Done") -> None:
        """
        Set the final result of the workflow and mark it as done.

        Args:
            result (Any): The result to store as the workflow's output.
            status (str, optional): The status to mark the workflow as. Defaults to "Done".
        """
        self._current_activity_status = "Done"
        self._workflow_result = result
        
    async def _handle_activity_error(self, error: Exception, activity_id: str) -> None:
        """
        Handle errors that occur during activity execution.

        This method is intended to be overridden in subclasses to provide custom error handling logic (e.g., logging, compensation, retries).

        Args:
            error (Exception): The exception that was raised.
            activity_id (str): The ID of the activity that failed.
        """
        pass
    
    @workflow.query
    async def get_current_activity(self) -> str:
        """
        Query handler: Get the current activity's name, status, and ID.

        Returns:
            dict: A dictionary with keys 'current_activity', 'status', and 'activity_id'.
        """
        return {"current_activity": self._current_activity, "status": self._current_activity_status, "activity_id": self._current_activity_id}

    @workflow.query
    async def get_activity_result(self, activity_id: str) -> Any:
        """
        Query handler: Retrieve the result of a completed activity by its ID.

        Args:
            activity_id (str): The unique identifier of the activity.

        Returns:
            Any: The result of the activity, or None if not found.
        """
        return self._state.get(activity_id, None)
    
    @workflow.query
    async def get_callback_result(self, activity_id: str) -> Any:
        """
        Query handler: Retrieve the result of a completed callback by its activity ID.

        Args:
            activity_id (str): The unique identifier of the activity.

        Returns:
            Any: The result of the callback, or None if not found.
        """
        callback_id=activity_id + str("_callback")
        return self._state.get(callback_id, None)

    @workflow.run
    async def run(self, *args, **kwargs) -> Any:
        """
        Main workflow execution loop.

        This method is the entry point for the workflow. It waits for the workflow result to be set (typically by activities or callbacks) and then returns it, completing the workflow.
        It waits for all the signal/update handlers to be completed.

        Args:
            *args: Positional arguments passed to the workflow.
            **kwargs: Keyword arguments passed to the workflow.

        Returns:
            Any: The final result of the workflow, as set by set_workflow_result().
        """
        while True:
            await workflow.wait_condition(lambda: bool(self._workflow_result) and workflow.all_handlers_finished())
            logger.info("Workflow result: " + str(self._workflow_result))
            if self._workflow_result is not None:
                return self._workflow_result 