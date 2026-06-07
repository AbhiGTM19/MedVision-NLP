import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    if len(coords) == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess_image(img_path, save_path):
    img = cv2.imread(img_path)
    if img is None:
        return False
        
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Denoise (Gaussian blur)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive Thresholding (Binarization)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Deskewing
    deskewed = deskew(thresh)
    
    # Invert back to normal text (black text on white background)
    final_img = cv2.bitwise_not(deskewed)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, final_img)
    return True

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "dataset" / "raw"
    processed_dir = base_dir / "dataset" / "processed" / "ocr_images"
    
    image_paths = []
    for ext in ["*.jpg", "*.png", "*.jpeg"]:
        image_paths.extend(raw_dir.rglob(ext))
        
    print(f"Found {len(image_paths)} images for OCR preprocessing.")
    
    if not image_paths:
        print("No images found. Please ensure you have downloaded the image datasets into dataset/raw/.")
        return

    os.makedirs(processed_dir, exist_ok=True)
    
    success_count = 0
    for img_path in tqdm(image_paths, desc="Preprocessing OCR Images"):
        # Prevent naming collisions by prefixing the parent folder name
        rel_name = f"{img_path.parent.name}_{img_path.name}"
        save_path = str(processed_dir / rel_name)
        if preprocess_image(str(img_path), save_path):
            success_count += 1
            
    print(f"Preprocessing complete. {success_count}/{len(image_paths)} images successfully processed.")

if __name__ == "__main__":
    main()
