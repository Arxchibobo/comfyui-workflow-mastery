#!/usr/bin/env python3
"""
ComfyUI 批量生成 + 质量评估自动化脚本
======================================
用途：通过 ComfyUI API 系统性批量生成图像，支持多 prompt × 多参数矩阵。
实践产出：comfyui-learning Session 10

使用方法：
  1. 确保 ComfyUI 在 http://127.0.0.1:8188 运行
  2. 将 workflow_api.json 放在同目录下（从 ComfyUI Dev Mode 导出）
  3. python3 batch_generate_evaluate.py

依赖：
  - 标准库即可运行（urllib, json）
  - 可选评估：pip install pyiqa torch torchvision torchmetrics
"""

import json
import random
import time
import os
import csv
from urllib import request, error
from pathlib import Path
from datetime import datetime


# ============================================================
# 配置区
# ============================================================

COMFYUI_SERVER = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188")
OUTPUT_DIR = Path("batch_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
TIMEOUT_SECONDS = 300  # 单次生成超时
POLL_INTERVAL = 2      # 轮询间隔（秒）

# 实验参数矩阵
EXPERIMENT_CONFIG = {
    "prompts": [
        "a majestic snow leopard on a rocky cliff at sunset, 8k, national geographic",
        "a cozy coffee shop interior, warm lighting, rainy window, watercolor style",
        "cyberpunk cityscape at night, neon lights, flying cars, cinematic",
    ],
    "negative_prompt": "blurry, low quality, deformed, ugly, bad anatomy, watermark, text",
    "seeds": [42, 123, 456, 789],
    "samplers": ["euler", "dpmpp_2m", "dpmpp_sde"],
    "schedulers": ["normal", "karras"],
    "steps": [20],
    "cfg_scales": [7.0],
    "width": 1024,
    "height": 1024,
    "checkpoint": "sd_xl_base_1.0.safetensors",
}


# ============================================================
# ComfyUI API 交互
# ============================================================

def queue_prompt(workflow: dict) -> str:
    """提交工作流到 ComfyUI 队列，返回 prompt_id"""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = request.Request(
        f"{COMFYUI_SERVER}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = json.loads(request.urlopen(req).read())
        return resp["prompt_id"]
    except error.HTTPError as e:
        print(f"  [ERROR] HTTP {e.code}: {e.read().decode()[:200]}")
        raise


def wait_for_completion(prompt_id: str, timeout: int = TIMEOUT_SECONDS) -> dict:
    """轮询等待执行完成，返回 history 数据"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = json.loads(
                request.urlopen(f"{COMFYUI_SERVER}/history/{prompt_id}").read()
            )
            if prompt_id in resp:
                return resp[prompt_id]
        except error.HTTPError:
            pass
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"Prompt {prompt_id} timed out after {timeout}s")


def build_workflow(
    prompt: str,
    negative: str,
    seed: int,
    sampler: str,
    scheduler: str,
    steps: int,
    cfg: float,
    width: int,
    height: int,
    checkpoint: str,
    filename_prefix: str,
) -> dict:
    """构建 ComfyUI API 格式的工作流 JSON"""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["1", 1]},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"images": ["6", 0], "filename_prefix": filename_prefix},
        },
    }


# ============================================================
# 批量生成主流程
# ============================================================

def run_batch_experiment():
    """执行批量生成实验"""
    cfg = EXPERIMENT_CONFIG
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 计算总任务数
    total = (
        len(cfg["prompts"])
        * len(cfg["seeds"])
        * len(cfg["samplers"])
        * len(cfg["schedulers"])
        * len(cfg["steps"])
        * len(cfg["cfg_scales"])
    )
    print(f"=== ComfyUI Batch Experiment ===")
    print(f"Total tasks: {total}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    results = []
    task_num = 0

    for pi, prompt in enumerate(cfg["prompts"]):
        prompt_short = prompt[:40].replace(" ", "_").replace(",", "")
        for seed in cfg["seeds"]:
            for sampler in cfg["samplers"]:
                for scheduler in cfg["schedulers"]:
                    for steps in cfg["steps"]:
                        for cfg_scale in cfg["cfg_scales"]:
                            task_num += 1
                            prefix = f"p{pi}_{sampler}_{scheduler}_s{steps}_cfg{cfg_scale}_seed{seed}"
                            print(f"[{task_num}/{total}] {prefix}")

                            workflow = build_workflow(
                                prompt=prompt,
                                negative=cfg["negative_prompt"],
                                seed=seed,
                                sampler=sampler,
                                scheduler=scheduler,
                                steps=steps,
                                cfg=cfg_scale,
                                width=cfg["width"],
                                height=cfg["height"],
                                checkpoint=cfg["checkpoint"],
                                filename_prefix=f"batch/{prefix}",
                            )

                            try:
                                t0 = time.time()
                                prompt_id = queue_prompt(workflow)
                                output = wait_for_completion(prompt_id)
                                elapsed = time.time() - t0

                                results.append({
                                    "task": task_num,
                                    "prompt_index": pi,
                                    "seed": seed,
                                    "sampler": sampler,
                                    "scheduler": scheduler,
                                    "steps": steps,
                                    "cfg": cfg_scale,
                                    "time_s": round(elapsed, 2),
                                    "status": "ok",
                                    "filename_prefix": prefix,
                                })
                                print(f"  ✅ Done in {elapsed:.1f}s")

                            except Exception as e:
                                results.append({
                                    "task": task_num,
                                    "prompt_index": pi,
                                    "seed": seed,
                                    "sampler": sampler,
                                    "scheduler": scheduler,
                                    "steps": steps,
                                    "cfg": cfg_scale,
                                    "time_s": 0,
                                    "status": f"error: {e}",
                                    "filename_prefix": prefix,
                                })
                                print(f"  ❌ Error: {e}")

    # 保存实验结果 CSV
    csv_path = OUTPUT_DIR / "experiment_results.csv"
    if results:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\n📊 Results saved to: {csv_path}")

    # 保存实验配置
    config_path = OUTPUT_DIR / "experiment_config.json"
    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"📋 Config saved to: {config_path}")

    # 生成简要报告
    ok_count = sum(1 for r in results if r["status"] == "ok")
    err_count = total - ok_count
    avg_time = sum(r["time_s"] for r in results if r["status"] == "ok") / max(ok_count, 1)
    
    report = f"""
# Batch Experiment Report
- Date: {datetime.now().isoformat()}
- Total tasks: {total}
- Success: {ok_count}, Failed: {err_count}
- Average generation time: {avg_time:.1f}s
- Prompts: {len(cfg['prompts'])}
- Seeds: {cfg['seeds']}
- Samplers: {cfg['samplers']}
- Schedulers: {cfg['schedulers']}

## Next Steps
1. 人工评审生成图片（按文件名分组对比）
2. 可选：运行 evaluate_quality.py 进行自动评分
3. 分析哪个 sampler×scheduler 组合最优
"""
    report_path = OUTPUT_DIR / "REPORT.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"📝 Report saved to: {report_path}")


if __name__ == "__main__":
    run_batch_experiment()
