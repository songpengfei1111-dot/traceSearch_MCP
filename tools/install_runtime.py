"""Install a versioned package and atomically update only one Codex MCP entry."""
import argparse,copy,hashlib,json,os,re,shutil,sys,tempfile,tomllib,uuid
from pathlib import Path

def tree_identity(root):
    if root.is_symlink() or not root.is_dir():raise ValueError("Select a real package directory")
    result={}
    for file in sorted(root.rglob("*")):
        if file.is_symlink():raise ValueError("Package links are unsupported")
        if file.is_file():
            relative=file.relative_to(root)
            if "__pycache__" in relative.parts or file.suffix in (".pyc",".pyo"):continue
            with file.open("rb") as source:result[relative.as_posix()]=hashlib.file_digest(source,"sha256").hexdigest()
    return result

def validate_package(package,identity):
    required={"runtime.json","large_text_viewer_mcp.py","runtime_support.py","crypto_magic_search.py","requirements.txt","THIRD-PARTY-NOTICES.txt"}
    if not required.issubset(identity):raise ValueError("Select a complete runtime package")
    manifest=json.loads((package/"runtime.json").read_text(encoding="utf-8"))
    if not isinstance(manifest,dict) or manifest.get("schema")!=1 or manifest.get("protocol")!="large-text-cli-v1":raise ValueError("Unsupported runtime manifest")
    executable=manifest.get("executable")
    if not isinstance(executable,str):raise ValueError("Invalid runtime executable")
    relative=Path(executable)
    if relative.is_absolute() or len(relative.parts)!=2 or relative.parts[0]!="bin" or ".." in relative.parts:raise ValueError("Runtime executable must be in the package bin directory")
    digest=manifest.get("sha256")
    if not isinstance(digest,str) or not re.fullmatch(r"[a-fA-F0-9]{64}",digest) or identity.get(relative.as_posix())!=digest.lower():raise ValueError("Runtime executable failed integrity verification")

def update_config(config,server_name,entry_path):
    config=config.resolve();command=str(Path(sys.executable).resolve()).replace("\\","/")
    arguments=["-B","-X","utf8",str(entry_path).replace("\\","/")]
    for attempt in range(2):
        original=config.read_bytes();text=original.decode("utf-8");before=tomllib.loads(text)
        entry=before.get("mcp_servers",{}).get(server_name)
        if not isinstance(entry,dict):raise ValueError("Selected MCP entry does not exist")
        expected=copy.deepcopy(before);chosen=expected["mcp_servers"][server_name]
        chosen["command"]=command;chosen["args"]=arguments
        if isinstance(chosen.get("env"),dict):chosen["env"].pop("LARGE_TEXT_VIEWER_BIN",None)
        header=r"(?m)^\[mcp_servers\."+re.escape(server_name)+r"\]\r?\n"
        match=re.search(header,text)
        if not match:raise ValueError("Selected MCP entry header needs manual migration")
        start=match.end();next_header=re.search(r"(?m)^\[",text[start:]);end=start+next_header.start() if next_header else len(text)
        block=text[start:end]
        for key,value in [("command",command),("args",arguments)]:
            replacement=key+" = "+json.dumps(value,ensure_ascii=False)
            block,count=re.subn(r"(?m)^"+key+r"\s*=.*$",lambda _m:replacement,block)
            if count!=1:raise ValueError("Selected MCP command/args use an unsupported layout")
        updated=text[:start]+block+text[end:]
        env_header=r"(?m)^\[mcp_servers\."+re.escape(server_name)+r"\.env\]\r?\n"
        match=re.search(env_header,updated)
        if match:
            start=match.end();next_header=re.search(r"(?m)^\[",updated[start:]);end=start+next_header.start() if next_header else len(updated)
            block=re.sub(r"(?m)^LARGE_TEXT_VIEWER_BIN\s*=.*(?:\r?\n|$)","",updated[start:end])
            updated=updated[:start]+block+updated[end:]
        if tomllib.loads(updated)!=expected:raise ValueError("Config update would affect fields outside the selected MCP entry")
        if before==expected:return {"changed":False,"only_selected_entry":True,"concurrent_update_detection":"best_effort_before_replace"}
        backup=config.with_name(config.name+".before-large-text-"+uuid.uuid4().hex)
        with backup.open("xb") as output:output.write(original);output.flush();os.fsync(output.fileno())
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode="wb",dir=config.parent,prefix=".large-text-config-",delete=False) as output:
                temporary=Path(output.name);output.write(updated.encode("utf-8"));output.flush();os.fsync(output.fileno())
            if config.read_bytes()!=original:
                temporary.unlink();temporary=None
                continue
            os.replace(temporary,config);temporary=None
            actual=tomllib.loads(config.read_text(encoding="utf-8"))
            if actual.get("mcp_servers",{}).get(server_name)!=expected["mcp_servers"][server_name]:raise ValueError("Selected MCP entry changed after publication")
            return {"changed":True,"only_selected_entry":True,"backup":str(backup),"concurrent_update_retries":attempt,"concurrent_update_detection":"best_effort_before_replace"}
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)
    raise ValueError("Config changed concurrently; original updates were preserved")

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--package",type=Path,required=True);parser.add_argument("--install-root",type=Path,required=True);parser.add_argument("--version",required=True);parser.add_argument("--codex-config",type=Path);parser.add_argument("--server-name",default="large-text-searcher");parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}",args.version):raise ValueError("Invalid package version")
    package=args.package.resolve();expected=tree_identity(package)
    validate_package(package,expected)
    if args.install_root.resolve().is_relative_to(package):raise ValueError("Install root must be outside the source package")
    versions=args.install_root.absolute()/"versions";versions.mkdir(parents=True,exist_ok=True);destination=versions/args.version
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix=".large-text-install-",dir=versions) as temporary:
            staging=Path(temporary)/"package";shutil.copytree(package,staging,ignore=shutil.ignore_patterns("__pycache__","*.pyc","*.pyo"))
            if tree_identity(staging)!=expected:raise ValueError("Staged package differs from its source")
            staging.rename(destination)
    if tree_identity(destination)!=expected:raise ValueError("Existing installed version differs; select a new version")
    config_result=update_config(args.codex_config,args.server_name,destination/"large_text_viewer_mcp.py") if args.codex_config else None
    receipt={"installed":True,"package_path":str(destination),"source_package":str(package),"verified_files":len(expected),"config":config_result,"live_connection_verified":False,"other_servers_restarted":False}
    args.receipt.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8");print(json.dumps(receipt))
if __name__=="__main__":main()
