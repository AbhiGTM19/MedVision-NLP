import os
import glob
import pandas as pd
from pathlib import Path

def analyze_datasets():
    print("=== PHASE 1: COMPREHENSIVE DATA STUDY ===")
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "dataset" / "raw"
    
    print("\n--- 1. Image vs Text Breakdown ---")
    
    # 1. Handwritten Medical Prescriptions Collection
    hw_collection = raw_dir / "Handwritten_Medical_Prescriptions_Collection"
    hw_col_images = list(hw_collection.glob("*.jpg")) + list(hw_collection.glob("*.png"))
    print(f"Handwritten_Medical_Prescriptions_Collection: {len(hw_col_images)} images found. [EXCLUDED FROM TRAINING — no labels, used for inference testing only]")
    
    # 2. Medical Prescription Handwritten Words
    hw_words = raw_dir / "Medical_Prescription_Handwritten_Words"
    hw_words_images = list(hw_words.rglob("*.jpg")) + list(hw_words.rglob("*.png"))
    print(f"Medical_Prescription_Handwritten_Words: {len(hw_words_images)} images found.")
    
    # 3. Medical Records Parsing Validation Set (Parquets)
    val_set = raw_dir / "medical_records_parsing_validation_set"
    parquets = list(val_set.glob("*.parquet"))
    print(f"Medical_Records_Parsing_Validation_Set: {len(parquets)} parquet files found.")
    
    print("\n--- 2. Parquet Schema Analysis ---")
    if parquets:
        sample_pq = pd.read_parquet(parquets[0])
        print(f"Schema for {parquets[0].name}:")
        for col in sample_pq.columns:
            null_count = sample_pq[col].isnull().sum()
            print(f"  - {col}: type={sample_pq[col].dtype}, nulls={null_count}/{len(sample_pq)}")
        
        # Check rubrics sample
        if 'rubrics' in sample_pq.columns:
            print(f"  Sample rubric: {sample_pq['rubrics'].iloc[0]}")
            
    print("\n--- 3. MIMIC-IV Schema & Mapping ---")
    mimic_dir = raw_dir / "mimic-iv-clinical-database-demo-2.2" / "hosp"
    if mimic_dir.exists():
        patients_csv = mimic_dir / "patients.csv"
        diagnoses_csv = mimic_dir / "diagnoses_icd.csv"
        prescriptions_csv = mimic_dir / "prescriptions.csv"
        
        if patients_csv.exists():
            df_pat = pd.read_csv(patients_csv)
            print(f"patients.csv: {len(df_pat)} records. Key: 'subject_id'. Missing values:")
            print(df_pat.isnull().sum().to_string())
            
        if prescriptions_csv.exists():
            df_presc = pd.read_csv(prescriptions_csv)
            print(f"\nprescriptions.csv: {len(df_presc)} records. Keys: 'subject_id', 'hadm_id'. Missing values in key fields:")
            print(df_presc[['subject_id', 'hadm_id', 'drug']].isnull().sum().to_string())
            print(f"Sample drug: {df_presc['drug'].dropna().iloc[0]}")
            
    print("\n--- 4. MTSamples Missingness ---")
    mtsamples_csv = raw_dir / "mtsamples.csv"
    if mtsamples_csv.exists():
        df_mt = pd.read_csv(mtsamples_csv)
        print(f"mtsamples.csv: {len(df_mt)} records. Missingness:")
        print(df_mt.isnull().sum().to_string())
        
        # Duplicates
        dup_count = df_mt.duplicated(subset=['transcription']).sum()
        print(f"\nDuplicate transcriptions in mtsamples: {dup_count}")

if __name__ == "__main__":
    analyze_datasets()
