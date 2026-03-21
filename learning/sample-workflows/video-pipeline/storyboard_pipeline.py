#!/usr/bin/env python3
"""
Day 16: 多分镜视频生产管线
基于 RunningHub API 的完整视频制作流程

管线: 分镜脚本 → 关键帧生成 → 视频生成 → 拼接输出

Usage:
    export RUNNINGHUB_API_KEY="your_key"
    python3 storyboard_pipeline.py --storyboard storyboard.json --output /tmp/final_video/
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

RUNNINGHUB_SCRIPT = os.path.expanduser(
    "~/.openclaw/workspace/skills/runninghub-skills/scripts/runninghub.py"
)

# ─── 数据模型 ─────────────────────────────────────────────

@dataclass
class Scene:
    """分镜场景"""
    scene_id: int
    keyframe_prompt: str          # 关键帧图像描述
    motion_prompt: str            # 视频运动描述
    duration: int = 5             # 视频时长（秒）
    aspect_ratio: str = "16:9"    # 宽高比
    image_model: str = "rhart-image-n-pro/text-to-image"
    video_model: str = "seedance-v1.5-pro/image-to-video"
    resolution: str = "2K"        # 图像分辨率
    
    # 生成结果（运行时填充）
    keyframe_path: Optional[str] = None
    video_path: Optional[str] = None
    keyframe_cost: float = 0
    video_cost: float = 0
    keyframe_time: float = 0
    video_time: float = 0

@dataclass
class PipelineConfig:
    """管线配置"""
    output_dir: str = "/tmp/video-pipeline"
    max_retries: int = 3
    retry_delay: int = 10
    verbose: bool = True

# ─── 核心管线 ─────────────────────────────────────────────

class StoryboardPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def run(self, scenes: list[Scene]) -> dict:
        """执行完整管线"""
        results = {
            "scenes": [],
            "total_cost": 0,
            "total_time": 0,
            "success_count": 0,
            "fail_count": 0,
        }
        
        for scene in scenes:
            self._log(f"\n{'='*60}")
            self._log(f"Scene {scene.scene_id}: Generating keyframe...")
            self._log(f"{'='*60}")
            
            # Stage 1: 生成关键帧
            success = self._generate_keyframe(scene)
            if not success:
                self._log(f"  ❌ Keyframe generation failed, skipping scene {scene.scene_id}")
                results["fail_count"] += 1
                continue
            
            self._log(f"  ✅ Keyframe: {scene.keyframe_path} (¥{scene.keyframe_cost}, {scene.keyframe_time:.0f}s)")
            
            # Stage 2: 生成视频
            self._log(f"  📹 Generating video with {scene.video_model}...")
            success = self._generate_video(scene)
            if not success:
                self._log(f"  ❌ Video generation failed for scene {scene.scene_id}")
                results["fail_count"] += 1
                continue
            
            self._log(f"  ✅ Video: {scene.video_path} (¥{scene.video_cost}, {scene.video_time:.0f}s)")
            
            results["scenes"].append({
                "scene_id": scene.scene_id,
                "keyframe": scene.keyframe_path,
                "video": scene.video_path,
                "cost": scene.keyframe_cost + scene.video_cost,
                "time": scene.keyframe_time + scene.video_time,
            })
            results["total_cost"] += scene.keyframe_cost + scene.video_cost
            results["total_time"] += scene.keyframe_time + scene.video_time
            results["success_count"] += 1
        
        # Stage 3: 拼接视频（如果有 ffmpeg）
        if results["success_count"] > 1:
            self._concat_videos(results)
        
        # 输出报告
        self._print_report(results)
        return results
    
    def _generate_keyframe(self, scene: Scene) -> bool:
        """Stage 1: 文生图"""
        output_path = os.path.join(
            self.config.output_dir, f"scene{scene.scene_id:02d}_keyframe.jpg"
        )
        
        for attempt in range(self.config.max_retries):
            start = time.time()
            result = self._run_runninghub(
                endpoint=scene.image_model,
                prompt=scene.keyframe_prompt,
                params={
                    "aspectRatio": scene.aspect_ratio,
                    "resolution": scene.resolution,
                },
                output=output_path,
            )
            elapsed = time.time() - start
            
            if result["success"]:
                scene.keyframe_path = result.get("output_file", output_path)
                scene.keyframe_cost = result.get("cost", 0)
                scene.keyframe_time = elapsed
                return True
            
            if attempt < self.config.max_retries - 1:
                self._log(f"  ⚠️ Retry {attempt+1}/{self.config.max_retries}...")
                time.sleep(self.config.retry_delay)
        
        return False
    
    def _generate_video(self, scene: Scene) -> bool:
        """Stage 2: 图生视频"""
        output_path = os.path.join(
            self.config.output_dir, f"scene{scene.scene_id:02d}_video.mp4"
        )
        
        for attempt in range(self.config.max_retries):
            start = time.time()
            result = self._run_runninghub(
                endpoint=scene.video_model,
                prompt=scene.motion_prompt,
                image=scene.keyframe_path,
                output=output_path,
            )
            elapsed = time.time() - start
            
            if result["success"]:
                scene.video_path = result.get("output_file", output_path)
                scene.video_cost = result.get("cost", 0)
                scene.video_time = elapsed
                return True
            
            if attempt < self.config.max_retries - 1:
                self._log(f"  ⚠️ Retry {attempt+1}/{self.config.max_retries}...")
                time.sleep(self.config.retry_delay)
        
        return False
    
    def _run_runninghub(self, endpoint, prompt, output, image=None, params=None) -> dict:
        """调用 RunningHub API"""
        cmd = [
            sys.executable, RUNNINGHUB_SCRIPT,
            "--endpoint", endpoint,
            "--prompt", prompt,
            "--output", output,
        ]
        if image:
            cmd.extend(["--image", image])
        if params:
            for k, v in params.items():
                cmd.extend(["--param", f"{k}={v}"])
        
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                env={**os.environ, "RUNNINGHUB_API_KEY": os.environ.get("RUNNINGHUB_API_KEY", "")}
            )
            
            output_file = None
            cost = 0
            for line in proc.stdout.splitlines():
                if line.startswith("OUTPUT_FILE:"):
                    output_file = line.split(":", 1)[1]
                if line.startswith("COST:"):
                    cost_str = line.split("¥")[1] if "¥" in line else "0"
                    cost = float(cost_str)
            
            return {
                "success": proc.returncode == 0 and output_file,
                "output_file": output_file,
                "cost": cost,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _concat_videos(self, results):
        """用 ffmpeg 拼接所有视频片段"""
        video_paths = [s["video"] for s in results["scenes"]]
        if len(video_paths) < 2:
            return
        
        concat_list = os.path.join(self.config.output_dir, "concat_list.txt")
        with open(concat_list, "w") as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")
        
        output = os.path.join(self.config.output_dir, "final_combined.mp4")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list, "-c", "copy", output
            ], capture_output=True, timeout=60)
            results["combined_video"] = output
            self._log(f"\n🎬 Combined video: {output}")
        except Exception as e:
            self._log(f"\n⚠️ Concat failed: {e}")
    
    def _print_report(self, results):
        """输出管线报告"""
        self._log(f"\n{'='*60}")
        self._log("📊 Pipeline Report")
        self._log(f"{'='*60}")
        self._log(f"Total scenes: {results['success_count']}/{results['success_count']+results['fail_count']}")
        self._log(f"Total cost: ¥{results['total_cost']:.3f}")
        self._log(f"Total time: {results['total_time']:.0f}s")
        
        for s in results["scenes"]:
            self._log(f"  Scene {s['scene_id']}: ¥{s['cost']:.3f}, {s['time']:.0f}s")
    
    def _log(self, msg):
        if self.config.verbose:
            print(msg)


# ─── CLI ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Storyboard → Video Pipeline")
    parser.add_argument("--storyboard", "-s", required=True, help="Storyboard JSON file")
    parser.add_argument("--output", "-o", default="/tmp/video-pipeline", help="Output directory")
    parser.add_argument("--video-model", default="seedance-v1.5-pro/image-to-video")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    
    with open(args.storyboard) as f:
        storyboard_data = json.load(f)
    
    scenes = [Scene(**s) for s in storyboard_data["scenes"]]
    
    config = PipelineConfig(
        output_dir=args.output,
        verbose=not args.quiet,
    )
    
    pipeline = StoryboardPipeline(config)
    results = pipeline.run(scenes)
    
    # Save results
    with open(os.path.join(args.output, "pipeline_results.json"), "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
