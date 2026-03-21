#!/usr/bin/env python3
"""
SDXL Base+Refiner Ratio Sweep — ComfyUI API Automation
========================================================
Systematically compares different Base:Refiner step split ratios.
Generates one image per ratio with identical seed/prompt, varying only the handoff point.

Usage:
    python3 sdxl_refiner_sweep.py --server http://127.0.0.1:8188 --output ./refiner_sweep_results/

Requires: requests, websocket-client
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

try:
    import websocket
except ImportError:
    print("pip install websocket-client")
    sys.exit(1)


# ─── Configuration ────────────────────────────────────────────

SEED = 777
TOTAL_STEPS = 50
CFG = 6.5
SAMPLER = "dpmpp_2m_sde"
SCHEDULER = "karras"
WIDTH = 832
HEIGHT = 1216

POSITIVE_PROMPT = "portrait of a young woman with freckles, natural lighting, shallow depth of field, 85mm lens, professional photography"
NEGATIVE_PROMPT = "blurry, deformed, ugly, oversaturated"

BASE_CHECKPOINT = "sd_xl_base_1.0.safetensors"
REFINER_CHECKPOINT = "sd_xl_refiner_1.0_0.9vae.safetensors"

REFINER_ASCORE_POS = 6.0
REFINER_ASCORE_NEG = 2.5

# Ratios to test: (name, base_end_step)
# base_end_step = where base stops, refiner starts
RATIOS = [
    ("100_base_only", 50),   # No refiner
    ("90_10", 45),           # 90% base, 10% refiner
    ("80_20", 40),           # Standard recommended
    ("70_30", 35),           # More refiner
    ("60_40", 30),           # Heavy refiner
]


def build_base_only_workflow():
    """Build a simple SDXL base-only workflow (no refiner)."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_CHECKPOINT}
        },
        "2": {
            "class_type": "CLIPTextEncodeSDXL",
            "inputs": {
                "clip": ["1", 1],
                "width": WIDTH, "height": HEIGHT,
                "crop_w": 0, "crop_h": 0,
                "target_width": WIDTH, "target_height": HEIGHT,
                "text_g": POSITIVE_PROMPT,
                "text_l": POSITIVE_PROMPT,
            }
        },
        "3": {
            "class_type": "CLIPTextEncodeSDXL",
            "inputs": {
                "clip": ["1", 1],
                "width": WIDTH, "height": HEIGHT,
                "crop_w": 0, "crop_h": 0,
                "target_width": WIDTH, "target_height": HEIGHT,
                "text_g": NEGATIVE_PROMPT,
                "text_l": NEGATIVE_PROMPT,
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": WIDTH, "height": HEIGHT, "batch_size": 1}
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": SEED,
                "control_after_generate": "fixed",
                "steps": TOTAL_STEPS,
                "cfg": CFG,
                "sampler_name": SAMPLER,
                "scheduler": SCHEDULER,
                "denoise": 1.0,
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]}
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"images": ["6", 0], "filename_prefix": "sweep_100_base_only"}
        },
    }


def build_refiner_workflow(name: str, base_end: int):
    """Build SDXL Base+Refiner workflow with given handoff point."""
    return {
        # Base checkpoint
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_CHECKPOINT}
        },
        # Refiner checkpoint
        "2": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": REFINER_CHECKPOINT}
        },
        # Base positive conditioning
        "10": {
            "class_type": "CLIPTextEncodeSDXL",
            "inputs": {
                "clip": ["1", 1],
                "width": WIDTH, "height": HEIGHT,
                "crop_w": 0, "crop_h": 0,
                "target_width": WIDTH, "target_height": HEIGHT,
                "text_g": POSITIVE_PROMPT,
                "text_l": POSITIVE_PROMPT,
            }
        },
        # Base negative conditioning
        "11": {
            "class_type": "CLIPTextEncodeSDXL",
            "inputs": {
                "clip": ["1", 1],
                "width": WIDTH, "height": HEIGHT,
                "crop_w": 0, "crop_h": 0,
                "target_width": WIDTH, "target_height": HEIGHT,
                "text_g": NEGATIVE_PROMPT,
                "text_l": NEGATIVE_PROMPT,
            }
        },
        # Refiner positive conditioning
        "12": {
            "class_type": "CLIPTextEncodeSDXLRefiner",
            "inputs": {
                "clip": ["2", 1],
                "ascore": REFINER_ASCORE_POS,
                "width": WIDTH, "height": HEIGHT,
                "text": POSITIVE_PROMPT,
            }
        },
        # Refiner negative conditioning
        "13": {
            "class_type": "CLIPTextEncodeSDXLRefiner",
            "inputs": {
                "clip": ["2", 1],
                "ascore": REFINER_ASCORE_NEG,
                "width": WIDTH, "height": HEIGHT,
                "text": NEGATIVE_PROMPT,
            }
        },
        # Empty latent
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": WIDTH, "height": HEIGHT, "batch_size": 1}
        },
        # Base KSampler (Advanced) — stops at base_end
        "20": {
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "model": ["1", 0],
                "positive": ["10", 0],
                "negative": ["11", 0],
                "latent_image": ["4", 0],
                "add_noise": "enable",
                "noise_seed": SEED,
                "steps": TOTAL_STEPS,
                "cfg": CFG,
                "sampler_name": SAMPLER,
                "scheduler": SCHEDULER,
                "start_at_step": 0,
                "end_at_step": base_end,
                "return_with_leftover_noise": "enable",
            }
        },
        # Refiner KSampler (Advanced) — starts from base_end
        "21": {
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "model": ["2", 0],
                "positive": ["12", 0],
                "negative": ["13", 0],
                "latent_image": ["20", 0],
                "add_noise": "disable",
                "noise_seed": SEED,
                "steps": TOTAL_STEPS,
                "cfg": CFG,
                "sampler_name": SAMPLER,
                "scheduler": SCHEDULER,
                "start_at_step": base_end,
                "end_at_step": TOTAL_STEPS,
                "return_with_leftover_noise": "disable",
            }
        },
        # Decode + Save
        "30": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["21", 0], "vae": ["1", 2]}
        },
        "31": {
            "class_type": "SaveImage",
            "inputs": {"images": ["30", 0], "filename_prefix": f"sweep_{name}"}
        },
    }


def queue_prompt(server: str, workflow: dict) -> str:
    """Queue a prompt and return the prompt_id."""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{server}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result["prompt_id"]


def wait_for_completion(server: str, prompt_id: str, timeout: int = 600):
    """Wait for prompt to complete via polling /history."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{server}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not complete in {timeout}s")


def download_image(server: str, filename: str, subfolder: str, output_dir: Path):
    """Download a generated image."""
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    url = f"{server}/view?{params}"
    output_path = output_dir / filename
    urllib.request.urlretrieve(url, str(output_path))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="SDXL Refiner Ratio Sweep")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--output", default="./refiner_sweep_results/")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    
    for name, base_end in RATIOS:
        print(f"\n{'='*60}")
        print(f"Running: {name} (base_end={base_end}, refiner_start={base_end})")
        print(f"{'='*60}")
        
        if base_end >= TOTAL_STEPS:
            workflow = build_base_only_workflow()
        else:
            workflow = build_refiner_workflow(name, base_end)
        
        try:
            t0 = time.time()
            prompt_id = queue_prompt(args.server, workflow)
            print(f"  Queued: {prompt_id}")
            
            history = wait_for_completion(args.server, prompt_id)
            elapsed = time.time() - t0
            print(f"  Completed in {elapsed:.1f}s")
            
            # Extract output images
            outputs = history.get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        path = download_image(
                            args.server, img["filename"], 
                            img.get("subfolder", ""), output_dir
                        )
                        print(f"  Saved: {path}")
            
            results.append({
                "name": name,
                "base_end": base_end,
                "refiner_steps": TOTAL_STEPS - base_end,
                "elapsed_seconds": round(elapsed, 1),
                "status": "success",
            })
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "name": name,
                "base_end": base_end,
                "status": "error",
                "error": str(e),
            })
    
    # Save summary
    summary_path = output_dir / "sweep_summary.json"
    with open(summary_path, "w") as f:
        json.dump({
            "config": {
                "seed": SEED,
                "steps": TOTAL_STEPS,
                "cfg": CFG,
                "sampler": SAMPLER,
                "scheduler": SCHEDULER,
                "resolution": f"{WIDTH}x{HEIGHT}",
                "positive_prompt": POSITIVE_PROMPT,
            },
            "results": results,
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Sweep complete! Summary saved to {summary_path}")
    print(f"{'='*60}")
    
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        time_str = f"{r.get('elapsed_seconds', '?')}s" if r["status"] == "success" else r.get("error", "")
        print(f"  {status} {r['name']:20s} base_end={r['base_end']:2d}  refiner={r.get('refiner_steps', '?'):>2}steps  {time_str}")


if __name__ == "__main__":
    main()
