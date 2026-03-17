#!/usr/bin/env python3
"""
ComfyUI Workflow Generator & Executor for RunningHub
=====================================================
Generates ComfyUI workflows from templates, submits to RunningHub, polls for results.

Usage:
  # Text to image
  python3 comfyui_workflow.py --template text2img --prompt "a cute puppy" --width 1024 --height 1024

  # Image to image
  python3 comfyui_workflow.py --template img2img --image ./photo.jpg --prompt "anime style"

  # Text to image with LoRA
  python3 comfyui_workflow.py --template text2img_lora --prompt "3D style panda" --lora "小猪佩奇.safetensors"

  # Image upscale
  python3 comfyui_workflow.py --template img2img_upscale --image ./photo.jpg --prompt "high quality"

  # Check account balance
  python3 comfyui_workflow.py --check

  # List templates
  python3 comfyui_workflow.py --list

  # Download output
  python3 comfyui_workflow.py --template text2img --prompt "sunset" --output ./result.png
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

MAX_POLL_SECONDS = 600
POLL_INTERVAL = 8


# ---------------------------------------------------------------------------
# Config & API Key
# ---------------------------------------------------------------------------

def load_templates() -> dict:
    with open(TEMPLATES_PATH) as f:
        return json.load(f)

def resolve_api_key() -> str:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if key:
        return key
    # Try personal-secrets.json
    secrets_path = Path.home() / ".openclaw" / "personal-secrets.json"
    if secrets_path.exists():
        with open(secrets_path) as f:
            data = json.load(f)
            key = data.get("RUNNINGHUB_API_KEY", "")
            if key:
                return key
    print("Error: RUNNINGHUB_API_KEY not found. Set env var or add to personal-secrets.json", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def curl_post(url: str, payload: dict, timeout: int = 60) -> dict:
    cmd = [
        "curl", "-s", "-S", "--fail-with-body", "--max-time", str(timeout),
        "-X", "POST", url,
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    return json.loads(result.stdout)

def curl_upload(url: str, api_key: str, file_path: str, timeout: int = 120) -> str:
    """Upload a file to RunningHub and return the uploaded filename."""
    cmd = [
        "curl", "-s", "-S", "--max-time", str(timeout),
        "-X", "POST", url,
        "-F", f"apiKey={api_key}",
        "-F", f"file=@{file_path}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Upload failed: {result.stderr}")
    data = json.loads(result.stdout)
    if data.get("code") != 0:
        raise RuntimeError(f"Upload error: {data.get('msg', 'unknown')}")
    filename = data.get("data", {}).get("fileName", "")
    if not filename:
        raise RuntimeError(f"Upload returned no fileName: {data}")
    return filename

def download_file(url: str, output_path: str) -> str:
    cmd = ["curl", "-s", "-S", "-L", "--max-time", "120", "-o", output_path, url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Download failed: {result.stderr}")
    return output_path


# ---------------------------------------------------------------------------
# Core workflow execution
# ---------------------------------------------------------------------------

def build_node_info_list(template: dict, args: dict, api_key: str, config: dict) -> list:
    """Build nodeInfoList from template definition and user args."""
    nodes = template["nodes"]
    node_info = []

    for param_name, node_def in nodes.items():
        node_id = node_def["nodeId"]
        field = node_def["field"]
        node_type = node_def.get("type", "text")

        # Check if user provided this param
        value = args.get(param_name)

        if value is None:
            # Use default if available
            if "default" in node_def:
                value = node_def["default"]
            else:
                continue

        # Handle image uploads
        if node_type == "image" and value:
            if value.startswith("http://") or value.startswith("https://"):
                # Download first, then upload
                tmp_path = f"/tmp/comfyui_input_{random.randint(10000, 99999)}.jpg"
                download_file(value, tmp_path)
                value = curl_upload(config["api"]["upload_url"], api_key, tmp_path)
                os.remove(tmp_path)
            else:
                # Local file - upload directly
                value = curl_upload(config["api"]["upload_url"], api_key, value)

        # Handle seed=-1 (random)
        if field == "seed" and (value == -1 or value == "-1"):
            value = random.randint(0, 2**53)

        node_info.append({
            "nodeId": str(node_id),
            "fieldName": field,
            "fieldValue": str(value)
        })

    return node_info


def submit_task(api_key: str, workflow_id: str, node_info_list: list, config: dict) -> str:
    """Submit task and return taskId."""
    payload = {
        "apiKey": api_key,
        "workflowId": workflow_id,
        "nodeInfoList": node_info_list
    }
    resp = curl_post(config["api"]["create_url"], payload)
    if resp.get("code") != 0:
        # Try with instanceType
        payload["instanceType"] = "plus"
        resp = curl_post(config["api"]["create_url"], payload)
    if resp.get("code") != 0:
        raise RuntimeError(f"Task submission failed: {resp}")
    task_id = resp.get("data", {}).get("taskId", "")
    if not task_id:
        raise RuntimeError(f"No taskId in response: {resp}")
    return task_id


def poll_task(api_key: str, task_id: str, config: dict) -> str:
    """Poll until SUCCESS/FAILED, return final status."""
    start = time.time()
    while time.time() - start < MAX_POLL_SECONDS:
        time.sleep(POLL_INTERVAL)
        resp = curl_post(config["api"]["status_url"], {"apiKey": api_key, "taskId": task_id})
        status = resp.get("data", "")
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] {status}", file=sys.stderr)
        if status in ("SUCCESS", "FAILED"):
            return status
    return "TIMEOUT"


def get_outputs(api_key: str, task_id: str, config: dict) -> list:
    """Get task output files."""
    resp = curl_post(config["api"]["outputs_url"], {"apiKey": api_key, "taskId": task_id})
    if resp.get("code") == 0:
        return resp.get("data", [])
    # If code != 0, check for failure reason
    if resp.get("code") == 805:
        reason = resp.get("data", {}).get("failedReason", {})
        raise RuntimeError(f"Task failed: {reason.get('exception_message', 'unknown')}")
    return []


def get_failure_reason(api_key: str, task_id: str, config: dict) -> str:
    """Get failure reason for a failed task."""
    resp = curl_post(config["api"]["outputs_url"], {"apiKey": api_key, "taskId": task_id})
    if resp.get("code") == 805:
        reason = resp.get("data", {}).get("failedReason", {})
        return reason.get("exception_message", "unknown error")
    return str(resp)


def check_account(api_key: str, config: dict):
    """Check account status."""
    resp = curl_post(config["api"]["account_url"], {"apiKey": api_key})
    if resp.get("code") == 0:
        d = resp["data"]
        print(f"Account Status:")
        print(f"  Balance: ${d.get('remainMoney', '?')} ({d.get('currency', '?')})")
        print(f"  Coins: {d.get('remainCoins', '?')}")
        print(f"  Running Tasks: {d.get('currentTaskCounts', '?')}")
        print(f"  API Type: {d.get('apiType', '?')}")
    else:
        print(f"Error: {resp}")


def run_workflow(template_name: str, params: dict, config: dict, output_path: str | None = None) -> dict:
    """
    Main entry point: run a workflow template with given parameters.
    Returns dict with status, outputs, and timing info.
    """
    api_key = resolve_api_key()

    if template_name not in config["templates"]:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(config['templates'].keys())}")

    template = config["templates"][template_name]

    # Validate required params
    for req in template.get("required", []):
        if req not in params or not params[req]:
            raise ValueError(f"Missing required parameter: {req}")

    print(f"🎯 Template: {template['name']} ({template_name})", file=sys.stderr)
    print(f"📋 WorkflowId: {template['workflowId']}", file=sys.stderr)

    # Build nodeInfoList
    node_info = build_node_info_list(template, params, api_key, config)
    print(f"🔧 Parameters: {len(node_info)} nodes", file=sys.stderr)
    for n in node_info:
        val_preview = str(n["fieldValue"])[:60]
        print(f"   [{n['nodeId']}] {n['fieldName']} = {val_preview}", file=sys.stderr)

    # Submit
    print(f"\n🚀 Submitting task...", file=sys.stderr)
    task_id = submit_task(api_key, template["workflowId"], node_info, config)
    print(f"📝 Task ID: {task_id}", file=sys.stderr)

    # Poll
    print(f"⏳ Waiting (typical: {template.get('typical_time', '30-60s')})...", file=sys.stderr)
    status = poll_task(api_key, task_id, config)

    result = {
        "status": status,
        "task_id": task_id,
        "template": template_name,
        "workflow_id": template["workflowId"],
        "outputs": []
    }

    if status == "SUCCESS":
        outputs = get_outputs(api_key, task_id, config)
        result["outputs"] = outputs
        print(f"\n✅ Success! {len(outputs)} output(s):", file=sys.stderr)
        for i, out in enumerate(outputs):
            url = out.get("fileUrl", "")
            ftype = out.get("fileType", "")
            cost_time = out.get("taskCostTime", "?")
            print(f"  [{i+1}] {ftype}: {url}", file=sys.stderr)
            print(f"      Time: {cost_time}s", file=sys.stderr)

            # Download if output_path given
            if output_path and i == 0:
                ext = ftype if ftype else "png"
                dl_path = output_path if output_path.endswith(f".{ext}") else f"{output_path}.{ext}"
                download_file(url, dl_path)
                result["downloaded"] = dl_path
                print(f"      Saved: {dl_path}", file=sys.stderr)

    elif status == "FAILED":
        reason = get_failure_reason(api_key, task_id, config)
        result["error"] = reason
        print(f"\n❌ Failed: {reason}", file=sys.stderr)

    else:
        result["error"] = "Timeout waiting for task"
        print(f"\n⏰ Timeout after {MAX_POLL_SECONDS}s", file=sys.stderr)

    # Output JSON to stdout for programmatic use
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    config = load_templates()

    parser = argparse.ArgumentParser(description="ComfyUI Workflow Generator & Executor")
    parser.add_argument("--template", "-t", help="Template name (text2img, img2img, etc.)")
    parser.add_argument("--prompt", "-p", help="Positive prompt text")
    parser.add_argument("--negative", "-n", help="Negative prompt")
    parser.add_argument("--image", "-i", help="Input image path or URL (for img2img)")
    parser.add_argument("--width", "-W", type=int, help="Width (text2img)")
    parser.add_argument("--height", "-H", type=int, help="Height (text2img)")
    parser.add_argument("--steps", type=int, help="Sampling steps")
    parser.add_argument("--cfg", type=float, help="CFG scale")
    parser.add_argument("--seed", type=int, help="Seed (-1 for random)")
    parser.add_argument("--denoise", type=float, help="Denoise strength (img2img)")
    parser.add_argument("--sampler", help="Sampler name")
    parser.add_argument("--scheduler", help="Scheduler name")
    parser.add_argument("--checkpoint", help="Checkpoint model name")
    parser.add_argument("--lora", help="LoRA model name")
    parser.add_argument("--lora-strength", type=float, help="LoRA strength")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--check", action="store_true", help="Check account status")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--json", action="store_true", help="Output only JSON (no stderr)")

    args = parser.parse_args()

    if args.check:
        check_account(resolve_api_key(), config)
        return

    if args.list:
        print("Available templates:")
        for name, tpl in config["templates"].items():
            req = ", ".join(tpl.get("required", []))
            print(f"  {name:20s} - {tpl['name']} (required: {req})")
        return

    if not args.template:
        parser.print_help()
        sys.exit(1)

    # Build params dict
    params = {}
    if args.prompt:
        params["positive_prompt"] = args.prompt
    if args.negative:
        params["negative_prompt"] = args.negative
    if args.image:
        params["input_image"] = args.image
    if args.width:
        params["width"] = args.width
    if args.height:
        params["height"] = args.height
    if args.steps:
        params["steps"] = args.steps
    if args.cfg is not None:
        params["cfg"] = args.cfg
    if args.seed is not None:
        params["seed"] = args.seed
    if args.denoise is not None:
        params["denoise"] = args.denoise
    if args.sampler:
        params["sampler"] = args.sampler
    if args.scheduler:
        params["scheduler"] = args.scheduler
    if args.checkpoint:
        params["checkpoint"] = args.checkpoint
    if args.lora:
        params["lora_name"] = args.lora
    if args.lora_strength is not None:
        params["lora_strength"] = args.lora_strength

    run_workflow(args.template, params, config, args.output)


if __name__ == "__main__":
    main()
