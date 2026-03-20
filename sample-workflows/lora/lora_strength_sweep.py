#!/usr/bin/env python3
"""
LoRA Strength Sweep — ComfyUI API 批量实验脚本

通过 API 自动化运行 LoRA strength 对比实验，收集不同参数组合下的生成结果。
支持两种模式：
1. strength_model 单变量扫描
2. strength_model × strength_clip 网格扫描

用法：
    python lora_strength_sweep.py --mode single --lora style_lora.safetensors
    python lora_strength_sweep.py --mode grid --lora style_lora.safetensors
"""

import json
import urllib.request
import urllib.parse
import os
import sys
import time
import argparse
from pathlib import Path
from itertools import product

# ComfyUI API 配置
COMFY_API = os.getenv("COMFY_API", "http://127.0.0.1:8188")

def build_workflow(
    checkpoint: str,
    lora_name: str,
    strength_model: float,
    strength_clip: float,
    prompt: str,
    negative: str,
    seed: int = 42,
    steps: int = 25,
    cfg: float = 7.0,
    width: int = 512,
    height: int = 768,
    sampler: str = "dpmpp_2m",
    scheduler: str = "karras",
    filename_prefix: str = "sweep"
) -> dict:
    """构建带 LoRA 的完整 API 工作流 JSON"""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint}
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": lora_name,
                "strength_model": strength_model,
                "strength_clip": strength_clip
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 1],
                "text": prompt
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 1],
                "text": negative
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "control_after_generate": "fixed",
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["1", 2]
            }
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": filename_prefix
            }
        }
    }


def queue_prompt(workflow: dict) -> dict:
    """向 ComfyUI 发送生成请求"""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_API}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def wait_for_completion(prompt_id: str, timeout: int = 300):
    """等待生成完成"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_API}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not complete within {timeout}s")


def run_single_sweep(args):
    """模式1: strength_model 单变量扫描"""
    strengths = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5]
    
    print(f"=== LoRA Strength Single Sweep ===")
    print(f"LoRA: {args.lora}")
    print(f"Strengths: {strengths}")
    print(f"Fixed seed: {args.seed}\n")
    
    results = []
    for s in strengths:
        prefix = f"lora_sweep_m{s:.1f}_c{s:.1f}"
        workflow = build_workflow(
            checkpoint=args.checkpoint,
            lora_name=args.lora,
            strength_model=s,
            strength_clip=s,  # model == clip in single mode
            prompt=args.prompt,
            negative=args.negative,
            seed=args.seed,
            filename_prefix=prefix
        )
        
        print(f"Queuing: strength={s:.1f} ...", end=" ", flush=True)
        try:
            resp = queue_prompt(workflow)
            prompt_id = resp["prompt_id"]
            result = wait_for_completion(prompt_id)
            print(f"✅ Done (prompt_id={prompt_id[:8]})")
            results.append({"strength": s, "prompt_id": prompt_id, "status": "ok"})
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"strength": s, "status": "error", "error": str(e)})
    
    return results


def run_grid_sweep(args):
    """模式2: strength_model × strength_clip 网格扫描"""
    model_strengths = [0.3, 0.7, 1.0]
    clip_strengths = [0.3, 0.7, 1.0]
    
    print(f"=== LoRA Model×CLIP Grid Sweep ===")
    print(f"LoRA: {args.lora}")
    print(f"Model strengths: {model_strengths}")
    print(f"CLIP strengths: {clip_strengths}")
    print(f"Total: {len(model_strengths) * len(clip_strengths)} combinations\n")
    
    results = []
    for sm, sc in product(model_strengths, clip_strengths):
        prefix = f"lora_grid_M{sm:.1f}_C{sc:.1f}"
        workflow = build_workflow(
            checkpoint=args.checkpoint,
            lora_name=args.lora,
            strength_model=sm,
            strength_clip=sc,
            prompt=args.prompt,
            negative=args.negative,
            seed=args.seed,
            filename_prefix=prefix
        )
        
        print(f"Queuing: model={sm:.1f} clip={sc:.1f} ...", end=" ", flush=True)
        try:
            resp = queue_prompt(workflow)
            prompt_id = resp["prompt_id"]
            result = wait_for_completion(prompt_id)
            print(f"✅ Done")
            results.append({"model": sm, "clip": sc, "prompt_id": prompt_id, "status": "ok"})
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"model": sm, "clip": sc, "status": "error", "error": str(e)})
    
    return results


def main():
    parser = argparse.ArgumentParser(description="LoRA Strength Sweep Experiment")
    parser.add_argument("--mode", choices=["single", "grid"], default="single")
    parser.add_argument("--lora", required=True, help="LoRA filename")
    parser.add_argument("--checkpoint", default="dreamshaper_8.safetensors")
    parser.add_argument("--prompt", default="masterpiece, best quality, 1girl, princess, castle, sunset, cinematic")
    parser.add_argument("--negative", default="worst quality, low quality, blurry, watermark")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--api", default=None, help="ComfyUI API URL")
    
    args = parser.parse_args()
    
    if args.api:
        global COMFY_API
        COMFY_API = args.api
    
    if args.mode == "single":
        results = run_single_sweep(args)
    else:
        results = run_grid_sweep(args)
    
    # 保存结果
    output_file = f"lora_sweep_{args.mode}_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "mode": args.mode,
            "lora": args.lora,
            "checkpoint": args.checkpoint,
            "seed": args.seed,
            "results": results
        }, f, indent=2)
    
    print(f"\n📊 Results saved to {output_file}")
    print(f"✅ Completed: {sum(1 for r in results if r['status'] == 'ok')}/{len(results)}")


if __name__ == "__main__":
    main()
