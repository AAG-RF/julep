# This file was auto-generated by Fern from our API Definition.

import typing

from .tasks_error_workflow_step import TasksErrorWorkflowStep
from .tasks_evaluate_step import TasksEvaluateStep
from .tasks_if_else_workflow_step import TasksIfElseWorkflowStep
from .tasks_prompt_step import TasksPromptStep
from .tasks_tool_call_step import TasksToolCallStep
from .tasks_yield_step import TasksYieldStep

TasksPatchTaskRequestMainItem = typing.Union[
    TasksEvaluateStep,
    TasksToolCallStep,
    TasksYieldStep,
    TasksPromptStep,
    TasksErrorWorkflowStep,
    TasksIfElseWorkflowStep,
]