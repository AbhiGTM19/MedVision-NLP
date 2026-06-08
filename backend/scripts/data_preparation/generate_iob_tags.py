import json
import re
import argparse
from pathlib import Path

def parse_donut_string(donut_str):
    """
    Parses a Donut-style OCR string into a dictionary of entities.
    Example: "<s_ocr> doctor_name: Dr. C. Rossi clinic_name: Greenwood ... </s>"
    """
    # Remove XML-like tags
    clean_str = donut_str.replace('<s_ocr>', '').replace('</s>', '').strip()
    
    # Define the known keys to look for
    keys = [
        "doctor_name:", "clinic_name:", "clinic_address:", 
        "patient_name:", "patient_age:", "date:", "medications:", "signature:"
    ]
    
    entities = []
    
    # A simple regex approach to find where keys are in the text
    pattern = '|'.join([re.escape(k) for k in keys])
    matches = list(re.finditer(pattern, clean_str))
    
    for i, match in enumerate(matches):
        key = match.group(0).replace(':', '').strip()
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(clean_str)
        
        value = clean_str[start_idx:end_idx].strip()
        if value:
            entities.append({'entity': key, 'value': value})
            
    return entities

def tokenize_and_align(text, entities):
    """
    Given raw text and a list of entities, generates IOB tags.
    """
    tokens = text.split()
    tags = ['O'] * len(tokens)
    
    for ent in entities:
        ent_tokens = ent['value'].split()
        ent_label = ent['entity'].upper()
        
        # Find the sublist of ent_tokens in tokens
        for i in range(len(tokens) - len(ent_tokens) + 1):
            if tokens[i:i+len(ent_tokens)] == ent_tokens:
                tags[i] = f"B-{ent_label}"
                for j in range(1, len(ent_tokens)):
                    tags[i+j] = f"I-{ent_label}"
                break # Only tag the first exact match to be safe
                
    return tokens, tags

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_file = base_dir / "dataset" / "processed" / "unified_dataset_fused.jsonl"
    output_file = base_dir / "dataset" / "processed" / "unified_dataset_iob.jsonl"
    
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return
        
    print(f"Parsing Donut strings and generating IOB tags from {input_file}...")
    
    processed_count = 0
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            record = json.loads(line)
            
            # Default fallback
            record['tokens'] = []
            record['iob_tags'] = []
            
            # Only process if it's an image with the Donut-style text
            if record.get('modality') == 'image' and '<s_ocr>' in record.get('text', ''):
                donut_text = record['text']
                entities = parse_donut_string(donut_text)
                
                # To align tags, we need the "raw" OCR text without the keys. 
                # Since the Donut string *is* the text in our dataset, we will just 
                # use the raw text and tag the values. The keys themselves get 'O'.
                # A more advanced approach would use the OCR extracted text list.
                
                clean_text = donut_text.replace('<s_ocr>', '').replace('</s>', '').strip()
                tokens, tags = tokenize_and_align(clean_text, entities)
                
                record['tokens'] = tokens
                record['iob_tags'] = tags
                
            elif record.get('modality') == 'text':
                # For clinical notes, we don't have entity annotations in the dataset yet,
                # so we just generate 'O' tags for the whole text as a placeholder.
                # In a real scenario, we'd use an NLP entity extractor here.
                tokens = record.get('text', '').split()
                record['tokens'] = tokens
                record['iob_tags'] = ['O'] * len(tokens)
                
            outfile.write(json.dumps(record) + '\n')
            processed_count += 1
            
            if processed_count % 1000 == 0:
                print(f"Processed {processed_count} records...")
                
    print(f"Successfully generated IOB tags for {processed_count} records.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
