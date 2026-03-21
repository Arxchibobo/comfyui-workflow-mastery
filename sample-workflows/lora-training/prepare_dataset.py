#!/usr/bin/env python3
"""
LoRA Training Dataset Preparation Script
Automates: image validation, resizing, duplicate detection, directory structure creation

Usage:
  python prepare_dataset.py \
    --input_dir ./raw_images \
    --output_dir ./training_data \
    --trigger_word "sks" \
    --class_token "person" \
    --repeats 10 \
    --resolution 512 \
    --create_reg  # Generate regularization directory structure

Requirements: pip install Pillow imagehash
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False


def get_image_info(path: Path) -> dict:
    """Get image metadata."""
    if not HAS_PIL:
        return {"path": str(path), "valid": True, "width": 0, "height": 0}
    
    try:
        with Image.open(path) as img:
            return {
                "path": str(path),
                "valid": True,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "megapixels": round(img.width * img.height / 1_000_000, 2),
            }
    except Exception as e:
        return {"path": str(path), "valid": False, "error": str(e)}


def find_duplicates(image_paths: list, threshold: int = 5) -> list:
    """Find near-duplicate images using perceptual hashing."""
    if not HAS_IMAGEHASH or not HAS_PIL:
        print("⚠️  imagehash/PIL not available, skipping duplicate detection")
        return []
    
    hashes = {}
    duplicates = []
    
    for path in image_paths:
        try:
            with Image.open(path) as img:
                h = imagehash.phash(img)
                for existing_path, existing_hash in hashes.items():
                    if abs(h - existing_hash) <= threshold:
                        duplicates.append((str(path), str(existing_path)))
                        break
                else:
                    hashes[path] = h
        except Exception:
            continue
    
    return duplicates


def resize_image(input_path: Path, output_path: Path, resolution: int):
    """Resize image to target resolution, maintaining aspect ratio with center crop."""
    if not HAS_PIL:
        shutil.copy2(input_path, output_path)
        return
    
    with Image.open(input_path) as img:
        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize maintaining aspect ratio (larger dimension fits)
        w, h = img.size
        scale = max(resolution / w, resolution / h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Center crop to exact resolution
        left = (new_w - resolution) // 2
        top = (new_h - resolution) // 2
        img = img.crop((left, top, left + resolution, top + resolution))
        
        img.save(output_path, quality=95)


def create_caption_file(image_path: Path, trigger_word: str, class_token: str):
    """Create a basic caption file for an image."""
    caption_path = image_path.with_suffix(".txt")
    if not caption_path.exists():
        caption = f"{trigger_word} {class_token}"
        caption_path.write_text(caption)
        return True
    return False


def validate_dataset(data_dir: Path) -> dict:
    """Validate a prepared dataset directory."""
    stats = {
        "total_images": 0,
        "total_captions": 0,
        "missing_captions": [],
        "orphan_captions": [],
        "image_sizes": defaultdict(int),
    }
    
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    
    images = set()
    captions = set()
    
    for f in data_dir.rglob("*"):
        if f.suffix.lower() in image_exts:
            images.add(f.stem)
            stats["total_images"] += 1
            if HAS_PIL:
                try:
                    with Image.open(f) as img:
                        stats["image_sizes"][f"{img.width}x{img.height}"] += 1
                except:
                    pass
        elif f.suffix == ".txt":
            captions.add(f.stem)
            stats["total_captions"] += 1
    
    stats["missing_captions"] = list(images - captions)
    stats["orphan_captions"] = list(captions - images)
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="LoRA Training Dataset Preparation")
    parser.add_argument("--input_dir", type=str, required=True, help="Raw images directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Output training directory")
    parser.add_argument("--trigger_word", type=str, default="sks", help="Trigger word for LoRA")
    parser.add_argument("--class_token", type=str, default="person", help="Class token")
    parser.add_argument("--repeats", type=int, default=10, help="Training repeats per image")
    parser.add_argument("--resolution", type=int, default=512, help="Target resolution")
    parser.add_argument("--min_resolution", type=int, default=256, help="Minimum source resolution")
    parser.add_argument("--create_reg", action="store_true", help="Create regularization directory")
    parser.add_argument("--check_duplicates", action="store_true", help="Check for near-duplicate images")
    parser.add_argument("--validate_only", action="store_true", help="Only validate existing dataset")
    parser.add_argument("--dry_run", action="store_true", help="Show what would be done without doing it")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Validate only mode
    if args.validate_only:
        print(f"📊 Validating dataset at: {output_dir}")
        stats = validate_dataset(output_dir)
        print(f"   Images: {stats['total_images']}")
        print(f"   Captions: {stats['total_captions']}")
        print(f"   Missing captions: {stats['missing_captions']}")
        print(f"   Orphan captions: {stats['orphan_captions']}")
        print(f"   Sizes: {dict(stats['image_sizes'])}")
        return
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Scan input images
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in image_exts]
    
    print(f"📁 Found {len(image_files)} images in {input_dir}")
    
    # Analyze images
    print("\n🔍 Analyzing images...")
    valid_images = []
    rejected = []
    
    for img_path in sorted(image_files):
        info = get_image_info(img_path)
        if not info["valid"]:
            rejected.append((img_path, "invalid"))
            continue
        if HAS_PIL and (info["width"] < args.min_resolution or info["height"] < args.min_resolution):
            rejected.append((img_path, f"too small: {info['width']}x{info['height']}"))
            continue
        valid_images.append(img_path)
    
    print(f"   ✅ Valid: {len(valid_images)}")
    print(f"   ❌ Rejected: {len(rejected)}")
    for path, reason in rejected:
        print(f"      - {path.name}: {reason}")
    
    # Check duplicates
    if args.check_duplicates and valid_images:
        print("\n🔍 Checking for duplicates...")
        dupes = find_duplicates(valid_images)
        if dupes:
            print(f"   ⚠️  Found {len(dupes)} near-duplicate pairs:")
            for a, b in dupes:
                print(f"      - {Path(a).name} ≈ {Path(b).name}")
        else:
            print("   ✅ No duplicates found")
    
    if args.dry_run:
        print(f"\n🏁 DRY RUN: Would create dataset with {len(valid_images)} images")
        print(f"   Output: {output_dir}/{args.repeats}_{args.trigger_word}_{args.class_token}/")
        print(f"   Resolution: {args.resolution}x{args.resolution}")
        total_steps_per_epoch = len(valid_images) * args.repeats
        print(f"   Steps per epoch: {total_steps_per_epoch}")
        print(f"   Recommended epochs: 2-3 → {total_steps_per_epoch * 2}-{total_steps_per_epoch * 3} total steps")
        return
    
    # Create output directory
    subset_name = f"{args.repeats}_{args.trigger_word}_{args.class_token}"
    subset_dir = output_dir / subset_name
    subset_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 Creating dataset at: {subset_dir}")
    
    # Process images
    for i, img_path in enumerate(sorted(valid_images)):
        out_name = f"image_{i+1:04d}.png"
        out_path = subset_dir / out_name
        
        # Resize
        resize_image(img_path, out_path, args.resolution)
        
        # Create caption
        created = create_caption_file(out_path, args.trigger_word, args.class_token)
        
        print(f"   [{i+1}/{len(valid_images)}] {img_path.name} → {out_name}" + 
              (" (+ caption)" if created else ""))
    
    # Create regularization directory
    if args.create_reg:
        reg_dir = output_dir / f"1_{args.class_token}"
        reg_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Created regularization directory: {reg_dir}")
        print(f"   → Generate {len(valid_images) * 3}-{len(valid_images) * 5} images here")
        print(f"   → Use base model to generate '{args.class_token}' images")
    
    # Summary
    total_steps_per_epoch = len(valid_images) * args.repeats
    print(f"\n✅ Dataset ready!")
    print(f"   Images: {len(valid_images)}")
    print(f"   Repeats: {args.repeats}")
    print(f"   Steps per epoch: {total_steps_per_epoch}")
    print(f"   Recommended: 2-3 epochs → {total_steps_per_epoch * 2}-{total_steps_per_epoch * 3} total steps")
    
    # Write dataset info
    info = {
        "trigger_word": args.trigger_word,
        "class_token": args.class_token,
        "resolution": args.resolution,
        "num_images": len(valid_images),
        "repeats": args.repeats,
        "steps_per_epoch": total_steps_per_epoch,
        "recommended_epochs": "2-3",
        "recommended_total_steps": f"{total_steps_per_epoch * 2}-{total_steps_per_epoch * 3}",
    }
    info_path = output_dir / "dataset_info.json"
    info_path.write_text(json.dumps(info, indent=2))
    print(f"   Info saved to: {info_path}")


if __name__ == "__main__":
    main()
