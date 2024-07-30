# This file was auto-generated by Fern from our API Definition.

import typing

from .entries_base_entry_content_item import EntriesBaseEntryContentItem
from .tools_chosen_tool_call import ToolsChosenToolCall
from .tools_tool import ToolsTool
from .tools_tool_response import ToolsToolResponse

EntriesBaseEntryContent = typing.Union[
    typing.List[EntriesBaseEntryContentItem],
    ToolsTool,
    ToolsChosenToolCall,
    str,
    ToolsToolResponse,
    typing.List[EntriesBaseEntryContentItem],
]