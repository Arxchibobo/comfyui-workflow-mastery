#!/usr/bin/env python3
"""
图像质量自动评估脚本
====================
配合 batch_generate_evaluate.py 使用，对批量生成的图片进行自动质量评分。

依赖安装：
  pip install pyiqa torch torchvision Pillow

可选（CLIP Score）：
  pip install torchmetrics transformers

使用方法：
  python3 evaluate_quality.py --input batch_results/20260320_140000/ --prompts-csv prompts.csv
"""

import argparse
import csv
import json
from pathlib import Path


def evaluate_niqe_only(image_dir: Path) -> list:
    """仅使用 NIQE（无参考质量评估），不需要 GPU"""
    try:
        import pyiqa
        import torch
    except ImportError:
        print("需要安装 pyiqa: pip install pyiqa torch torchvision")
        return []

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    niqe = pyiqa.create_metric("niqe", device=device)

    results = []
    images = sorted(image_dir.glob("**/*.png"))
    print(f"Found {len(images)} images to evaluate")

    for i, img_path in enumerate(images):
        try:
            score = niqe(str(img_path)).item()
            results.append({"file": img_path.name, "niqe": round(score, 4)})
            print(f"  [{i+1}/{len(images)}] {img_path.name}: NIQE={score:.4f}")
        except Exception as e:
            print(f"  [{i+1}/{len(images)}] {img_path.name}: ERROR - {e}")
            results.append({"file": img_path.name, "niqe": -1})

    return results


def evaluate_clip_score(image_dir: Path, prompts_map: dict) -> list:
    """使用 CLIP Score 评估图文对齐"""
    try:
        import torch
        from torchmetrics.multimodal import CLIPScore
        from PIL import Image
        from torchvision import transforms
    except ImportError:
        print("需要安装: pip install torchmetrics transformers Pillow torchvision")
        return []

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clip_metric = CLIPScore(model_name_or_path="openai/clip-vit-large-patch14").to(device)
    
    to_tensor = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    results = []
    images = sorted(image_dir.glob("**/*.png"))

    for i, img_path in enumerate(images):
        prompt = prompts_map.get(img_path.stem, "")
        if not prompt:
            # 尝试从文件名推断 prompt index
            for key in prompts_map:
                if key in img_path.stem:
                    prompt = prompts_map[key]
                    break

        if not prompt:
            print(f"  [{i+1}] {img_path.name}: No prompt found, skipping CLIP Score")
            continue

        try:
            img = Image.open(img_path).convert("RGB")
            img_tensor = (to_tensor(img) * 255).to(torch.uint8).unsqueeze(0).to(device)
            score = clip_metric(img_tensor, prompt).item()
            results.append({
                "file": img_path.name,
                "clip_score": round(score, 4),
                "prompt": prompt[:50],
            })
            print(f"  [{i+1}/{len(images)}] {img_path.name}: CLIP={score:.4f}")
        except Exception as e:
            print(f"  [{i+1}/{len(images)}] {img_path.name}: ERROR - {e}")

    return results


def evaluate_image_reward(image_dir: Path, prompts_map: dict) -> list:
    """使用 ImageReward 评估人类偏好"""
    try:
        import ImageReward as RM
    except ImportError:
        print("需要安装: pip install image-reward")
        return []

    model = RM.load("ImageReward-v1.0")
    results = []
    images = sorted(image_dir.glob("**/*.png"))

    for i, img_path in enumerate(images):
        prompt = prompts_map.get(img_path.stem, "")
        if not prompt:
            for key in prompts_map:
                if key in img_path.stem:
                    prompt = prompts_map[key]
                    break
        if not prompt:
            continue

        try:
            score = model.score(prompt, str(img_path))
            results.append({
                "file": img_path.name,
                "image_reward": round(score, 4),
            })
            print(f"  [{i+1}/{len(images)}] {img_path.name}: IR={score:.4f}")
        except Exception as e:
            print(f"  [{i+1}/{len(images)}] {img_path.name}: ERROR - {e}")

    return results


def generate_report(niqe_results: list, clip_results: list, ir_results: list, output_dir: Path):
    """生成综合评估报告"""
    report = ["# Image Quality Evaluation Report\n"]

    if niqe_results:
        report.append("## NIQE Scores (lower = better)\n")
        sorted_niqe = sorted(niqe_results, key=lambda x: x["niqe"])
        report.append("| Rank | File | NIQE |")
        report.append("|------|------|------|")
        for i, r in enumerate(sorted_niqe[:20]):
            report.append(f"| {i+1} | {r['file']} | {r['niqe']} |")

        avg = sum(r["niqe"] for r in niqe_results if r["niqe"] > 0) / max(len(niqe_results), 1)
        report.append(f"\n**Average NIQE: {avg:.4f}**\n")

    if clip_results:
        report.append("## CLIP Scores (higher = better alignment)\n")
        sorted_clip = sorted(clip_results, key=lambda x: -x["clip_score"])
        report.append("| Rank | File | CLIP Score | Prompt |")
        report.append("|------|------|------------|--------|")
        for i, r in enumerate(sorted_clip[:20]):
            report.append(f"| {i+1} | {r['file']} | {r['clip_score']} | {r['prompt']} |")

    if ir_results:
        report.append("## ImageReward Scores (higher = better human preference)\n")
        sorted_ir = sorted(ir_results, key=lambda x: -x["image_reward"])
        report.append("| Rank | File | ImageReward |")
        report.append("|------|------|-------------|")
        for i, r in enumerate(sorted_ir[:20]):
            report.append(f"| {i+1} | {r['file']} | {r['image_reward']} |")

    report_path = output_dir / "EVALUATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))
    print(f"\n📊 Report: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate generated image quality")
    parser.add_argument("--input", required=True, help="Directory with generated images")
    parser.add_argument("--metrics", default="niqe", help="Comma-separated: niqe,clip,imagereward")
    parser.add_argument("--prompts-json", help="JSON file mapping filename_prefix → prompt")
    args = parser.parse_args()

    image_dir = Path(args.input)
    metrics = args.metrics.split(",")

    prompts_map = {}
    if args.prompts_json:
        prompts_map = json.load(open(args.prompts_json))

    niqe_results, clip_results, ir_results = [], [], []

    if "niqe" in metrics:
        print("\n=== NIQE Evaluation ===")
        niqe_results = evaluate_niqe_only(image_dir)

    if "clip" in metrics:
        print("\n=== CLIP Score Evaluation ===")
        clip_results = evaluate_clip_score(image_dir, prompts_map)

    if "imagereward" in metrics:
        print("\n=== ImageReward Evaluation ===")
        ir_results = evaluate_image_reward(image_dir, prompts_map)

    generate_report(niqe_results, clip_results, ir_results, image_dir)


if __name__ == "__main__":
    main()
