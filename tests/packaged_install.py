"""Exercise real stdio MCP from a relocated package and an unrelated cwd."""
import argparse,asyncio,contextlib,hashlib,importlib.util,json,os,re,shutil,sys,tempfile,unittest.mock
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def session(package,env,fixture,mode):
    process_env=dict(os.environ)
    process_env.pop("LARGE_TEXT_VIEWER_BIN",None)
    process_env.update(env)
    async with stdio_client(StdioServerParameters(command=sys.executable,args=["-X","utf8",str(package/"large_text_viewer_mcp.py")],env=process_env,cwd=str(fixture.parent))) as streams:
        async with ClientSession(*streams) as client:
            await client.initialize()
            names={t.name for t in (await client.list_tools()).tools}
            assert {"runtime_health","file_info","extract_lines","search_text","search_crypto_magic"}.issubset(names)
            health=await client.call_tool("runtime_health",{})
            state=health.structuredContent
            if mode!="ready":
                assert not state["ready"],state
                result=await client.call_tool("extract_lines",{"file_path":str(fixture),"start":230,"end":342})
                assert result.isError and result.structuredContent["error"]["code"].startswith("runtime_"),result
                assert "D:/project/rust" not in result.model_dump_json() and "developer/old" not in result.model_dump_json()
                return {"mode":mode,"error":result.structuredContent["error"]["code"],"structured_error":True}
            assert state["ready"] and state["source"]=="bundled" and state["integrity_verified"],state
            path_health=(await client.call_tool("runtime_health",{"include_paths":True})).structuredContent
            assert Path(path_health["executable_path"]).parent==package/"bin"
            def text(value):
                assert not value.isError,value
                return "".join(item.text for item in value.content if item.type=="text")
            result=await client.call_tool("extract_lines",{"file_path":str(fixture),"start":230,"end":342,"count":1})
            lines=text(result).splitlines();assert len(lines)==113
            assert lines[0].strip()=="230 line 230: 自有测试😀" and lines[-1].strip()=="342 line 342: 自有测试😀"
            plain=text(await client.call_tool("extract_lines",{"file_path":str(fixture),"start":230,"count":113,"line_numbers":False})).splitlines()
            assert plain==[f"line {n}: 自有测试😀" for n in range(230,343)]
            eof=text(await client.call_tool("extract_lines",{"file_path":str(fixture),"start":350,"count":2})).splitlines();assert len(eof)==1 and eof[0].strip().startswith("350 ")
            text(await client.call_tool("file_info",{"file_path":str(fixture)}))
            search=text(await client.call_tool("search_text",{"file_path":str(fixture),"pattern":"line 23[0-2]:","regex":True}));assert "Found 3 matches" in search
            literal=text(await client.call_tool("search_text",{"file_path":str(fixture),"pattern":"never|matching"}));assert "Found 0 matches" in literal
            contextual=text(await client.call_tool("search_text",{"file_path":str(fixture),"pattern":"line 230:","context":1}));assert all(f"line {n}:" in contextual for n in [229,230,231])
            for arguments in [{"start":0},{"start":True},{"start":1,"count":0},{"start":10,"end":1}]:
                result=await client.call_tool("extract_lines",{"file_path":str(fixture),**arguments});assert result.isError and result.structuredContent["ok"] is False
            invalid=await client.call_tool("search_text",{"file_path":str(fixture),"pattern":"[","regex":True});assert invalid.isError and invalid.structuredContent["ok"] is False
            magic=fixture.parent/"magic.txt";magic.write_text("first\n9E3779B9\nlast\n",encoding="utf-8")
            hit=text(await client.call_tool("search_crypto_magic",{"file_path":str(magic)}));assert "line=2" in hit,hit
            no_hit=text(await client.call_tool("search_crypto_magic",{"file_path":str(fixture)}));assert no_hit=="no magicnum found"
            empty=fixture.parent/"empty.txt";empty.write_bytes(b"")
            assert "Size: 0 bytes" in text(await client.call_tool("file_info",{"file_path":str(empty)}))
            assert text(await client.call_tool("extract_lines",{"file_path":str(empty),"start":1}))==""
            large=fixture.parent/"long-line.txt";large.write_text("x"*300000,encoding="ascii")
            budget=await client.call_tool("extract_lines",{"file_path":str(large),"start":1});assert budget.isError and budget.structuredContent["error"]["code"]=="output_limit_exceeded"
            return {"mode":mode,"lines":len(lines),"unicode_exact":True,"eof_exact":True,"regex":True,"literal":True,"crypto_hit_and_no_hit":True,"structured_errors":True,"output_budget":True}

def malformed_probe_tests(root):
    spec=importlib.util.spec_from_file_location("runtime_probe_test",root/"runtime_support.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for payload in [b"[]",b"null",b"7",b'{"protocol":"large-text-cli-v1","commands":null}',b'{"protocol":"large-text-cli-v1","commands":7}']:
        with unittest.mock.patch.dict(os.environ,{"LARGE_TEXT_VIEWER_BIN":sys.executable},clear=False),unittest.mock.patch.object(module.subprocess,"run",return_value=module.subprocess.CompletedProcess([],0,payload,b"")):
            runtime=module.TextRuntime(root)
            assert runtime.failure.payload["code"]=="runtime_incompatible"
    return {"malformed_capabilities":5}

async def main():
    parser=argparse.ArgumentParser();parser.add_argument("--package",type=Path,required=True);parser.add_argument("--evidence",type=Path,required=True);args=parser.parse_args()
    args.evidence.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="relocated-text-",dir=args.evidence) as temporary:
        base=Path(temporary);moved=base/"搬迁 package";shutil.copytree(args.package,moved)
        fixture_dir=base/"unrelated cwd";fixture_dir.mkdir();fixture=fixture_dir/"owned-350.txt";fixture.write_text("".join(f"line {n}: 自有测试😀\n" for n in range(1,351)),encoding="utf-8")
        reports=[await session(moved,{},fixture,"ready")]
        missing=base/"missing";shutil.copytree(moved,missing);binary=missing/"bin"/json.loads((missing/"runtime.json").read_text())["executable"].split("/")[-1];binary.rename(binary.with_suffix(".absent"))
        reports.append(await session(missing,{},fixture,"missing"))
        reports.append(await session(moved,{"LARGE_TEXT_VIEWER_BIN":"D:/developer/old/target/release/not-installed.exe"},fixture,"stale_override"))
        tampered=base/"tampered";shutil.copytree(moved,tampered);binary=tampered/json.loads((tampered/"runtime.json").read_text())["executable"];data=bytearray(binary.read_bytes());data[0]^=1;binary.write_bytes(data)
        reports.append(await session(tampered,{},fixture,"tampered"))
        probe=malformed_probe_tests(moved)
    result={"passed":True,"cases":reports,"probe":probe,"real_stdio_mcp":True,"runtime_packaged":True,"developer_tree_read":False}
    (args.evidence/"RESULT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,ensure_ascii=True))
if __name__=="__main__":asyncio.run(main())
