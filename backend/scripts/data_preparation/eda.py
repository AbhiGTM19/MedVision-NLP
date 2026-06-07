import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
import glob
from pathlib import Path

# Fix for matplotlib headless environments
import matplotlib
matplotlib.use('Agg')

def perform_nlp_eda(raw_dir, eda_dir):
    print("--- Starting NLP EDA ---")
    mtsamples_path = raw_dir / "mtsamples.csv"
    if not mtsamples_path.exists():
        print("mtsamples.csv not found.")
        return
        
    df = pd.read_csv(mtsamples_path)
    
    # 1. Basic Stats
    total_records = len(df)
    missing_transcriptions = df['transcription'].isna().sum()
    print(f"Total Records: {total_records}")
    print(f"Missing Transcriptions: {missing_transcriptions}")
    
    # Drop NAs
    df = df.dropna(subset=['transcription', 'medical_specialty'])
    
    # 2. Text Length Distribution
    df['text_length'] = df['transcription'].apply(lambda x: len(str(x).split()))
    plt.figure(figsize=(10, 5))
    sns.histplot(df['text_length'], bins=50, kde=True, color='teal')
    plt.title('Distribution of Word Counts in Transcriptions')
    plt.xlabel('Word Count')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(eda_dir / 'word_count_distribution.png')
    plt.close()
    
    # 3. Medical Specialty Distribution
    plt.figure(figsize=(12, 8))
    specialty_counts = df['medical_specialty'].value_counts()
    sns.barplot(x=specialty_counts.values, y=specialty_counts.index, palette='viridis')
    plt.title('Distribution of Medical Specialties')
    plt.xlabel('Number of Records')
    plt.ylabel('Specialty')
    plt.tight_layout()
    plt.savefig(eda_dir / 'specialty_distribution.png')
    plt.close()
    print("NLP EDA plots saved.")

def perform_ocr_eda(raw_dir, eda_dir):
    print("--- Starting OCR EDA ---")
    synthetic_dir = raw_dir / "medical-prescription-dataset"
    if not synthetic_dir.exists():
        print("Synthetic dataset not found.")
        return
        
    images = list(synthetic_dir.rglob("*.jpg")) + list(synthetic_dir.rglob("*.png"))
    images = [str(p) for p in images]
    print(f"Found {len(images)} images in synthetic dataset.")
    
    if not images:
        return
        
    heights, widths = [], []
    for img_path in images[:100]: # Sample 100 for speed
        img = cv2.imread(img_path)
        if img is not None:
            h, w, _ = img.shape
            heights.append(h)
            widths.append(w)
            
    print(f"Average Height: {sum(heights)/len(heights):.2f}")
    print(f"Average Width: {sum(widths)/len(widths):.2f}")
    
    # Image Size Distribution
    plt.figure(figsize=(10, 5))
    sns.scatterplot(x=widths, y=heights, alpha=0.6, color='coral')
    plt.title('Image Size Distribution (Width vs Height)')
    plt.xlabel('Width (pixels)')
    plt.ylabel('Height (pixels)')
    plt.tight_layout()
    plt.savefig(eda_dir / 'image_size_distribution.png')
    plt.close()
    
    # Sample Collage
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    axes = axes.flatten()
    for i, ax in enumerate(axes):
        if i < len(images):
            img = cv2.imread(images[i])
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            ax.imshow(img_rgb)
            ax.axis('off')
            ax.set_title(f"Sample {i+1}")
    plt.tight_layout()
    plt.savefig(eda_dir / 'sample_prescriptions.png')
    plt.close()
    print("OCR EDA plots saved.")

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "dataset" / "raw"
    eda_dir = raw_dir / "eda_plots"
    os.makedirs(eda_dir, exist_ok=True)
    
    perform_nlp_eda(raw_dir, eda_dir)
    perform_ocr_eda(raw_dir, eda_dir)

if __name__ == "__main__":
    main()
