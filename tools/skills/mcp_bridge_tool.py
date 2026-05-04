import subprocess
import sys
import json
import shlex

def run_mcp_tool(tool_name, tool_args):
    try:
        from vps_bridge import run_on_vps
    except ImportError:
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        try:
             from vps_bridge import run_on_vps
        except:
             return "Hiba: vps_bridge nem talalhato a Python path-ban."
             
    # A JSON payload escape-elése bash híváshoz, hogy a bonyolult stringek ne hasaljanak el.
    args_json = json.dumps(tool_args)
    safe_args = shlex.quote(args_json)
    
    # Invoke the mcp cli on the VPS
    cmd = f"mcp call {tool_name} --args {safe_args}"
    success, output = run_on_vps(cmd)
    
    return output

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
