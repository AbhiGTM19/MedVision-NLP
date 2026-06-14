import pandas as pd
import json
import numpy as np
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Configure Production Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s' # Keep it clean for stdout reporting
)
logger = logging.getLogger('DatasetEvaluator')

class DatasetEvaluator:
    """Rigorous Production Dataset Integrity Evaluator"""
    
    def __init__(self, base_dir: Path):
        self.MAX_BERT_CHARS = 3000
        self.MAX_TROCR_CHARS = 500
        self.base_dir = base_dir
        
    def check_missingness(self, df: pd.DataFrame) -> bool:
        logger.info("\n[✓] Missingness Audit:")
        missing = df.replace("", np.nan).isnull().sum()
        total = len(df)
        passed = True
        
        for col, count in missing.items():
            perc = (count / total) * 100
            status = "PASS" if count == 0 else f"FAIL ({perc:.2f}% missing)"
            logger.info(f"  - {col}: {count} missing [{status}]")
            if count > 0: passed = False
            
        return passed

    def check_outliers(self, df: pd.DataFrame, model_type: str) -> bool:
        logger.info(f"\n[✓] Text Outliers & Token Length Audit ({model_type}):")
        df['text_len'] = df['text'].astype(str).apply(len)
        
        max_limit = self.MAX_BERT_CHARS if model_type == 'bert' else self.MAX_TROCR_CHARS
        
        violations = df[df['text_len'] > max_limit]
        empty = df[df['text_len'] == 0]
        
        logger.info(f"  - Mean length: {df['text_len'].mean():.1f} chars")
        logger.info(f"  - 99th percentile: {df['text_len'].quantile(0.99):.1f} chars")
        logger.info(f"  - Max length: {df['text_len'].max():.1f} chars")
        
        status = "PASS" if len(violations) == 0 else f"FAIL ({len(violations)} records exceed max limit)"
        logger.info(f"  - Max limit violations: {status}")
        
        empty_status = "PASS" if len(empty) == 0 else f"FAIL ({len(empty)} empty text strings)"
        logger.info(f"  - Empty text violations: {empty_status}")
        
        return len(violations) == 0 and len(empty) == 0
        
    def check_schema(self, df: pd.DataFrame, expected_cols: List[str]) -> bool:
        logger.info("\n[✓] Schema Structure Audit:")
        actual_cols = set(df.columns)
        expected_set = set(expected_cols)
        
        missing = expected_set - actual_cols
        
        if not missing:
            logger.info("  - Schema matches exact specification: PASS")
            return True
        else:
            logger.info(f"  - Missing expected columns: {missing} FAIL")
            return False

    def check_image_paths(self, df: pd.DataFrame) -> bool:
        logger.info("\n[✓] Image Path Integrity Audit (TrOCR):")
        if 'file_path' not in df.columns:
            return True
        
        # Resolve paths using explicit directory construction rather than bare relative
        # path joining, which breaks if base_dir doesn't match the expected prefix.
        processed_img_dir = self.base_dir / "dataset" / "processed" / "images"
        missing_files = 0
        for path in df['file_path'].dropna():
            full_path = processed_img_dir / Path(path).name
            if not full_path.exists():
                missing_files += 1
                if missing_files <= 5:
                    logger.warning(f"  Missing: {full_path}")
                
        status = "PASS" if missing_files == 0 else f"FAIL ({missing_files} broken paths)"
        logger.info(f"  - Image path verification: {status}")
        return missing_files == 0

    def check_class_balance(self, df: pd.DataFrame) -> bool:
        logger.info("\n[✓] Class Distribution Audit (BERT):")
        if 'label' not in df.columns:
            return True
            
        counts = df['label'].value_counts()
        logger.info(f"  - Total unique classes: {len(counts)}")
        logger.info(f"  - Top 3 classes:\n{counts.head(3).to_string()}")
        
        minority = counts[counts < 50]
        if len(minority) > 0:
            logger.warning(f"  - Warning: {len(minority)} classes have severe under-representation (< 50 samples).")
            
        return True

    def evaluate(self, filepath: Path, name: str, model_type: str) -> None:
        logger.info(f"\n{'='*60}\n RIGOROUS EVALUATION: {name}\n{'='*60}")
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return
            
        try:
            df = pd.read_json(filepath, lines=True)
        except Exception as e:
            logger.error(f"Failed to parse JSONL: {str(e)}")
            return
            
        logger.info(f"Total Valid Records Parsed: {len(df)}")
        
        expected_cols = ['id', 'source', 'modality', 'text']
        if model_type == 'bert': expected_cols.append('label')
        if model_type == 'trocr': expected_cols.append('file_path')
            
        p1 = self.check_schema(df, expected_cols)
        p2 = self.check_missingness(df)
        p3 = self.check_outliers(df, model_type)
        
        p4 = p5 = True
        if model_type == 'bert': p4 = self.check_class_balance(df)
        if model_type == 'trocr': p5 = self.check_image_paths(df)
        
        if p1 and p2 and p3 and p4 and p5:
            logger.info(f"\n>>> VERDICT: {name} PASSED ALL INTEGRITY CHECKS <<<")
        else:
            logger.error(f"\n>>> VERDICT: {name} FAILED INTEGRITY CHECKS <<<")

def main():
    parser = argparse.ArgumentParser(description="MedVision Dataset Evaluator")
    parser.add_argument("--base_dir", type=str, default=str(Path(__file__).resolve().parent.parent.parent), help="Root backend directory")
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    processed_dir = base_dir / "dataset" / "processed"
    
    evaluator = DatasetEvaluator(base_dir)
    evaluator.evaluate(processed_dir / "bio_clinicalbert_dataset.jsonl", "Bio_ClinicalBERT Dataset", "bert")
    evaluator.evaluate(processed_dir / "trocr_dataset.jsonl", "TrOCR Dataset", "trocr")

if __name__ == "__main__":
    main()
