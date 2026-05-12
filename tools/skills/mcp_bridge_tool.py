#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess

# Közvetlen stdio kliens a Python MCP SDK használatával
# pip install mcp
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_mcp_client(tool_name, args_dict):
    import shutil

    server_params = StdioServerParameters(
        command="ssh",
        args=[
            "-o", "StrictHostKeyChecking=no",
            f"misi@{os.environ.get('VPS_HOST', '5.189.163.88')}",
            "/home/misi/Jules_mx/venv/bin/python3",
            "/home/misi/Jules_mx/tools/skills/vps_mcp_server.py"
        ],
        env=os.environ.copy()
    )
    
    if os.environ.get("VPS_PWD"):
        if shutil.which("sshpass"):
            server_params.command = "sshpass"
            server_params.args = ["-p", os.environ.get("VPS_PWD"), "ssh"] + server_params.args
        else:
            print("⚠️ sshpass nem található, a jelszavas belépés nem fog működni! Próbálj kulcsot beállítani.", file=sys.stderr)

    elif os.environ.get("VPS_SSH_KEY"):
        with open("temp_mcp_key", "w") as f:
            f.write(os.environ.get("VPS_SSH_KEY") + "\n")
        os.chmod("temp_mcp_key", 0o600)
        server_params.args = ["-i", "temp_mcp_key"] + server_params.args

    print(f"🔗 Csatlakozás a VPS MCP Szerverhez hivatalos MCP SDK-val...", file=sys.stderr)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Meghívjuk a toolt
                result = await session.call_tool(tool_name, arguments=args_dict)

                outputs = []
                if hasattr(result, "content"):
                    for content in result.content:
                        if content.type == "text":
                            outputs.append(content.text)
                return "\n".join(outputs)
    finally:
        if os.path.exists("temp_mcp_key"):
            os.remove("temp_mcp_key")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Hasznalat: python3 mcp_bridge_tool.py <tool_neve> [arg1] [arg2] ... vagy --tool <tool> --args '<json>'")
        sys.exit(1)

    tool_name = ""
    args_dict = {}

    if sys.argv[1] == "--tool":
        # Régi, JSON args alapú hívás (agent_memory_manager így használja)
        parser = argparse.ArgumentParser(description="Jules Lokális MCP Kliens (Hivatalos SDK)")
        parser.add_argument("--tool", type=str, required=True, help="Az MCP tool neve")
        parser.add_argument("--args", type=str, required=True, help="JSON argumentumok")
        args = parser.parse_args()
        tool_name = args.tool
        try:
            args_dict = json.loads(args.args)
        except Exception as e:
            print(f"Érvénytelen JSON argumentum: {e}")
            sys.exit(1)
    else:
        # Új, primitív pozicionális parser (amit a rajtagok gyakran használnak)
        tool_name = sys.argv[1]
        if tool_name == 'execute_bash' and len(sys.argv) > 2:
             args_dict['command'] = sys.argv[2]
        elif tool_name == 'execute_python' and len(sys.argv) > 2:
             args_dict['code'] = sys.argv[2]
        elif tool_name == 'get_next_swarm_job' and len(sys.argv) > 2:
             args_dict['agent_id'] = sys.argv[2]
        elif tool_name == 'complete_swarm_job' and len(sys.argv) > 3:
             args_dict['job_id'] = int(sys.argv[2])
             args_dict['result'] = sys.argv[3]
        elif tool_name == 'search_rag_database' and len(sys.argv) > 3:
             args_dict['rag_name'] = sys.argv[2]
             args_dict['keyword'] = sys.argv[3]

    try:
        result = asyncio.run(run_mcp_client(tool_name, args_dict))
        print(result)
    except Exception as e:
        print(f"❌ Kliens hiba: {e}")