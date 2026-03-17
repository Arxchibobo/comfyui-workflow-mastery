#!/usr/bin/env python3
"""
ComfyUI Custom Workflow Composer
=================================
Compose new workflows by modifying base templates' API format.
Supports: changing prompts, models, sizes, steps, and adding/removing nodes.

This is the "write your own workflow" capability.

Usage:
  # Compose from base template with modifications
  python3 workflow_composer.py --base text2img \
    --prompt "cyberpunk city at night" \
    --width 1024 --height 1024 --steps 25

  # Compose and execute
  python3 workflow_composer.py --base text2img \
    --prompt "anime girl" --execute

  # Save composed workflow to file
  python3 workflow_composer.py --base text2img \
    --prompt "landscape" --save /tmp/my_workflow.json
"""

from __future__ import annotations
import argparse
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
TEMPLATES_PATH = DATA_DIR / "templates.json"
TOKEN_PATH = Path("/tmp/rh_access_token.txt")
API_KEY = os.environ.get("RUNNINGHUB_API_KEY", "")
RH_BASE = "https://www.runninghub.ai"
RH_API = "https://www.runninghub.cn"
WORKSPACE_ID = "2033835239616811009"

# Base template IDs for API format extraction
BASE_TEMPLATES = {
    "text2img": "9999",
    "img2img": "9997",
    "text2img_lora": "9998",
    "img2img_lora": "9995",
    "img2img_upscale": "9996"
}


def resolve_api_key() -> str:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if key:
        return key
    secrets = Path.home() / ".openclaw" / "personal-secrets.json"
    if secrets.exists():
        with open(secrets) as f:
            key = json.load(f).get("RUNNINGHUB_API_KEY", "")
            if key:
                return key
    print("Error: RUNNINGHUB_API_KEY not found", file=sys.stderr)
    sys.exit(1)


def get_token() -> str:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()
    raise RuntimeError("No access token. Need to login via Playwright first.")


def get_base_api_format(token: str, template_id: str) -> dict:
    """Get the API format from an existing template."""
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{RH_BASE}/api/openapi/getJsonApiFormat',
        '-H', 'Content-Type: application/json',
        '-H', f'Authorization: Bearer {token}',
        '-d', json.dumps({"workflowId": template_id})
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    prompt_str = data.get('data', {}).get('prompt', '')
    if not prompt_str:
        raise RuntimeError(f"Template {template_id} has no API format")
    return json.loads(prompt_str) if isinstance(prompt_str, str) else prompt_str


def save_to_workspace(token: str, workspace_id: str, api_format: dict) -> bool:
    """Save API format to workspace for execution."""
    payload = {
        "workflowId": workspace_id,
        "workflowContent": "{}",  # Minimal UI (not needed for execution)
        "promptContent": json.dumps(api_format)
    }
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{RH_BASE}/api/workflow/setContent',
        '-H', 'Content-Type: application/json',
        '-H', f'Authorization: Bearer {token}',
        '-d', json.dumps(payload)
    ], capture_output=True, text=True)
    resp = json.loads(result.stdout)
    return resp.get("code") == 0


def submit_and_poll(api_key: str, workflow_id: str, node_info: list = None, timeout: int = 300) -> dict:
    """Submit task and poll for results."""
    payload = {"apiKey": api_key, "workflowId": workflow_id}
    if node_info:
        payload["nodeInfoList"] = node_info

    result = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/create',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ], capture_output=True, text=True)
    resp = json.loads(result.stdout)

    if resp.get("code") != 0:
        return {"status": "ERROR", "error": resp.get("msg", "unknown")}

    task_id = resp["data"]["taskId"]
    print(f"📝 Task: {task_id}", file=sys.stderr)

    start = time.time()
    while time.time() - start < timeout:
        time.sleep(8)
        sr = subprocess.run([
            'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/status',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({"apiKey": api_key, "taskId": task_id})
        ], capture_output=True, text=True)
        status = json.loads(sr.stdout).get("data", "")
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] {status}", file=sys.stderr)

        if status == "SUCCESS":
            or_ = subprocess.run([
                'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/outputs',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({"apiKey": api_key, "taskId": task_id})
            ], capture_output=True, text=True)
            outputs = json.loads(or_.stdout).get("data", [])
            return {"status": "SUCCESS", "task_id": task_id, "outputs": outputs}
        elif status == "FAILED":
            return {"status": "FAILED", "task_id": task_id}

    return {"status": "TIMEOUT", "task_id": task_id}


def compose_workflow(base_name: str, modifications: dict) -> dict:
    """
    Compose a new workflow by getting base API format and applying modifications.
    
    modifications can include:
    - positive_prompt: str
    - negative_prompt: str
    - width, height: int
    - steps, cfg: number
    - seed: int
    - sampler: str
    - scheduler: str
    - denoise: float
    - checkpoint: str
    """
    token = get_token()
    template_id = BASE_TEMPLATES.get(base_name)
    if not template_id:
        raise ValueError(f"Unknown base: {base_name}. Available: {list(BASE_TEMPLATES.keys())}")

    # Load templates config for node mapping
    with open(TEMPLATES_PATH) as f:
        config = json.load(f)
    template = config["templates"][base_name]

    # Get API format from RunningHub
    print(f"📥 Getting base API format from template {template_id}...", file=sys.stderr)
    api = get_base_api_format(token, template_id)
    print(f"✅ Got {len(api)} nodes", file=sys.stderr)

    # Apply modifications using node mapping
    nodes = template["nodes"]
    for param_name, value in modifications.items():
        if param_name in nodes:
            node_def = nodes[param_name]
            node_id = node_def["nodeId"]
            field = node_def["field"]
            if node_id in api and field in api[node_id].get("inputs", {}):
                api[node_id]["inputs"][field] = value
                print(f"  ✏️ [{node_id}].{field} = {str(value)[:60]}", file=sys.stderr)

    # Handle seed randomization
    for nid, node in api.items():
        if "seed" in node.get("inputs", {}):
            if modifications.get("seed", -1) == -1:
                node["inputs"]["seed"] = random.randint(0, 2**53)

    return api


def main():
    parser = argparse.ArgumentParser(description="Compose custom ComfyUI workflows")
    parser.add_argument("--base", "-b", required=True, help="Base template name")
    parser.add_argument("--prompt", "-p", help="Positive prompt")
    parser.add_argument("--negative", "-n", help="Negative prompt")
    parser.add_argument("--width", "-W", type=int, help="Width")
    parser.add_argument("--height", "-H", type=int, help="Height")
    parser.add_argument("--steps", type=int, help="Steps")
    parser.add_argument("--cfg", type=float, help="CFG")
    parser.add_argument("--seed", type=int, default=-1, help="Seed")
    parser.add_argument("--sampler", help="Sampler")
    parser.add_argument("--scheduler", help="Scheduler")
    parser.add_argument("--denoise", type=float, help="Denoise")
    parser.add_argument("--checkpoint", help="Checkpoint model")
    parser.add_argument("--save", help="Save composed workflow to file")
    parser.add_argument("--execute", action="store_true", help="Execute the workflow")
    parser.add_argument("--workspace", default=WORKSPACE_ID, help="Workspace ID for execution")
    args = parser.parse_args()

    mods = {}
    if args.prompt: mods["positive_prompt"] = args.prompt
    if args.negative: mods["negative_prompt"] = args.negative
    if args.width: mods["width"] = args.width
    if args.height: mods["height"] = args.height
    if args.steps: mods["steps"] = args.steps
    if args.cfg is not None: mods["cfg"] = args.cfg
    if args.seed is not None: mods["seed"] = args.seed
    if args.sampler: mods["sampler"] = args.sampler
    if args.scheduler: mods["scheduler"] = args.scheduler
    if args.denoise is not None: mods["denoise"] = args.denoise
    if args.checkpoint: mods["checkpoint"] = args.checkpoint

    api = compose_workflow(args.base, mods)

    if args.save:
        with open(args.save, 'w') as f:
            json.dump(api, f, indent=2)
        print(f"💾 Saved to {args.save}", file=sys.stderr)

    if args.execute:
        token = get_token()
        api_key = resolve_api_key()

        print(f"\n📝 Saving to workspace {args.workspace}...", file=sys.stderr)
        ok = save_to_workspace(token, args.workspace, api)
        if not ok:
            print("❌ Failed to save", file=sys.stderr)
            sys.exit(1)

        print(f"🚀 Executing...", file=sys.stderr)
        result = submit_and_poll(api_key, args.workspace)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Just output the composed API JSON
        print(json.dumps(api, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
