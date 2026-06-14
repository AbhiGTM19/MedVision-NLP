import os
from PIL import Image, ImageOps
from pathlib import Path

def normalize_image(input_path, output_dir, target_size=(384, 384), source_prefix=None):
    """
    Standardizes image dimensions and contrast without destroying data.

    Args:
        input_path: Path to the raw input image.
        output_dir: Directory to save the processed image.
        target_size: Target (width, height) for the output image.
        source_prefix: Optional prefix to namespace output filenames by source,
                       preventing cross-source filename collisions (e.g., "synth", "hw").
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        img = Image.open(input_path)
        
        # CRITICAL: Read EXIF orientation tags and rotate accordingly (fixes upside down mobile uploads)
        img = ImageOps.exif_transpose(img)
        
        # Convert to RGB if necessary (e.g. RGBA or Grayscale)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Exact Resize & Pad (maintains aspect ratio, fills with white, strict TrOCR dimensions)
        img = ImageOps.pad(img, target_size, method=Image.Resampling.LANCZOS, color=(255, 255, 255))
        
        # Basic Contrast Normalization
        img = ImageOps.autocontrast(img, cutoff=1)
        
        # Save processed image (namespaced by source to prevent cross-source collisions)
        base_name = Path(input_path).name
        if source_prefix:
            output_path = Path(output_dir) / f"{source_prefix}_{base_name}"
        else:
            output_path = Path(output_dir) / base_name
        
        # Overwrite if exists (prevents disk bloat on multiple pipeline runs)
        img.save(output_path, quality=95)
        return str(output_path)
    except Exception as e:
        print(f"Error normalizing image {input_path}: {e}")
        return None
