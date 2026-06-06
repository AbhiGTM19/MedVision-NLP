import os
import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.metric_preset import TargetDriftPreset

def generate_report():
    print("Generating Evidently AI Monitoring Report...")
    
    # Simulate reference data (e.g., training distribution)
    np.random.seed(42)
    n_ref = 1000
    ref_data = pd.DataFrame({
        'review_length': np.random.normal(loc=150, scale=50, size=n_ref).astype(int),
        'confidence_score': np.random.uniform(low=0.6, high=0.99, size=n_ref),
        'prediction': np.random.choice([0, 1], size=n_ref, p=[0.5, 0.5])
    })
    
    # Simulate current data (e.g., last 7 days of production traffic)
    n_curr = 500
    # Introduce a slight drift in review length and confidence
    curr_data = pd.DataFrame({
        'review_length': np.random.normal(loc=130, scale=40, size=n_curr).astype(int),
        'confidence_score': np.random.uniform(low=0.5, high=0.95, size=n_curr),
        'prediction': np.random.choice([0, 1], size=n_curr, p=[0.6, 0.4])
    })
    
    # Initialize Evidently Report
    report = Report(metrics=[
        DataQualityPreset(),
        DataDriftPreset(),
    ])
    
    # Run the report
    report.run(reference_data=ref_data, current_data=curr_data)
    
    # Ensure static directory exists
    os.makedirs('static', exist_ok=True)
    report_path = 'static/monitoring_report.html'
    
    # Save the HTML report
    report.save_html(report_path)
    print(f"Report successfully saved to {report_path}")

if __name__ == '__main__':
    generate_report()
