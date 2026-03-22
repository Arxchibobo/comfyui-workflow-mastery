#!/usr/bin/env python3
"""
ComfyUI Batch API Runner — 生产级批量生成脚本
Day 18 学习产出

Features:
- CSV/JSON 批量任务定义
- WebSocket 实时进度追踪
- 指数退避重试（最多 3 次）
- CUDA OOM 自动恢复（POST /free）
- 结果摘要报告
- 队列深度控制

Usage:
  python batch_api_runner.py --workflow workflow_api.json --tasks tasks.csv --output ./output/
  python batch_api_runner.py --workflow workflow_api.json --tasks tasks.json --output ./output/ --server 127.0.0.1:8188
"""

import argparse
import asyncio
import copy
import csv
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

# Fallback to synchronous if async libs not available
import urllib.request
import urllib.parse

# ─── Data Classes ────────────────────────────────────────────

@dataclass
class BatchJob:
    """Single batch job definition"""
    job_id: str
    modifications: Dict[str, Dict[str, Any]]  # node_id → {inputs: {key: value}}
    output_prefix: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JobResult:
    """Result of a single job execution"""
    job_id: str
    status: str  # success / failed / timeout
    elapsed: float = 0.0
    output_files: List[str] = field(default_factory=list)
    error: str = ""
    attempts: int = 1

# ─── Core Runner ─────────────────────────────────────────────

class ComfyUIBatchRunner:
    def __init__(self, server_address: str, max_retries: int = 3, 
                 retry_delay: float = 5.0, timeout: float = 300.0):
        self.server = server_address
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())
        self.results: List[JobResult] = []
    
    # ─── HTTP helpers ────────────────────────────────────────
    
    def _post_prompt(self, prompt: dict, prompt_id: str) -> dict:
        """Submit prompt to ComfyUI queue"""
        payload = {
            "prompt": prompt,
            "client_id": self.client_id,
            "prompt_id": prompt_id,
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"http://{self.server}/prompt",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    
    def _get_history(self, prompt_id: str) -> dict:
        """Get execution history for a prompt"""
        url = f"http://{self.server}/history/{prompt_id}"
        resp = urllib.request.urlopen(url)
        return json.loads(resp.read())
    
    def _get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download an output image"""
        params = urllib.parse.urlencode({
            "filename": filename, "subfolder": subfolder, "type": folder_type
        })
        url = f"http://{self.server}/view?{params}"
        resp = urllib.request.urlopen(url)
        return resp.read()
    
    def _free_memory(self):
        """Free GPU memory by unloading models"""
        data = json.dumps({"unload_models": True, "free_memory": True}).encode()
        req = urllib.request.Request(
            f"http://{self.server}/free",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
    
    def _get_queue(self) -> dict:
        """Get current queue status"""
        url = f"http://{self.server}/queue"
        resp = urllib.request.urlopen(url)
        return json.loads(resp.read())
    
    def _get_system_stats(self) -> dict:
        """Get system stats"""
        url = f"http://{self.server}/system_stats"
        resp = urllib.request.urlopen(url)
        return json.loads(resp.read())
    
    # ─── Workflow modification ───────────────────────────────
    
    @staticmethod
    def modify_workflow(workflow: dict, modifications: dict) -> dict:
        """Apply modifications to a workflow template
        
        modifications = {
            "6": {"text": "new prompt"},         # shorthand for inputs
            "3": {"seed": 12345, "steps": 30},
        }
        """
        wf = copy.deepcopy(workflow)
        for node_id, changes in modifications.items():
            if node_id in wf:
                for key, value in changes.items():
                    wf[node_id]["inputs"][key] = value
        return wf
    
    # ─── Synchronous execution (websocket-client) ────────────
    
    def execute_sync(self, prompt: dict, prompt_id: str, 
                     progress_callback=None) -> dict:
        """Execute a single prompt synchronously using websocket-client"""
        import websocket as ws_client  # websocket-client package
        
        ws = ws_client.WebSocket()
        ws.settimeout(self.timeout)
        ws.connect(f"ws://{self.server}/ws?clientId={self.client_id}")
        
        try:
            self._post_prompt(prompt, prompt_id)
            
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    msg_type = message.get("type")
                    data = message.get("data", {})
                    
                    if msg_type == "progress" and progress_callback:
                        progress_callback(data["value"], data["max"], data.get("node"))
                    
                    elif msg_type == "executing":
                        if data.get("node") is None and data.get("prompt_id") == prompt_id:
                            break  # Execution complete
                    
                    elif msg_type == "execution_error":
                        raise RuntimeError(
                            data.get("exception_message", "Unknown execution error")
                        )
            
            # Fetch results
            history = self._get_history(prompt_id).get(prompt_id, {})
            return history.get("outputs", {})
            
        finally:
            ws.close()
    
    # ─── Batch execution ─────────────────────────────────────
    
    def run_batch(self, workflow_template: dict, jobs: List[BatchJob],
                  output_dir: str, verbose: bool = True):
        """Run a batch of jobs with retry logic"""
        
        os.makedirs(output_dir, exist_ok=True)
        total = len(jobs)
        start_total = time.time()
        
        if verbose:
            print(f"{'='*60}")
            print(f"ComfyUI Batch Runner — {total} jobs")
            print(f"Server: {self.server}")
            print(f"Output: {output_dir}")
            print(f"Max retries: {self.max_retries}")
            print(f"{'='*60}\n")
        
        for i, job in enumerate(jobs):
            if verbose:
                print(f"[{i+1}/{total}] Job: {job.job_id}")
            
            prompt = self.modify_workflow(workflow_template, job.modifications)
            
            # Set output filename prefix if specified
            if job.output_prefix:
                for node_id, node in prompt.items():
                    if node.get("class_type") == "SaveImage":
                        node["inputs"]["filename_prefix"] = job.output_prefix
            
            result = self._execute_with_retry(prompt, job, output_dir, verbose)
            self.results.append(result)
            
            if verbose:
                status_icon = "✅" if result.status == "success" else "❌"
                print(f"  {status_icon} {result.status} in {result.elapsed:.1f}s "
                      f"(attempt {result.attempts})\n")
        
        elapsed_total = time.time() - start_total
        
        if verbose:
            self._print_summary(elapsed_total)
        
        return self.results
    
    def _execute_with_retry(self, prompt: dict, job: BatchJob,
                            output_dir: str, verbose: bool) -> JobResult:
        """Execute a single job with retry logic"""
        
        for attempt in range(1, self.max_retries + 1):
            prompt_id = str(uuid.uuid4())
            start = time.time()
            
            try:
                def on_progress(value, max_val, node):
                    if verbose:
                        pct = value / max_val * 100
                        print(f"\r  Sampling: {pct:.0f}% ({value}/{max_val})", end="")
                
                outputs = self.execute_sync(prompt, prompt_id, on_progress)
                elapsed = time.time() - start
                
                if verbose and outputs:
                    print()  # newline after progress
                
                # Download output images
                output_files = []
                for node_id, node_output in outputs.items():
                    for img in node_output.get("images", []):
                        image_data = self._get_image(
                            img["filename"], img["subfolder"], img["type"]
                        )
                        save_path = os.path.join(
                            output_dir, 
                            f"{job.output_prefix or job.job_id}_{img['filename']}"
                        )
                        with open(save_path, 'wb') as f:
                            f.write(image_data)
                        output_files.append(save_path)
                
                return JobResult(
                    job_id=job.job_id, status="success",
                    elapsed=elapsed, output_files=output_files, attempts=attempt
                )
                
            except RuntimeError as e:
                error_msg = str(e)
                if verbose:
                    print(f"\n  ⚠️ Attempt {attempt} failed: {error_msg[:100]}")
                
                if "CUDA out of memory" in error_msg:
                    if verbose:
                        print("  🔄 Freeing GPU memory...")
                    self._free_memory()
                    time.sleep(3)
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    if verbose:
                        print(f"  ⏳ Retrying in {delay:.0f}s...")
                    time.sleep(delay)
                else:
                    return JobResult(
                        job_id=job.job_id, status="failed",
                        elapsed=time.time() - start, error=error_msg, attempts=attempt
                    )
            
            except Exception as e:
                elapsed = time.time() - start
                if verbose:
                    print(f"\n  ❌ Unexpected error: {e}")
                return JobResult(
                    job_id=job.job_id, status="failed",
                    elapsed=elapsed, error=str(e), attempts=attempt
                )
        
        return JobResult(job_id=job.job_id, status="failed", error="max retries exceeded")
    
    def _print_summary(self, total_elapsed: float):
        """Print batch execution summary"""
        success = sum(1 for r in self.results if r.status == "success")
        failed = sum(1 for r in self.results if r.status == "failed")
        total = len(self.results)
        
        print(f"\n{'='*60}")
        print(f"BATCH SUMMARY")
        print(f"{'─'*60}")
        print(f"Total: {total} | Success: {success} | Failed: {failed}")
        print(f"Total time: {total_elapsed:.1f}s | Avg: {total_elapsed/max(total,1):.1f}s/job")
        print(f"{'─'*60}")
        
        for r in self.results:
            icon = "✅" if r.status == "success" else "❌"
            files = f" → {len(r.output_files)} files" if r.output_files else ""
            err = f" ({r.error[:50]})" if r.error else ""
            print(f"  {icon} {r.job_id:30s} {r.elapsed:6.1f}s attempt#{r.attempts}{files}{err}")
        
        print(f"{'='*60}")

# ─── Task loading ────────────────────────────────────────────

def load_tasks_from_csv(csv_path: str) -> List[BatchJob]:
    """Load batch tasks from CSV
    
    Expected columns: job_id, node_id, param_name, param_value, [output_prefix]
    Or: job_id, prompt, seed, [output_prefix] (simplified format)
    """
    jobs = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            job_id = row['job_id']
            if job_id not in jobs:
                jobs[job_id] = BatchJob(
                    job_id=job_id,
                    modifications={},
                    output_prefix=row.get('output_prefix', job_id)
                )
            
            if 'node_id' in row and 'param_name' in row:
                # Detailed format
                node_id = row['node_id']
                if node_id not in jobs[job_id].modifications:
                    jobs[job_id].modifications[node_id] = {}
                
                value = row['param_value']
                # Try to parse as number
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                
                jobs[job_id].modifications[node_id][row['param_name']] = value
            
            elif 'prompt' in row:
                # Simplified format — assumes node "6" is positive prompt, "3" is KSampler
                if '6' not in jobs[job_id].modifications:
                    jobs[job_id].modifications['6'] = {}
                jobs[job_id].modifications['6']['text'] = row['prompt']
                
                if 'seed' in row and row['seed']:
                    if '3' not in jobs[job_id].modifications:
                        jobs[job_id].modifications['3'] = {}
                    jobs[job_id].modifications['3']['seed'] = int(row['seed'])
    
    return list(jobs.values())


def load_tasks_from_json(json_path: str) -> List[BatchJob]:
    """Load batch tasks from JSON
    
    Expected format:
    [
        {
            "job_id": "dragon_01",
            "output_prefix": "dragon",
            "modifications": {
                "6": {"text": "a dragon"},
                "3": {"seed": 12345, "steps": 20}
            }
        }
    ]
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    return [
        BatchJob(
            job_id=item['job_id'],
            modifications=item.get('modifications', {}),
            output_prefix=item.get('output_prefix', item['job_id']),
            metadata=item.get('metadata', {})
        )
        for item in data
    ]

# ─── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ComfyUI Batch API Runner")
    parser.add_argument("--workflow", required=True, help="Workflow JSON file (API format)")
    parser.add_argument("--tasks", required=True, help="Tasks file (CSV or JSON)")
    parser.add_argument("--output", default="./batch_output", help="Output directory")
    parser.add_argument("--server", default="127.0.0.1:8188", help="ComfyUI server address")
    parser.add_argument("--retries", type=int, default=3, help="Max retries per job")
    parser.add_argument("--timeout", type=float, default=300, help="Timeout per job (seconds)")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    args = parser.parse_args()
    
    # Load workflow template
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
    
    # Load tasks
    if args.tasks.endswith('.csv'):
        jobs = load_tasks_from_csv(args.tasks)
    elif args.tasks.endswith('.json'):
        jobs = load_tasks_from_json(args.tasks)
    else:
        print(f"Error: Unsupported task file format: {args.tasks}")
        sys.exit(1)
    
    print(f"Loaded {len(jobs)} jobs from {args.tasks}")
    
    # Run batch
    runner = ComfyUIBatchRunner(
        server_address=args.server,
        max_retries=args.retries,
        timeout=args.timeout
    )
    
    results = runner.run_batch(workflow, jobs, args.output, verbose=not args.quiet)
    
    # Save results report
    report_path = os.path.join(args.output, "batch_report.json")
    with open(report_path, 'w') as f:
        json.dump([{
            "job_id": r.job_id,
            "status": r.status,
            "elapsed": r.elapsed,
            "attempts": r.attempts,
            "output_files": r.output_files,
            "error": r.error
        } for r in results], f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    
    # Exit with error code if any failures
    if any(r.status != "success" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
