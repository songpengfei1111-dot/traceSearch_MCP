"""Create a new relocatable MCP package from an explicitly selected CLI binary."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path

FILES=("large_text_viewer_mcp.py","runtime_support.py","crypto_magic_search.py","requirements.txt","README-runtime.md","THIRD-PARTY-NOTICES.txt")

def package(runtime:Path,output:Path)->dict:
    root=Path(__file__).resolve().parents[1]
    runtime=runtime.resolve();output=output.absolute()
    if output.exists():raise ValueError("Package output already exists")
    if not runtime.is_file():raise ValueError("Select a compiled headless runtime")
    probe=subprocess.run([str(runtime),"--capabilities"],capture_output=True,timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    info=json.loads(probe.stdout.decode("utf-8"))
    if probe.returncode or info.get("protocol")!="large-text-cli-v1":raise ValueError("Selected runtime protocol is incompatible")
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".text-package-",dir=output.parent) as temporary:
        staging=Path(temporary)/"package";staging.mkdir()
        for name in FILES:shutil.copyfile(root/name,staging/name)
        (staging/"bin").mkdir()
        name="large-text-viewer-cli.exe" if os.name=="nt" else "large-text-viewer-cli"
        shutil.copy2(runtime,staging/"bin"/name)
        with runtime.open("rb") as binary:digest=hashlib.file_digest(binary,"sha256").hexdigest()
        manifest={"schema":1,"protocol":"large-text-cli-v1","version":info["version"],"executable":"bin/"+name,"sha256":digest}
        (staging/"runtime.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
        staging.rename(output)
    return {"created":True,"directory":str(output),"protocol":manifest["protocol"],"version":manifest["version"]}

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--runtime",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();print(json.dumps(package(args.runtime,args.output)))
if __name__=="__main__":main()
