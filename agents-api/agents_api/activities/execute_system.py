import asyncio
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import Any
from uuid import UUID

from beartype import beartype
from box import Box, BoxList
from fastapi.background import BackgroundTasks
from temporalio import activity

from ..autogen.openapi_model import (
    ChatInput,
    CreateDocRequest,
    CreateSessionRequest,
    HybridDocSearchRequest,
    SystemDef,
    TextOnlyDocSearchRequest,
    UpdateSessionRequest,
    UpdateUserRequest,
    VectorDocSearchRequest,
)
from ..common.protocol.tasks import ExecutionInput, StepContext
from ..common.storage_handler import auto_blob_store, load_from_blob_store_if_remote
from ..env import testing
from ..models.developer import get_developer
from .utils import get_handler

# For running synchronous code in the background
process_pool_executor = ProcessPoolExecutor()


@auto_blob_store(deep=True)
@beartype
async def execute_system(
    context: StepContext,
    system: SystemDef,
) -> Any:
    """Execute a system call with the appropriate handler and transformed arguments."""
    arguments: dict[str, Any] = system.arguments or {}

    if set(arguments.keys()) == {"bucket", "key"}:
        arguments = await load_from_blob_store_if_remote(arguments)

    if not isinstance(context.execution_input, ExecutionInput):
        raise TypeError("Expected ExecutionInput type for context.execution_input")

    arguments["developer_id"] = context.execution_input.developer_id

    # Unbox all the arguments
    for key, value in arguments.items():
        if isinstance(value, Box):
            arguments[key] = value.to_dict()
        elif isinstance(value, BoxList):
            arguments[key] = value.to_list()

    # Convert all UUIDs to UUID objects
    uuid_fields = ["agent_id", "user_id", "task_id", "session_id", "doc_id"]
    for field in uuid_fields:
        if field in arguments:
            arguments[field] = UUID(arguments[field])

    try:
        handler = get_handler(system)

        # Transform arguments for doc-related operations (except create and search
        # as we're calling the endpoint function rather than the model method)
        if system.subresource == "doc" and system.operation not in ["create", "search"]:
            owner_id_field = f"{system.resource}_id"
            if owner_id_field in arguments:
                doc_args = {
                    "owner_type": system.resource,
                    "owner_id": arguments[owner_id_field],
                    **arguments,
                }
                doc_args.pop(owner_id_field)
                arguments = doc_args

        # Handle special cases for doc operations
        if system.operation == "create" and system.subresource == "doc":
            arguments["x_developer_id"] = arguments.pop("developer_id")
            bg_runner = BackgroundTasks()
            res = await handler(
                data=CreateDocRequest(**arguments.pop("data")),
                background_tasks=bg_runner,
                **arguments,
            )
            await bg_runner()
            return res

        # Handle search operations
        if system.operation == "search" and system.subresource == "doc":
            arguments["x_developer_id"] = arguments.pop("developer_id")
            search_params = _create_search_request(arguments)
            return await handler(search_params=search_params, **arguments)

        # Handle chat operations
        if system.operation == "chat" and system.resource == "session":
            developer = get_developer(developer_id=arguments.get("developer_id"))
            session_id = arguments.get("session_id")
            x_custom_api_key = arguments.get("x_custom_api_key", None)
            chat_input = ChatInput(**arguments)
            bg_runner = BackgroundTasks()
            res = await handler(
                developer=developer,
                session_id=session_id,
                background_tasks=bg_runner,
                x_custom_api_key=x_custom_api_key,
                chat_input=chat_input,
            )
            await bg_runner()
            return res

        # Handle create session
        if system.operation == "create" and system.resource == "session":
            developer_id = arguments.pop("developer_id")
            session_id = arguments.pop("session_id", None)
            create_session_request = CreateSessionRequest(**arguments)

            # In case sessions.create becomes asynchronous in the future
            if asyncio.iscoroutinefunction(handler):
                return await handler()

            # Run the synchronous function in another process
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                process_pool_executor,
                partial(
                    handler,
                    developer_id=developer_id,
                    session_id=session_id,
                    data=create_session_request,
                ),
            )

        # Handle update session
        if system.operation == "update" and system.resource == "session":
            developer_id = arguments.pop("developer_id")
            session_id = arguments.pop("session_id")
            update_session_request = UpdateSessionRequest(**arguments)

            # In case sessions.update becomes asynchronous in the future
            if asyncio.iscoroutinefunction(handler):
                return await handler()

            # Run the synchronous function in another process
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                process_pool_executor,
                partial(
                    handler,
                    developer_id=developer_id,
                    session_id=session_id,
                    data=update_session_request,
                ),
            )

        # Handle update user
        if system.operation == "update" and system.resource == "user":
            developer_id = arguments.pop("developer_id")
            user_id = arguments.pop("user_id")
            update_user_request = UpdateUserRequest(**arguments)

            # In case users.update becomes asynchronous in the future
            if asyncio.iscoroutinefunction(handler):
                return await handler()

            # Run the synchronous function in another process
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                process_pool_executor,
                partial(
                    handler,
                    developer_id=developer_id,
                    user_id=user_id,
                    data=update_user_request,
                ),
            )

        # Handle regular operations
        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)

        # Run the synchronous function in another process
        # FIXME: When the handler throws an exception, the process dies and the error is not captured. Instead it throws:
        # "concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending."
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            process_pool_executor, partial(handler, **arguments)
        )
    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_system_call: {e}")
        raise


def _create_search_request(arguments: dict) -> Any:
    """Create appropriate search request based on available parameters."""
    if "text" in arguments and "vector" in arguments:
        return HybridDocSearchRequest(
            text=arguments.pop("text"),
            mmr_strength=arguments.pop("mmr_strength", 0),
            vector=arguments.pop("vector"),
            alpha=arguments.pop("alpha", 0.75),
            confidence=arguments.pop("confidence", 0.5),
            limit=arguments.get("limit", 10),
        )
    elif "text" in arguments:
        return TextOnlyDocSearchRequest(
            text=arguments.pop("text"),
            mmr_strength=arguments.pop("mmr_strength", 0),
            limit=arguments.get("limit", 10),
        )
    elif "vector" in arguments:
        return VectorDocSearchRequest(
            vector=arguments.pop("vector"),
            mmr_strength=arguments.pop("mmr_strength", 0),
            confidence=arguments.pop("confidence", 0.7),
            limit=arguments.get("limit", 10),
        )


# Keep the existing mock and activity definition
mock_execute_system = execute_system

execute_system = activity.defn(name="execute_system")(
    execute_system if not testing else mock_execute_system
)
