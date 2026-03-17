#!/usr/bin/env python3
"""
ComfyUI Workflow Compiler
=========================
Compiles ComfyUI workflows from high-level descriptions.
Understands node types, data flow, and can compose novel topologies.

Usage:
  # From pipeline description
  python3 workflow_compiler.py --pipeline "text2img" --prompt "cute puppy"
  python3 workflow_compiler.py --pipeline "text2img+controlnet" --prompt "..." --control-image photo.jpg
  python3 workflow_compiler.py --pipeline "text2img+lora+upscale" --prompt "..." --lora "style.safetensors"
  python3 workflow_compiler.py --pipeline "img2img+upscale" --image photo.jpg --prompt "anime"
  python3 workflow_compiler.py --pipeline "flux_text2img" --prompt "..."

  # Execute after compiling
  python3 workflow_compiler.py --pipeline "text2img" --prompt "sunset" --execute

  # Save to file
  python3 workflow_compiler.py --pipeline "text2img" --prompt "sunset" --save /tmp/wf.json
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
NODE_DB_PATH = DATA_DIR / "node_database.json"
TEMPLATES_PATH = DATA_DIR / "templates.json"
TOKEN_PATH = Path("/tmp/rh_access_token.txt")
RH_BASE = "https://www.runninghub.ai"
RH_API = "https://www.runninghub.cn"
WORKSPACE_ID = "2033835239616811009"

# Template IDs for base API format
BASE_TEMPLATE_IDS = {
    "text2img": "9999",
    "img2img": "9997",
    "text2img_lora": "9998",
    "img2img_lora": "9995",
    "img2img_upscale": "9996",
    "controlnet": "1818184196492820481"
}


def resolve_api_key() -> str:
    key = os.environ.get("RUNNINGHUB_API_KEY", "")
    if not key:
        secrets = Path.home() / ".openclaw" / "personal-secrets.json"
        if secrets.exists():
            with open(secrets) as f:
                key = json.load(f).get("RUNNINGHUB_API_KEY", "")
    return key


def get_token() -> str:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()
    return ""


def load_node_db() -> dict:
    with open(NODE_DB_PATH) as f:
        return json.load(f)


def get_base_api(token: str, template_id: str) -> dict:
    r = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{RH_BASE}/api/openapi/getJsonApiFormat',
        '-H', 'Content-Type: application/json',
        '-H', f'Authorization: Bearer {token}',
        '-d', json.dumps({"workflowId": template_id})
    ], capture_output=True, text=True)
    data = json.loads(r.stdout)
    prompt_str = data.get('data', {}).get('prompt', '')
    if not prompt_str:
        raise RuntimeError(f"No API format for template {template_id}")
    return json.loads(prompt_str) if isinstance(prompt_str, str) else prompt_str


# ---------------------------------------------------------------------------
# Pure Compiler: builds API format from scratch (no template needed)
# ---------------------------------------------------------------------------

class WorkflowCompiler:
    """Compiles ComfyUI API-format workflows from node descriptions."""
    
    def __init__(self):
        self.nodes = {}  # id -> {class_type, inputs, _meta}
        self.next_id = 1
    
    def add_node(self, class_type: str, inputs: dict = None, title: str = "") -> str:
        """Add a node and return its ID."""
        nid = str(self.next_id)
        self.next_id += 1
        self.nodes[nid] = {
            "inputs": inputs or {},
            "class_type": class_type,
            "_meta": {"title": title or class_type}
        }
        return nid
    
    def connect(self, from_id: str, from_output: int, to_id: str, to_input: str):
        """Connect output of one node to input of another."""
        self.nodes[to_id]["inputs"][to_input] = [from_id, from_output]
    
    def set_param(self, node_id: str, param: str, value):
        """Set a parameter on a node."""
        self.nodes[node_id]["inputs"][param] = value
    
    def compile(self) -> dict:
        """Return the API-format JSON."""
        return dict(self.nodes)

    # ----- High-level pipeline builders -----
    
    def build_text2img(self, prompt: str, negative: str = "", width: int = 1024, height: int = 1024,
                       steps: int = 20, cfg: float = 7.0, sampler: str = "dpmpp_2m_sde",
                       scheduler: str = "karras", checkpoint: str = "sd_xl_base_1.0.safetensors",
                       seed: int = -1, **kwargs) -> dict:
        """Build a text2img pipeline."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        empty = self.add_node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1}, "Empty Latent")
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive Prompt")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative Prompt")
        
        self.connect(ckpt, 1, pos, "clip")  # CLIP -> positive
        self.connect(ckpt, 1, neg, "clip")  # CLIP -> negative
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": sampler, "scheduler": scheduler, "denoise": 1.0
        }, "KSampler")
        
        self.connect(ckpt, 0, ks, "model")      # MODEL
        self.connect(pos, 0, ks, "positive")      # CONDITIONING
        self.connect(neg, 0, ks, "negative")      # CONDITIONING  
        self.connect(empty, 0, ks, "latent_image") # LATENT
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")   # LATENT
        self.connect(ckpt, 2, vae_dec, "vae")     # VAE
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")   # IMAGE
        
        return self.compile()
    
    def build_text2img_lora(self, prompt: str, lora_name: str, lora_strength: float = 0.7,
                            negative: str = "", width: int = 1024, height: int = 1024,
                            steps: int = 20, cfg: float = 7.0, checkpoint: str = "sd_xl_base_1.0.safetensors",
                            seed: int = -1, **kwargs) -> dict:
        """Build text2img + LoRA pipeline."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        lora = self.add_node("LoraLoader", {
            "lora_name": lora_name, "strength_model": lora_strength, "strength_clip": 1.0
        }, "Load LoRA")
        
        self.connect(ckpt, 0, lora, "model")  # MODEL
        self.connect(ckpt, 1, lora, "clip")   # CLIP
        
        empty = self.add_node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1}, "Empty Latent")
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        
        self.connect(lora, 1, pos, "clip")
        self.connect(lora, 1, neg, "clip")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "dpmpp_2m_sde", "scheduler": "karras", "denoise": 1.0
        }, "KSampler")
        
        self.connect(lora, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg, 0, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_img2img(self, prompt: str, image_file: str, denoise: float = 0.5,
                      negative: str = "", steps: int = 20, cfg: float = 7.0,
                      checkpoint: str = "sd_xl_base_1.0.safetensors", seed: int = -1, **kwargs) -> dict:
        """Build img2img pipeline."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        img = self.add_node("LoadImage", {"image": image_file}, "Load Image")
        
        vae_enc = self.add_node("VAEEncode", {}, "VAE Encode")
        self.connect(img, 0, vae_enc, "pixels")
        self.connect(ckpt, 2, vae_enc, "vae")
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        self.connect(ckpt, 1, pos, "clip")
        self.connect(ckpt, 1, neg, "clip")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": denoise
        }, "KSampler")
        
        self.connect(ckpt, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg, 0, ks, "negative")
        self.connect(vae_enc, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_controlnet(self, prompt: str, control_image: str, 
                         preprocessor: str = "CannyEdgePreprocessor",
                         controlnet_model: str = "controlnet-union-sdxl-1.0.safetensors",
                         strength: float = 0.7, negative: str = "",
                         width: int = 1024, height: int = 1024,
                         steps: int = 20, cfg: float = 7.0,
                         checkpoint: str = "sd_xl_base_1.0.safetensors",
                         seed: int = -1, **kwargs) -> dict:
        """Build ControlNet pipeline."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        cn_loader = self.add_node("ControlNetLoader", {"control_net_name": controlnet_model}, "Load ControlNet")
        ctrl_img = self.add_node("LoadImage", {"image": control_image}, "Control Image")
        
        # Preprocessor
        preprocess = self.add_node("AIO_Preprocessor", {
            "preprocessor": preprocessor, "resolution": 512
        }, "Preprocessor")
        self.connect(ctrl_img, 0, preprocess, "image")
        
        # Text encoding
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        self.connect(ckpt, 1, pos, "clip")
        self.connect(ckpt, 1, neg, "clip")
        
        # ControlNet Apply
        cn_apply = self.add_node("ControlNetApplyAdvanced", {
            "strength": strength, "start_percent": 0.0, "end_percent": 1.0
        }, "Apply ControlNet")
        self.connect(pos, 0, cn_apply, "positive")
        self.connect(neg, 0, cn_apply, "negative")
        self.connect(cn_loader, 0, cn_apply, "control_net")
        self.connect(preprocess, 0, cn_apply, "image")
        self.connect(ckpt, 2, cn_apply, "vae")
        
        # Sampling
        empty = self.add_node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1}, "Empty Latent")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "dpmpp_2m_sde", "scheduler": "karras", "denoise": 1.0
        }, "KSampler")
        
        self.connect(ckpt, 0, ks, "model")
        self.connect(cn_apply, 0, ks, "positive")
        self.connect(cn_apply, 1, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_flux_text2img(self, prompt: str, width: int = 1024, height: int = 1024,
                            steps: int = 20, guidance: float = 3.5,
                            unet_name: str = "flux1-dev.safetensors",
                            clip_name1: str = "t5xxl_fp16.safetensors",
                            clip_name2: str = "clip_l.safetensors",
                            vae_name: str = "ae.safetensors",
                            seed: int = -1, **kwargs) -> dict:
        """Build Flux text2img with advanced sampler pipeline."""
        unet = self.add_node("UNETLoader", {"unet_name": unet_name, "weight_dtype": "default"}, "Load UNet")
        clip = self.add_node("DualCLIPLoader", {
            "clip_name1": clip_name1, "clip_name2": clip_name2, "type": "flux"
        }, "Load CLIP")
        vae = self.add_node("VAELoader", {"vae_name": vae_name}, "Load VAE")
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        self.connect(clip, 0, pos, "clip")
        
        guidance_node = self.add_node("FluxGuidance", {"guidance": guidance}, "Flux Guidance")
        self.connect(pos, 0, guidance_node, "conditioning")
        
        neg = self.add_node("ConditioningZeroOut", {}, "Zero Negative")
        self.connect(pos, 0, neg, "conditioning")  # Zero out for Flux
        
        empty = self.add_node("EmptySD3LatentImage", {"width": width, "height": height, "batch_size": 1}, "Empty Latent")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        noise = self.add_node("RandomNoise", {"noise_seed": seed}, "Noise")
        sampler = self.add_node("KSamplerSelect", {"sampler_name": "euler"}, "Sampler")
        scheduler = self.add_node("BasicScheduler", {"scheduler": "simple", "steps": steps, "denoise": 1.0}, "Scheduler")
        self.connect(unet, 0, scheduler, "model")
        
        guider = self.add_node("CFGGuider", {"cfg": 1.0}, "CFG Guider")
        self.connect(unet, 0, guider, "model")
        self.connect(guidance_node, 0, guider, "positive")
        self.connect(neg, 0, guider, "negative")
        
        adv_sampler = self.add_node("SamplerCustomAdvanced", {}, "Sample")
        self.connect(noise, 0, adv_sampler, "noise")
        self.connect(guider, 0, adv_sampler, "guider")
        self.connect(sampler, 0, adv_sampler, "sampler")
        self.connect(scheduler, 0, adv_sampler, "sigmas")
        self.connect(empty, 0, adv_sampler, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(adv_sampler, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()


# ---------------------------------------------------------------------------
# Hybrid approach: compile from scratch OR modify base template
# ---------------------------------------------------------------------------

    def build_inpaint(self, prompt: str, image_file: str, mask_file: str = "",
                      negative: str = "", steps: int = 20, cfg: float = 7.0,
                      checkpoint: str = "512-inpainting-ema.safetensors",
                      grow_mask: int = 6, seed: int = -1, **kwargs) -> dict:
        """Build inpainting pipeline (局部重绘)."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        img = self.add_node("LoadImage", {"image": image_file}, "Load Image")
        
        # VAE Encode for Inpainting (special node)
        vae_enc = self.add_node("VAEEncodeForInpaint", {
            "grow_mask_by": grow_mask
        }, "VAE Encode (Inpaint)")
        self.connect(img, 0, vae_enc, "pixels")   # IMAGE
        self.connect(img, 1, vae_enc, "mask")      # MASK (from LoadImage output 1)
        self.connect(ckpt, 2, vae_enc, "vae")      # VAE
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        self.connect(ckpt, 1, pos, "clip")
        self.connect(ckpt, 1, neg, "clip")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0
        }, "KSampler")
        self.connect(ckpt, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg, 0, ks, "negative")
        self.connect(vae_enc, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_outpaint(self, prompt: str, image_file: str, 
                       left: int = 0, top: int = 0, right: int = 256, bottom: int = 0,
                       feathering: int = 40, negative: str = "", steps: int = 20, cfg: float = 7.0,
                       checkpoint: str = "512-inpainting-ema.safetensors",
                       seed: int = -1, **kwargs) -> dict:
        """Build outpainting pipeline (扩展画布)."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        img = self.add_node("LoadImage", {"image": image_file}, "Load Image")
        
        # Pad Image for Outpainting
        pad = self.add_node("ImagePadForOutpaint", {
            "left": left, "top": top, "right": right, "bottom": bottom,
            "feathering": feathering
        }, "Pad for Outpaint")
        self.connect(img, 0, pad, "image")
        
        # VAE Encode for Inpainting (uses padded image + mask)
        vae_enc = self.add_node("VAEEncodeForInpaint", {"grow_mask_by": 6}, "VAE Encode (Inpaint)")
        self.connect(pad, 0, vae_enc, "pixels")   # Padded IMAGE
        self.connect(pad, 1, vae_enc, "mask")      # MASK from padding
        self.connect(ckpt, 2, vae_enc, "vae")
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        self.connect(ckpt, 1, pos, "clip")
        self.connect(ckpt, 1, neg, "clip")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0
        }, "KSampler")
        self.connect(ckpt, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg, 0, ks, "negative")
        self.connect(vae_enc, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_upscale(self, image_file: str, upscale_model: str = "4x-ESRGAN.pth",
                      **kwargs) -> dict:
        """Build simple upscale pipeline (超分辨率)."""
        img = self.add_node("LoadImage", {"image": image_file}, "Load Image")
        model = self.add_node("UpscaleModelLoader", {"model_name": upscale_model}, "Load Upscale Model")
        upscale = self.add_node("ImageUpscaleWithModel", {}, "Upscale")
        self.connect(model, 0, upscale, "upscale_model")
        self.connect(img, 0, upscale, "image")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(upscale, 0, save, "images")
        
        return self.compile()
    
    def build_text2img_upscale(self, prompt: str, negative: str = "",
                               width: int = 768, height: int = 768,
                               steps: int = 20, cfg: float = 7.0,
                               checkpoint: str = "sd_xl_base_1.0.safetensors",
                               upscale_model: str = "4x-ESRGAN.pth",
                               seed: int = -1, **kwargs) -> dict:
        """Build text2img + upscale combo pipeline."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        empty = self.add_node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1}, "Empty Latent")
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        self.connect(ckpt, 1, pos, "clip")
        self.connect(ckpt, 1, neg, "clip")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "dpmpp_2m_sde", "scheduler": "karras", "denoise": 1.0
        }, "KSampler")
        self.connect(ckpt, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg, 0, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        # Upscale chain
        up_model = self.add_node("UpscaleModelLoader", {"model_name": upscale_model}, "Load Upscale Model")
        upscale = self.add_node("ImageUpscaleWithModel", {}, "Upscale")
        self.connect(up_model, 0, upscale, "upscale_model")
        self.connect(vae_dec, 0, upscale, "image")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(upscale, 0, save, "images")
        
        return self.compile()
    
    def build_multi_controlnet(self, prompt: str, control_image1: str = "", control_image2: str = "",
                                preprocessor1: str = "OpenPosePreprocessor",
                                preprocessor2: str = "CannyEdgePreprocessor",
                                controlnet_model1: str = "control_v11p_sd15_openpose_fp16.safetensors",
                                controlnet_model2: str = "control_v11p_sd15_scribble_fp16.safetensors",
                                strength1: float = 1.0, strength2: float = 1.0,
                                negative: str = "", width: int = 512, height: int = 768,
                                steps: int = 20, cfg: float = 7.0,
                                checkpoint: str = "dreamCreationVirtual3DECommerce_v10.safetensors",
                                seed: int = -1, **kwargs) -> dict:
        """Build dual ControlNet pipeline (多 ControlNet 混合)."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint}, "Load Checkpoint")
        
        # Text encoding
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg_node = self.add_node("CLIPTextEncode", {"text": negative or "(worst quality:1.5), blurry"}, "Negative")
        self.connect(ckpt, 1, pos, "clip")
        self.connect(ckpt, 1, neg_node, "clip")
        
        # ControlNet 1
        cn1_loader = self.add_node("ControlNetLoader", {"control_net_name": controlnet_model1}, "ControlNet 1")
        img1 = self.add_node("LoadImage", {"image": control_image1}, "Control Image 1")
        cn1_apply = self.add_node("ControlNetApplyAdvanced", {
            "strength": strength1, "start_percent": 0.0, "end_percent": 1.0
        }, "Apply CN1")
        self.connect(pos, 0, cn1_apply, "positive")
        self.connect(neg_node, 0, cn1_apply, "negative")
        self.connect(cn1_loader, 0, cn1_apply, "control_net")
        self.connect(img1, 0, cn1_apply, "image")
        self.connect(ckpt, 2, cn1_apply, "vae")
        
        # ControlNet 2 (chained from CN1)
        cn2_loader = self.add_node("ControlNetLoader", {"control_net_name": controlnet_model2}, "ControlNet 2")
        img2 = self.add_node("LoadImage", {"image": control_image2}, "Control Image 2")
        cn2_apply = self.add_node("ControlNetApplyAdvanced", {
            "strength": strength2, "start_percent": 0.0, "end_percent": 1.0
        }, "Apply CN2")
        self.connect(cn1_apply, 0, cn2_apply, "positive")   # Chain from CN1
        self.connect(cn1_apply, 1, cn2_apply, "negative")   # Chain from CN1
        self.connect(cn2_loader, 0, cn2_apply, "control_net")
        self.connect(img2, 0, cn2_apply, "image")
        self.connect(ckpt, 2, cn2_apply, "vae")
        
        # Sampling
        empty = self.add_node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1}, "Empty Latent")
        if seed == -1:
            seed = random.randint(0, 2**53)
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "dpmpp_2m_sde", "scheduler": "karras", "denoise": 1.0
        }, "KSampler")
        self.connect(ckpt, 0, ks, "model")
        self.connect(cn2_apply, 0, ks, "positive")
        self.connect(cn2_apply, 1, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"}, "Save Image")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_wan_t2v(self, prompt: str, negative: str = "", 
                      width: int = 832, height: int = 480, num_frames: int = 81,
                      steps: int = 30, cfg: float = 6.0,
                      diffusion_model: str = "wan2.1_t2v_1.3B_fp16.safetensors",
                      text_encoder: str = "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                      vae_name: str = "wan_2.1_vae.safetensors",
                      seed: int = -1, **kwargs) -> dict:
        """Build Wan2.1 Text-to-Video pipeline."""
        unet = self.add_node("UNETLoader", {"unet_name": diffusion_model, "weight_dtype": "default"}, "Load Diffusion Model")
        clip = self.add_node("CLIPLoader", {"clip_name": text_encoder, "type": "wan"}, "Load CLIP")
        vae = self.add_node("VAELoader", {"vae_name": vae_name}, "Load VAE")
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg_node = self.add_node("CLIPTextEncode", {"text": negative or ""}, "Negative")
        self.connect(clip, 0, pos, "clip")
        self.connect(clip, 0, neg_node, "clip")
        
        empty = self.add_node("EmptyHunyuanLatentVideo", {
            "width": width, "height": height, "length": num_frames, "batch_size": 1
        }, "Empty Video Latent")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "uni_pc_bh2", "scheduler": "simple", "denoise": 1.0
        }, "KSampler")
        self.connect(unet, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg_node, 0, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveAnimatedWEBP", {
            "filename_prefix": "ComfyUI", "fps": 16.0, "lossless": False, "quality": 90, "method": "default"
        }, "Save Video")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()
    
    def build_wan_i2v(self, prompt: str, image_file: str, negative: str = "",
                      width: int = 832, height: int = 480, num_frames: int = 81,
                      steps: int = 30, cfg: float = 6.0,
                      diffusion_model: str = "wan2.1_i2v_480p_14B_fp16.safetensors",
                      text_encoder: str = "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                      vae_name: str = "wan_2.1_vae.safetensors",
                      clip_vision_name: str = "clip_vision_h.safetensors",
                      seed: int = -1, **kwargs) -> dict:
        """Build Wan2.1 Image-to-Video pipeline."""
        unet = self.add_node("UNETLoader", {"unet_name": diffusion_model, "weight_dtype": "default"}, "Load Diffusion Model")
        clip = self.add_node("CLIPLoader", {"clip_name": text_encoder, "type": "wan"}, "Load CLIP")
        vae = self.add_node("VAELoader", {"vae_name": vae_name}, "Load VAE")
        clip_vision = self.add_node("CLIPVisionLoader", {"clip_name": clip_vision_name}, "Load CLIP Vision")
        
        img = self.add_node("LoadImage", {"image": image_file}, "Load Image")
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt}, "Positive")
        neg_node = self.add_node("CLIPTextEncode", {"text": negative or ""}, "Negative")
        self.connect(clip, 0, pos, "clip")
        self.connect(clip, 0, neg_node, "clip")
        
        # WanImageToVideo conditioning
        i2v = self.add_node("WanImageToVideo", {
            "width": width, "height": height, "length": num_frames, "batch_size": 1
        }, "Image to Video")
        self.connect(pos, 0, i2v, "positive")
        self.connect(neg_node, 0, i2v, "negative")
        self.connect(vae, 0, i2v, "vae")
        self.connect(clip_vision, 0, i2v, "clip_vision")
        self.connect(img, 0, i2v, "image")
        
        if seed == -1:
            seed = random.randint(0, 2**53)
        
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "uni_pc_bh2", "scheduler": "simple", "denoise": 1.0
        }, "KSampler")
        self.connect(unet, 0, ks, "model")
        self.connect(i2v, 0, ks, "positive")
        self.connect(i2v, 1, ks, "negative")
        self.connect(i2v, 2, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {}, "VAE Decode")
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveAnimatedWEBP", {
            "filename_prefix": "ComfyUI", "fps": 16.0, "lossless": False, "quality": 90, "method": "default"
        }, "Save Video")
        self.connect(vae_dec, 0, save, "images")
        
        return self.compile()


    # ===== Flux.2 Klein Text2Img =====
    def build_flux2_klein(self, prompt: str, negative: str = "",
                          width: int = 1024, height: int = 1024, steps: int = 20, cfg: float = 5.0,
                          diffusion_model: str = "flux-2-klein-base-4b-fp8.safetensors",
                          text_encoder: str = "qwen_3_4b.safetensors",
                          vae_name: str = "flux2-vae.safetensors",
                          seed: int = -1, **kwargs) -> dict:
        """Flux.2 Klein 4B text2img (UNETLoader + CLIPLoader(flux2) + SamplerCustomAdvanced)."""
        unet = self.add_node("UNETLoader", {"unet_name": diffusion_model, "weight_dtype": "default"})
        clip = self.add_node("CLIPLoader", {"clip_name": text_encoder, "type": "flux2", "device": "default"})
        vae = self.add_node("VAELoader", {"vae_name": vae_name})
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt})
        neg_node = self.add_node("CLIPTextEncode", {"text": negative or ""})
        self.connect(clip, 0, pos, "clip")
        self.connect(clip, 0, neg_node, "clip")
        
        guider = self.add_node("CFGGuider", {"cfg": cfg})
        self.connect(unet, 0, guider, "model")
        self.connect(pos, 0, guider, "positive")
        self.connect(neg_node, 0, guider, "negative")
        
        scheduler = self.add_node("Flux2Scheduler", {"steps": steps, "width": width, "height": height})
        sampler_select = self.add_node("KSamplerSelect", {"sampler_name": "euler"})
        noise = self.add_node("RandomNoise", {"noise_seed": seed if seed != -1 else random.randint(0, 2**53)})
        
        latent = self.add_node("EmptyFlux2LatentImage", {"width": width, "height": height, "batch_size": 1})
        
        advanced = self.add_node("SamplerCustomAdvanced", {})
        self.connect(noise, 0, advanced, "noise")
        self.connect(guider, 0, advanced, "guider")
        self.connect(sampler_select, 0, advanced, "sampler")
        self.connect(scheduler, 0, advanced, "sigmas")
        self.connect(latent, 0, advanced, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {})
        self.connect(advanced, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"})
        self.connect(vae_dec, 0, save, "images")
        return self.compile()

    # ===== Flux.2 Klein Distilled (4-step) =====
    def build_flux2_klein_distilled(self, prompt: str, width: int = 1024, height: int = 1024,
                                     diffusion_model: str = "flux-2-klein-4b-fp8.safetensors",
                                     text_encoder: str = "qwen_3_4b.safetensors",
                                     vae_name: str = "flux2-vae.safetensors",
                                     seed: int = -1, **kwargs) -> dict:
        """Flux.2 Klein Distilled (4 steps, cfg=1, ~1.2s)."""
        unet = self.add_node("UNETLoader", {"unet_name": diffusion_model, "weight_dtype": "default"})
        clip = self.add_node("CLIPLoader", {"clip_name": text_encoder, "type": "flux2", "device": "default"})
        vae = self.add_node("VAELoader", {"vae_name": vae_name})
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt})
        self.connect(clip, 0, pos, "clip")
        
        # Distilled uses ConditioningZeroOut for negative + cfg=1
        zero_neg = self.add_node("ConditioningZeroOut", {})
        self.connect(pos, 0, zero_neg, "conditioning")
        
        guider = self.add_node("CFGGuider", {"cfg": 1.0})
        self.connect(unet, 0, guider, "model")
        self.connect(pos, 0, guider, "positive")
        self.connect(zero_neg, 0, guider, "negative")
        
        scheduler = self.add_node("Flux2Scheduler", {"steps": 4, "width": width, "height": height})
        sampler_select = self.add_node("KSamplerSelect", {"sampler_name": "euler"})
        noise = self.add_node("RandomNoise", {"noise_seed": seed if seed != -1 else random.randint(0, 2**53)})
        latent = self.add_node("EmptyFlux2LatentImage", {"width": width, "height": height, "batch_size": 1})
        
        advanced = self.add_node("SamplerCustomAdvanced", {})
        self.connect(noise, 0, advanced, "noise")
        self.connect(guider, 0, advanced, "guider")
        self.connect(sampler_select, 0, advanced, "sampler")
        self.connect(scheduler, 0, advanced, "sigmas")
        self.connect(latent, 0, advanced, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {})
        self.connect(advanced, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"})
        self.connect(vae_dec, 0, save, "images")
        return self.compile()

    # ===== Flux Kontext Image Edit =====
    def build_flux_kontext(self, prompt: str, image_file: str,
                           diffusion_model: str = "flux1-dev-kontext_fp8_scaled.safetensors",
                           clip_l: str = "clip_l.safetensors",
                           t5xxl: str = "t5xxl_fp8_e4m3fn_scaled.safetensors",
                           vae_name: str = "ae.safetensors",
                           width: int = 1024, height: int = 1024,
                           steps: int = 20, guidance: float = 2.5,
                           seed: int = -1, **kwargs) -> dict:
        """Flux Kontext single-image edit."""
        unet = self.add_node("UNETLoader", {"unet_name": diffusion_model, "weight_dtype": "default"})
        clip = self.add_node("DualCLIPLoader", {
            "clip_name1": clip_l, "clip_name2": t5xxl, "type": "flux"
        })
        vae = self.add_node("VAELoader", {"vae_name": vae_name})
        
        img = self.add_node("LoadImage", {"image": image_file})
        vae_enc = self.add_node("VAEEncode", {})
        self.connect(img, 0, vae_enc, "pixels")
        self.connect(vae, 0, vae_enc, "vae")
        
        ref = self.add_node("ReferenceLatent", {})
        self.connect(vae_enc, 0, ref, "latent")
        
        pos = self.add_node("CLIPTextEncode", {"text": prompt})
        self.connect(clip, 0, pos, "clip")
        
        fg = self.add_node("FluxGuidance", {"guidance": guidance})
        self.connect(pos, 0, fg, "conditioning")
        
        zero_neg = self.add_node("ConditioningZeroOut", {})
        self.connect(pos, 0, zero_neg, "conditioning")
        
        latent = self.add_node("EmptySD3LatentImage", {"width": width, "height": height, "batch_size": 1})
        
        if seed == -1: seed = random.randint(0, 2**53)
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        })
        self.connect(unet, 0, ks, "model")
        self.connect(fg, 0, ks, "positive")
        self.connect(zero_neg, 0, ks, "negative")
        self.connect(ref, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {})
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"})
        self.connect(vae_dec, 0, save, "images")
        return self.compile()

    # ===== Qwen Image Edit =====
    def build_qwen_edit(self, prompt: str, image_file: str,
                        diffusion_model: str = "qwen_image_edit_2509_fp8_e4m3fn.safetensors",
                        text_encoder: str = "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                        vae_name: str = "qwen_image_vae.safetensors",
                        lora_name: str = "Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors",
                        steps: int = 4, seed: int = -1, **kwargs) -> dict:
        """Qwen Image Edit with Lightning LoRA (4 steps)."""
        unet = self.add_node("UNETLoader", {"unet_name": diffusion_model, "weight_dtype": "default"})
        clip = self.add_node("CLIPLoader", {"clip_name": text_encoder, "type": "qwen_image", "device": "default"})
        vae = self.add_node("VAELoader", {"vae_name": vae_name})
        
        cfg_norm = self.add_node("CFGNorm", {"strength": 1})
        self.connect(unet, 0, cfg_norm, "model")
        
        aura = self.add_node("ModelSamplingAuraFlow", {"shift": 3.0})
        self.connect(cfg_norm, 0, aura, "model")
        
        lora = self.add_node("LoraLoaderModelOnly", {"lora_name": lora_name, "strength_model": 1.0})
        self.connect(aura, 0, lora, "model")
        
        img = self.add_node("LoadImage", {"image": image_file})
        scale = self.add_node("ImageScaleToTotalPixels", {"upscale_method": "lanczos", "megapixels": 1.0})
        self.connect(img, 0, scale, "image")
        
        vae_enc = self.add_node("VAEEncode", {})
        self.connect(scale, 0, vae_enc, "pixels")
        self.connect(vae, 0, vae_enc, "vae")
        
        pos = self.add_node("TextEncodeQwenImageEditPlus", {"text": prompt})
        self.connect(clip, 0, pos, "clip")
        self.connect(scale, 0, pos, "image")
        
        neg_node = self.add_node("TextEncodeQwenImageEditPlus", {"text": ""})
        self.connect(clip, 0, neg_node, "clip")
        self.connect(scale, 0, neg_node, "image")
        
        if seed == -1: seed = random.randint(0, 2**53)
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        })
        self.connect(lora, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(neg_node, 0, ks, "negative")
        self.connect(vae_enc, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecode", {})
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(vae, 0, vae_dec, "vae")
        
        save = self.add_node("SaveImage", {"filename_prefix": "ComfyUI"})
        self.connect(vae_dec, 0, save, "images")
        return self.compile()

    # ===== ACE-Step Audio (Text-to-Song) =====
    def build_audio_song(self, prompt: str, duration: float = 60.0,
                         checkpoint: str = "ace_step_v1_3.5b.safetensors",
                         seed: int = -1, **kwargs) -> dict:
        """ACE-Step text-to-song generation."""
        ckpt = self.add_node("CheckpointLoaderSimple", {"ckpt_name": checkpoint})
        
        pos = self.add_node("TextEncodeAceStepAudio", {"text": prompt})
        self.connect(ckpt, 1, pos, "clip")
        
        zero_neg = self.add_node("ConditioningZeroOut", {})
        self.connect(pos, 0, zero_neg, "conditioning")
        
        empty = self.add_node("EmptyAceStepLatentAudio", {"seconds": duration, "batch_size": 1})
        
        # Apply CFG operation
        cfg_op = self.add_node("LatentApplyOperationCFG", {})
        reinhard = self.add_node("LatentOperationTonemapReinhard", {})
        self.connect(reinhard, 0, cfg_op, "operation")
        
        sampling = self.add_node("ModelSamplingSD3", {"shift": 1.0})
        self.connect(ckpt, 0, sampling, "model")
        self.connect(cfg_op, 0, sampling, "model")
        
        if seed == -1: seed = random.randint(0, 2**53)
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": 50, "cfg": 5.0,
            "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        })
        self.connect(sampling, 0, ks, "model")
        self.connect(pos, 0, ks, "positive")
        self.connect(zero_neg, 0, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        dec = self.add_node("VAEDecodeAudio", {})
        self.connect(ks, 0, dec, "samples")
        self.connect(ckpt, 2, dec, "vae")
        
        save = self.add_node("SaveAudio", {"filename_prefix": "ComfyUI"})
        self.connect(dec, 0, save, "audio")
        return self.compile()

    # ===== Hunyuan3D (Image-to-3D) =====
    def build_3d_hunyuan(self, image_file: str,
                         checkpoint: str = "hunyuan_3d_v2.1.safetensors",
                         steps: int = 30, cfg: float = 5.0, seed: int = -1, **kwargs) -> dict:
        """Hunyuan3D 2.1 image-to-3D mesh generation."""
        ckpt = self.add_node("ImageOnlyCheckpointLoader", {"ckpt_name": checkpoint})
        
        img = self.add_node("LoadImage", {"image": image_file})
        vision_enc = self.add_node("CLIPVisionEncode", {})
        self.connect(ckpt, 1, vision_enc, "clip_vision")  # CLIP_VISION from checkpoint
        self.connect(img, 0, vision_enc, "image")
        
        cond = self.add_node("Hunyuan3Dv2Conditioning", {})
        self.connect(vision_enc, 0, cond, "clip_vision_output")
        
        aura = self.add_node("ModelSamplingAuraFlow", {"shift": 1.0})
        self.connect(ckpt, 0, aura, "model")
        
        empty = self.add_node("EmptyLatentHunyuan3Dv2", {"resolution": 384, "batch_size": 1})
        
        if seed == -1: seed = random.randint(0, 2**53)
        ks = self.add_node("KSampler", {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0
        })
        self.connect(aura, 0, ks, "model")
        self.connect(cond, 0, ks, "positive")
        self.connect(cond, 1, ks, "negative")
        self.connect(empty, 0, ks, "latent_image")
        
        vae_dec = self.add_node("VAEDecodeHunyuan3D", {})
        self.connect(ks, 0, vae_dec, "samples")
        self.connect(ckpt, 2, vae_dec, "vae")
        
        mesh = self.add_node("VoxelToMesh", {"threshold": 0.5})
        self.connect(vae_dec, 0, mesh, "voxel")
        
        return self.compile()


PIPELINE_BUILDERS = {
    # Standard SD/SDXL
    "text2img": "build_text2img",
    "text2img_sdxl": "build_text2img",
    "img2img": "build_img2img",
    "img2img_sdxl": "build_img2img",
    "text2img_lora": "build_text2img_lora",
    "text2img+lora": "build_text2img_lora",
    "lora_sdxl": "build_text2img_lora",
    "controlnet": "build_controlnet",
    "controlnet_sdxl": "build_controlnet",
    "text2img+controlnet": "build_controlnet",
    "multi_controlnet": "build_multi_controlnet",
    "controlnet+controlnet": "build_multi_controlnet",
    "inpaint": "build_inpaint",
    "inpaint_sdxl": "build_inpaint",
    "outpaint": "build_outpaint",
    "outpaint_sdxl": "build_outpaint",
    "upscale": "build_upscale",
    "upscale_esrgan": "build_upscale",
    "text2img+upscale": "build_text2img_upscale",
    # Flux.1
    "flux": "build_flux_text2img",
    "flux_text2img": "build_flux_text2img",
    "text2img_flux1": "build_flux_text2img",
    # Flux.2 Klein
    "flux2_klein": "build_flux2_klein",
    "text2img_flux2_klein": "build_flux2_klein",
    "flux2_klein_base": "build_flux2_klein",
    "flux2_klein_distilled": "build_flux2_klein_distilled",
    "text2img_flux2_distilled": "build_flux2_klein_distilled",
    # Flux Kontext
    "flux_kontext": "build_flux_kontext",
    "img_edit_flux_kontext": "build_flux_kontext",
    "kontext": "build_flux_kontext",
    # Qwen Image Edit
    "qwen_edit": "build_qwen_edit",
    "img_edit_qwen": "build_qwen_edit",
    "qwen": "build_qwen_edit",
    # Video
    "wan_t2v": "build_wan_t2v",
    "wan_i2v": "build_wan_i2v",
    "video_wan21_t2v": "build_wan_t2v",
    "video_wan21_i2v": "build_wan_i2v",
    "video": "build_wan_t2v",
    # Audio
    "audio_song": "build_audio_song",
    "audio_t2a": "build_audio_song",
    "ace_step": "build_audio_song",
    # 3D
    "3d_hunyuan": "build_3d_hunyuan",
    "hunyuan3d": "build_3d_hunyuan",
    "image_to_3d": "build_3d_hunyuan",
}


def compile_pipeline(pipeline: str, params: dict) -> dict:
    """Compile a pipeline using the pure compiler."""
    builder_name = PIPELINE_BUILDERS.get(pipeline)
    if not builder_name:
        raise ValueError(f"Unknown pipeline: {pipeline}. Available: {list(PIPELINE_BUILDERS.keys())}")
    
    compiler = WorkflowCompiler()
    builder = getattr(compiler, builder_name)
    return builder(**params)


# =========================================================================
# Execution Engine v2: Three reliable paths (workspace setContent REMOVED)
# =========================================================================
# Path A: Template + nodeInfoList (image tasks, most reliable)
# Path B: Standard API via runninghub.py (video/audio/3D, 179 endpoints)
# Path C: AI App via runninghub_app.py (complex workflows like motion transfer)
# =========================================================================

# Template → pipeline mapping
TEMPLATE_MAP = {
    "text2img": "9999",
    "img2img": "9997",
    "text2img_lora": "9998",
    "img2img_lora": "9995",
    "img2img_upscale": "9996",
}

# Pipeline → template node mapping (nodeId + fieldName for each parameter)
TEMPLATE_NODES = {
    "9999": {  # text2img
        "prompt":    {"nodeId": "6",  "fieldName": "text"},
        "negative":  {"nodeId": "7",  "fieldName": "text"},
        "width":     {"nodeId": "5",  "fieldName": "width"},
        "height":    {"nodeId": "5",  "fieldName": "height"},
        "steps":     {"nodeId": "3",  "fieldName": "steps"},
        "cfg":       {"nodeId": "3",  "fieldName": "cfg"},
        "seed":      {"nodeId": "3",  "fieldName": "seed"},
        "sampler":   {"nodeId": "3",  "fieldName": "sampler_name"},
        "scheduler": {"nodeId": "3",  "fieldName": "scheduler"},
        "checkpoint": {"nodeId": "4", "fieldName": "ckpt_name"},
    },
    "9997": {  # img2img
        "image":     {"nodeId": "10", "fieldName": "image"},
        "prompt":    {"nodeId": "21", "fieldName": "text1"},
        "negative":  {"nodeId": "7",  "fieldName": "text"},
        "denoise":   {"nodeId": "3",  "fieldName": "denoise"},
        "steps":     {"nodeId": "3",  "fieldName": "steps"},
        "cfg":       {"nodeId": "3",  "fieldName": "cfg"},
        "seed":      {"nodeId": "3",  "fieldName": "seed"},
        "sampler":   {"nodeId": "3",  "fieldName": "sampler_name"},
        "checkpoint": {"nodeId": "4", "fieldName": "ckpt_name"},
    },
    "9998": {  # text2img + lora
        "prompt":    {"nodeId": "6",  "fieldName": "text"},
        "negative":  {"nodeId": "7",  "fieldName": "text"},
        "width":     {"nodeId": "5",  "fieldName": "width"},
        "height":    {"nodeId": "5",  "fieldName": "height"},
        "steps":     {"nodeId": "3",  "fieldName": "steps"},
        "cfg":       {"nodeId": "3",  "fieldName": "cfg"},
        "seed":      {"nodeId": "3",  "fieldName": "seed"},
        "lora":      {"nodeId": "10", "fieldName": "lora_name"},
        "lora_strength": {"nodeId": "10", "fieldName": "strength_model"},
        "checkpoint": {"nodeId": "4", "fieldName": "ckpt_name"},
    },
    "9995": {  # img2img + lora
        "image":     {"nodeId": "12", "fieldName": "image"},
        "prompt":    {"nodeId": "21", "fieldName": "text1"},
        "negative":  {"nodeId": "7",  "fieldName": "text"},
        "denoise":   {"nodeId": "3",  "fieldName": "denoise"},
        "steps":     {"nodeId": "3",  "fieldName": "steps"},
        "cfg":       {"nodeId": "3",  "fieldName": "cfg"},
        "seed":      {"nodeId": "3",  "fieldName": "seed"},
        "lora":      {"nodeId": "10", "fieldName": "lora_name"},
        "lora_strength": {"nodeId": "10", "fieldName": "strength_model"},
        "checkpoint": {"nodeId": "4", "fieldName": "ckpt_name"},
    },
    "9996": {  # img2img + upscale
        "image":     {"nodeId": "10", "fieldName": "image"},
        "prompt":    {"nodeId": "21", "fieldName": "text1"},
        "negative":  {"nodeId": "7",  "fieldName": "text"},
        "denoise":   {"nodeId": "3",  "fieldName": "denoise"},
        "steps":     {"nodeId": "3",  "fieldName": "steps"},
        "cfg":       {"nodeId": "3",  "fieldName": "cfg"},
        "seed":      {"nodeId": "3",  "fieldName": "seed"},
        "checkpoint": {"nodeId": "4", "fieldName": "ckpt_name"},
    },
}

# AI App workflow IDs for complex tasks
AI_APP_WORKFLOWS = {
    "motion_transfer": "1994717321291833345",       # 动作迁移升级版
    "motion_transfer_v4": "1975951975441412098",     # Wan2.2 Animate V4.1
    "dance_150": "1933689617772404738",              # 150帧跳舞高清
    "face_swap": "2027593896020152321",              # AI 换脸
}

# Locate runninghub scripts (OpenClaw_RH_Skills)
RH_SKILLS_PATHS = [
    Path("/tmp/OpenClaw_RH_Skills/runninghub/scripts"),
    Path.home() / ".openclaw/workspace/skills/runninghub-skills/scripts",
]

def _find_rh_script(name: str) -> str:
    """Find runninghub script path."""
    for base in RH_SKILLS_PATHS:
        p = base / name
        if p.exists():
            return str(p)
    return name  # fallback to PATH


def upload_file(file_path: str) -> str:
    """Upload a local file to RunningHub, return the remote filename."""
    api_key = resolve_api_key()
    r = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/upload',
        '-F', f'apiKey={api_key}',
        '-F', f'file=@{file_path}'
    ], capture_output=True, text=True)
    data = json.loads(r.stdout)
    fname = data.get('data', {}).get('fileName', '')
    if not fname:
        raise RuntimeError(f"Upload failed: {r.stdout[:200]}")
    return fname


def poll_task(task_id: str, max_wait: int = 600, interval: int = 10) -> dict:
    """Poll a RunningHub task until completion."""
    api_key = resolve_api_key()
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval
        sr = subprocess.run([
            'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/status',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({"apiKey": api_key, "taskId": task_id})
        ], capture_output=True, text=True)
        status = json.loads(sr.stdout).get("data", "")
        if isinstance(status, dict):
            status = status.get("taskStatus", "")
        print(f"  [{elapsed}s] {status}", file=sys.stderr)

        if status == "SUCCESS":
            out_r = subprocess.run([
                'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/outputs',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({"apiKey": api_key, "taskId": task_id})
            ], capture_output=True, text=True)
            outputs = json.loads(out_r.stdout).get("data", [])
            return {"status": "SUCCESS", "task_id": task_id, "outputs": outputs}
        elif status in ("FAILED", "TIMEOUT"):
            return {"status": status, "task_id": task_id}

    return {"status": "TIMEOUT", "task_id": task_id}


def execute_via_template(pipeline: str, params: dict) -> dict:
    """Path A: Execute via official template + nodeInfoList (most reliable)."""
    template_id = TEMPLATE_MAP.get(pipeline)
    if not template_id:
        raise ValueError(f"No template for pipeline '{pipeline}'. Available: {list(TEMPLATE_MAP.keys())}")

    node_map = TEMPLATE_NODES.get(template_id, {})
    api_key = resolve_api_key()

    # Build nodeInfoList from params
    node_info_list = []
    for param_name, value in params.items():
        if param_name in node_map and value is not None:
            entry = {
                "nodeId": node_map[param_name]["nodeId"],
                "fieldName": node_map[param_name]["fieldName"],
                "fieldValue": str(value),
            }
            node_info_list.append(entry)

    # Handle image upload if needed
    if "image" in params and params["image"] and not params["image"].startswith("api/"):
        remote = upload_file(params["image"])
        for entry in node_info_list:
            if entry["fieldName"] == "image":
                entry["fieldValue"] = remote

    # Random seed if -1
    for entry in node_info_list:
        if entry["fieldName"] == "seed" and entry["fieldValue"] == "-1":
            entry["fieldValue"] = str(random.randint(0, 2**53))

    print(f"🎯 Path A: Template {template_id} + {len(node_info_list)} params", file=sys.stderr)

    r = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{RH_API}/task/openapi/create',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "apiKey": api_key,
            "workflowId": template_id,
            "nodeInfoList": node_info_list,
        })
    ], capture_output=True, text=True)

    resp = json.loads(r.stdout)
    task_id = resp.get("data", {}).get("taskId", "") if isinstance(resp.get("data"), dict) else ""
    if not task_id:
        raise RuntimeError(f"Template execute failed: {r.stdout[:300]}")

    print(f"📝 Task: {task_id}", file=sys.stderr)
    return poll_task(task_id)


def execute_via_api(endpoint: str, params: dict) -> dict:
    """Path B: Execute via runninghub.py standard API (179 endpoints)."""
    script = _find_rh_script("runninghub.py")
    api_key = resolve_api_key()

    cmd = ["python3", script, endpoint]

    # Map common params to CLI flags
    if params.get("prompt"):
        cmd.extend(["--prompt", params["prompt"]])
    if params.get("image"):
        cmd.extend(["--image", params["image"]])
    if params.get("negative"):
        cmd.extend(["--negative", params["negative"]])
    if params.get("output"):
        cmd.extend(["-o", params["output"]])

    env = os.environ.copy()
    env["RUNNINGHUB_API_KEY"] = api_key

    print(f"🌐 Path B: API endpoint {endpoint}", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)

    if r.returncode != 0:
        raise RuntimeError(f"API call failed: {r.stderr[:300]}")

    # Parse output (script prints JSON result)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"status": "SUCCESS", "raw_output": r.stdout[:500]}


def execute_via_ai_app(webapp_id: str, nodes: dict = None, files: dict = None,
                       instance_type: str = "plus", output: str = None) -> dict:
    """Path C: Execute via runninghub_app.py AI App."""
    script = _find_rh_script("runninghub_app.py")
    api_key = resolve_api_key()

    cmd = ["python3", script, "--run", webapp_id]

    # Add node overrides
    if nodes:
        for node_spec, value in nodes.items():
            cmd.extend(["--node", f"{node_spec}={value}"])

    # Add file uploads
    if files:
        for node_spec, filepath in files.items():
            cmd.extend(["--file", f"{node_spec}={filepath}"])

    cmd.extend(["--instance-type", instance_type])

    if output:
        cmd.extend(["-o", output])

    env = os.environ.copy()
    env["RUNNINGHUB_API_KEY"] = api_key

    print(f"🔧 Path C: AI App {webapp_id}", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900)

    if r.returncode != 0:
        raise RuntimeError(f"AI App failed: {r.stderr[:300]}\n{r.stdout[:300]}")

    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"status": "SUCCESS", "raw_output": r.stdout[:500]}


def execute(pipeline: str, params: dict) -> dict:
    """Smart router: pick the best execution path for the given pipeline."""
    # Path A: template-based (image tasks)
    if pipeline in TEMPLATE_MAP:
        return execute_via_template(pipeline, params)

    # Path C: AI App (complex workflows)
    if pipeline in AI_APP_WORKFLOWS:
        webapp_id = AI_APP_WORKFLOWS[pipeline]
        return execute_via_ai_app(webapp_id, params.get("nodes"), params.get("files"),
                                  params.get("instance_type", "plus"),
                                  params.get("output"))

    # Path B: Standard API (video/audio/3D by endpoint name)
    return execute_via_api(pipeline, params)


# Legacy alias (DEPRECATED — workspace setContent is unreliable)
def save_and_execute(api_format: dict, workspace_id: str = WORKSPACE_ID) -> dict:
    """DEPRECATED: workspace setContent → create is UNRELIABLE.
    Use execute_via_template() or execute_via_ai_app() instead.
    This function now raises an error to prevent silent failures."""
    raise RuntimeError(
        "⚠️ save_and_execute() is DEPRECATED. workspace setContent execution is unreliable "
        "(executes cached old workflow, not the newly saved one). "
        "Use execute_via_template(), execute_via_api(), or execute_via_ai_app() instead."
    )


def main():
    parser = argparse.ArgumentParser(description="ComfyUI Workflow Compiler")
    parser.add_argument("--pipeline", "-p", required=True, help="Pipeline type")
    parser.add_argument("--prompt", help="Positive prompt")
    parser.add_argument("--negative", help="Negative prompt")
    parser.add_argument("--image", help="Input image (img2img)")
    parser.add_argument("--control-image", help="Control image (ControlNet)")
    parser.add_argument("--preprocessor", default="CannyEdgePreprocessor", help="ControlNet preprocessor")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=7.0)
    parser.add_argument("--guidance", type=float, default=3.5, help="Flux guidance")
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--denoise", type=float, default=0.5)
    parser.add_argument("--checkpoint", default="sd_xl_base_1.0.safetensors")
    parser.add_argument("--lora", help="LoRA model name")
    parser.add_argument("--lora-strength", type=float, default=0.7)
    parser.add_argument("--controlnet-model", default="controlnet-union-sdxl-1.0.safetensors")
    parser.add_argument("--controlnet-strength", type=float, default=0.7)
    parser.add_argument("--sampler", default="dpmpp_2m_sde")
    parser.add_argument("--scheduler", default="karras")
    parser.add_argument("--upscale-model", default="4x-ESRGAN.pth")
    parser.add_argument("--grow-mask", type=int, default=6, help="Inpaint mask grow")
    parser.add_argument("--pad-left", type=int, default=0, help="Outpaint left padding")
    parser.add_argument("--pad-top", type=int, default=0, help="Outpaint top padding")
    parser.add_argument("--pad-right", type=int, default=256, help="Outpaint right padding")
    parser.add_argument("--pad-bottom", type=int, default=0, help="Outpaint bottom padding")
    parser.add_argument("--feathering", type=int, default=40, help="Outpaint feathering")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--save", help="Save to file")
    parser.add_argument("--workspace", default=WORKSPACE_ID)
    args = parser.parse_args()
    
    params = {
        "prompt": args.prompt or "a beautiful landscape",
        "negative": args.negative or "",
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "cfg": args.cfg,
        "seed": args.seed,
        "denoise": args.denoise,
        "checkpoint": args.checkpoint,
        "sampler": args.sampler,
        "scheduler": args.scheduler,
        "guidance": args.guidance,
    }
    if args.image:
        params["image_file"] = args.image
    if args.control_image:
        params["control_image"] = args.control_image
    if args.preprocessor:
        params["preprocessor"] = args.preprocessor
    if args.lora:
        params["lora_name"] = args.lora
        params["lora_strength"] = args.lora_strength
    if args.controlnet_model:
        params["controlnet_model"] = args.controlnet_model
    if args.controlnet_strength:
        params["strength"] = args.controlnet_strength
    if args.upscale_model:
        params["upscale_model"] = args.upscale_model
    if args.grow_mask:
        params["grow_mask"] = args.grow_mask
    params["left"] = args.pad_left
    params["top"] = args.pad_top
    params["right"] = args.pad_right
    params["bottom"] = args.pad_bottom
    params["feathering"] = args.feathering
    
    print(f"🔧 Compiling pipeline: {args.pipeline}", file=sys.stderr)
    api_format = compile_pipeline(args.pipeline, params)
    
    node_summary = [(nid, n["class_type"]) for nid, n in api_format.items()]
    print(f"📋 Compiled {len(api_format)} nodes:", file=sys.stderr)
    for nid, ct in node_summary:
        print(f"  [{nid}] {ct}", file=sys.stderr)
    
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(api_format, f, indent=2)
        print(f"💾 Saved to {args.save}", file=sys.stderr)
    
    if args.execute:
        # Use new execution engine: template+nodeInfoList for image pipelines
        template_params = {
            "prompt": args.prompt,
            "negative": args.negative,
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "cfg": args.cfg,
            "seed": args.seed,
            "denoise": args.denoise,
            "checkpoint": args.checkpoint,
            "sampler": args.sampler,
            "scheduler": args.scheduler,
        }
        if args.image:
            template_params["image"] = args.image
        if args.lora:
            template_params["lora"] = args.lora
            template_params["lora_strength"] = args.lora_strength

        try:
            result = execute(args.pipeline, template_params)
        except (ValueError, RuntimeError) as e:
            print(f"⚠️ Smart execute failed: {e}", file=sys.stderr)
            print(f"💡 Falling back to JSON output (use template+nodeInfoList manually)", file=sys.stderr)
            result = {"status": "COMPILE_ONLY", "api_format": api_format}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif not args.save:
        print(json.dumps(api_format, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
