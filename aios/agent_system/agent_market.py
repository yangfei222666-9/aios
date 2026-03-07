import json
import requests
import os
from pathlib import Path
import argparse

# ============== Config (Already configured for you) ==============
CLAWDHUB_REPO = "yangfei222666-9/Repository-name-aios"
AGENTS_DIR = Path("agents")
GITHUB_API = f"https://api.github.com/repos/{CLAWDHUB_REPO}/contents/agents"
GITHUB_RAW = f"https://raw.githubusercontent.com/{CLAWDHUB_REPO}/main/agents/"
# =================================================================

AGENTS_DIR.mkdir(exist_ok=True)

def list_remote_agents():
    try:
        resp = requests.get(GITHUB_API, timeout=8)
        if resp.status_code == 200:
            files = [f["name"].replace(".json", "") for f in resp.json() if f["name"].endswith(".json")]
            print(f"ClawdHub Remote Market ({len(files)} Agents)")
            for i, name in enumerate(files, 1):
                print(f"  {i:2d}. {name}")
            return files
    except:
        pass
    
    demo = ["smart_researcher", "self_heal_agent", "monitor_master", "bigua_expander"]
    print("Demo Market (4 Agents)")
    for i, name in enumerate(demo, 1):
        print(f"  {i:2d}. {name}")
    return demo

def install_agent(agent_name: str):
    url = f"{GITHUB_RAW}{agent_name}.json"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            print(f"Error: Agent {agent_name} not found in ClawdHub (please upload first!)")
            return False
        
        agent_data = resp.json()
        save_path = AGENTS_DIR / f"{agent_name}.json"
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, ensure_ascii=False, indent=2)
        
        print(f"Success! {agent_name} installed to agents/{agent_name}.json")
        print(f"   Version: {agent_data.get('version', '1.0.0')}")
        print(f"   Capabilities: {', '.join(agent_data.get('capabilities', ['unknown']))}")
        return True
    except Exception as e:
        print(f"Error: Failed to install {agent_name}: {e}")
        return False

def search_agents(keyword: str):
    """Search agents by keyword in name or capabilities"""
    agents = list_remote_agents()
    
    # Filter by keyword
    matches = [a for a in agents if keyword.lower() in a.lower()]
    
    if not matches:
        print(f"\nNo agents found matching '{keyword}'")
        return []
    
    print(f"\nFound {len(matches)} agent(s) matching '{keyword}':")
    for i, name in enumerate(matches, 1):
        print(f"  {i}. {name}")
    
    return matches

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIOS Agent Market Remote Tool")
    parser.add_argument("action", choices=["list", "install", "search"], help="Action")
    parser.add_argument("arg", nargs="?", help="Argument")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_remote_agents()
    elif args.action == "install" and args.arg:
        install_agent(args.arg)
    elif args.action == "search" and args.arg:
        search_agents(args.arg)
    else:
        print("Usage: python agent_market.py list / install smart_researcher / search monitor")
