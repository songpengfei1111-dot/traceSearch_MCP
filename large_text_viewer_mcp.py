#!/usr/bin/env python3
"""Packaged, relocatable MCP adapter for the headless large-text runtime."""
import asyncio
import json
from pathlib import Path
import jsonschema
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from crypto_magic_search import search_all_crypto_magic, format_search_results
from runtime_support import get_runtime, RuntimeFailure

SERVER_NAME = "largeTextSearcher-server"
server = Server(SERVER_NAME)

def schema(properties, required):
    return {"type":"object", "properties":properties, "required":required, "additionalProperties":False}
FILE = {"type":"string", "minLength":1}
POSITIVE = {"type":"integer", "minimum":1, "maximum":9223372036854775807}
TOOLS = [
    types.Tool(name="runtime_health", description="Check packaged text-runtime capabilities and startup diagnostics; paths are opt-in.", inputSchema=schema({"include_paths":{"type":"boolean","default":False}},[])),
    types.Tool(name="file_info", description="获取文件的基本信息，如大小、估计行数和编码", inputSchema=schema({"file_path":FILE},["file_path"])),
    types.Tool(name="extract_lines", description="从文件中提取一基行号范围；支持大文件随机访问", inputSchema=schema({"file_path":FILE,"start":POSITIVE,"end":POSITIVE,"count":POSITIVE,"line_numbers":{"type":"boolean","default":True}},["file_path","start"])),
    types.Tool(name="search_text", description="在大文件中搜索文本或显式正则表达式，输出有界匹配及上下文", inputSchema=schema({"file_path":FILE,"pattern":{"type":"string","minLength":1},"context":{"type":"integer","minimum":0,"maximum":9223372036854775807},"regex":{"type":"boolean","default":False}},["file_path","pattern"])),
    types.Tool(name="search_crypto_magic", description="搜索已知加密常量；匹配是静态候选证据", inputSchema=schema({"file_path":FILE},["file_path"])),
]
DEFINITIONS = {tool.name:tool for tool in TOOLS}

@server.list_tools()
async def list_tools():
    return TOOLS

def dispatch(name, arguments):
    runtime = get_runtime()
    if name == "runtime_health":
        return runtime.health(arguments.get("include_paths",False))
    path = Path(arguments["file_path"])
    if not path.is_file():
        raise RuntimeFailure("file_unavailable", "The selected input is not a regular readable file")
    if name == "file_info":
        return runtime.execute(["info","--file",str(path)])
    if name == "extract_lines":
        command=["lines","--file",str(path),"--start",str(arguments["start"])]
        if "end" in arguments:
            if arguments["end"] < arguments["start"]:
                raise RuntimeFailure("invalid_range", "end must not precede start")
            command += ["--end",str(arguments["end"])]
        elif "count" in arguments:
            command += ["--count",str(arguments["count"])]
        if arguments.get("line_numbers",True):
            command += ["--line-numbers"]
        return runtime.execute(command)
    if name == "search_text":
        command=["search","--file",str(path),"--pattern",arguments["pattern"]]
        if arguments.get("regex",False):
            command += ["--regex"]
        if arguments.get("context",0):
            command += ["--context",str(arguments["context"])]
        return runtime.execute(command)
    if name == "search_crypto_magic":
        if runtime.failure:
            raise runtime.failure
        return format_search_results(search_all_crypto_magic(str(path)))
    raise RuntimeFailure("unknown_tool", "Unknown text tool")

def failure_result(failure):
    payload={"ok":False,"error":failure.payload}
    return types.ServerResult(types.CallToolResult(content=[types.TextContent(type="text",text=json.dumps(payload,ensure_ascii=False))],structuredContent=payload,isError=True))

async def call_tool_request(request):
    name=request.params.name
    arguments=request.params.arguments or {}
    tool=DEFINITIONS.get(name)
    if tool is None:
        return failure_result(RuntimeFailure("unknown_tool","Unknown text tool"))
    try:
        jsonschema.validate(arguments,tool.inputSchema)
    except jsonschema.ValidationError:
        return failure_result(RuntimeFailure("invalid_arguments","Tool arguments do not match the declared schema"))
    try:
        result=await asyncio.to_thread(dispatch,name,arguments)
        if isinstance(result,dict):
            return types.ServerResult(types.CallToolResult(content=[types.TextContent(type="text",text=json.dumps(result,ensure_ascii=False))],structuredContent=result,isError=False))
        return types.ServerResult(types.CallToolResult(content=[types.TextContent(type="text",text=result)],isError=False))
    except RuntimeFailure as failure:
        return failure_result(failure)
    except Exception:
        return failure_result(RuntimeFailure("tool_failed","The text request failed without a complete result"))

# SDK 1.12 normalizes iterable returns with isError=False. Register the public
# low-level request handler so structured failures retain their error status.
server.request_handlers[types.CallToolRequest]=call_tool_request

async def main():
    await asyncio.to_thread(get_runtime)
    async with stdio_server() as (read_stream,write_stream):
        await server.run(read_stream,write_stream,server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
