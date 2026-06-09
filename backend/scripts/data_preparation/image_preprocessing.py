import os
from PIL import Image, ImageOps
from pathlib import Path

def normalize_image(input_path, output_dir, target_size=(384, 384)):
    """
    Standardizes image dimensions and contrast without destroying data.
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
        
        # Save processed image
        base_name = Path(input_path).name
        output_path = Path(output_dir) / base_name
        
        # Overwrite if exists (prevents disk bloat on multiple pipeline runs)
        img.save(output_path, quality=95)
        return str(output_path)
    except Exception as e:
        print(f"Error normalizing image {input_path}: {e}")
        return None
