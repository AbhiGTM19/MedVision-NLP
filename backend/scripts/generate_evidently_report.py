import os
from pathlib import Path
import numpy as np
import pandas as pd
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report


def generate_report():
    print("Generating Evidently AI Monitoring Report...")
    
    SPECIALTIES = ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'Psychiatry']
    
    # Simulate reference data (e.g., training distribution)
    np.random.seed(42)
    n_ref = 1000
    ref_data = pd.DataFrame({
        'note_length': np.random.normal(loc=150, scale=50, size=n_ref).astype(int),
        'confidence_score': np.random.uniform(low=0.6, high=0.99, size=n_ref),
        'prediction': np.random.choice(SPECIALTIES, size=n_ref)
    })
    
    # Simulate current data (e.g., last 7 days of production traffic)
    n_curr = 500
    # Introduce a slight drift in note length and confidence
    curr_data = pd.DataFrame({
        'note_length': np.random.normal(loc=130, scale=40, size=n_curr).astype(int),
        'confidence_score': np.random.uniform(low=0.5, high=0.95, size=n_curr),
        'prediction': np.random.choice(SPECIALTIES, size=n_curr)
    })
    
    # Initialize Evidently Report
    report = Report(metrics=[
        DataQualityPreset(),
        DataDriftPreset(),
    ])
    
    # Run the report
    report.run(reference_data=ref_data, current_data=curr_data)
    
    # Ensure static directory exists in frontend
    BASE_DIR = Path(__file__).resolve().parent.parent
    FRONTEND_DIR = BASE_DIR.parent / "frontend"
    STATIC_DIR = FRONTEND_DIR / "static"
    
    os.makedirs(STATIC_DIR, exist_ok=True)
    report_path = STATIC_DIR / 'monitoring_report.html'
    
    # Save the HTML report
    report.save_html(str(report_path))
    print(f"Report successfully saved to {report_path}")

if __name__ == '__main__':
    generate_report()
