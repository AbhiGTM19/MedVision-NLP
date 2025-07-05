import pandas as pd
import os
import glob

# Specify the directory containing the .txt files
input_directory = "C:/Users/yugan/Desktop/VNIT Mtech/GDrive/SEM-2/MLDeployments/Final Assignment/aclImdb_v1/aclImdb/train/neg"  # Replace with your directory path
output_file = "output_train_neg.csv"  # Output CSV file name

# Get a list of all .txt files in the directory
txt_files = glob.glob(os.path.join(input_directory, "*.txt"))

# Initialize a list to store the content of each file
data = []

# Read each .txt file and append its content to the data list
for file_path in txt_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            data.append(content)
    except UnicodeDecodeError:
        # Try a different encoding if utf-8 fails
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
            data.append(content)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        data.append("")  # Append empty string for failed reads

# Create a pandas DataFrame with one column
df = pd.DataFrame(data, columns=["Content"])

# Save the DataFrame to a CSV file
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"Converted {len(data)} files to {output_file}")