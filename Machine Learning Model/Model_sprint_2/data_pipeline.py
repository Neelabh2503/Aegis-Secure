import os
import glob
import pandas as pd
import config
from feature_extraction import extract_features_from_dataframe

def load_and_sample_raw_data(data_dir, fraction=0.1, random_state=42):
    raw_data_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not raw_data_files:
        print(f"Error: No .csv files found in '{data_dir}'.")
        print("Please add your raw data files (e.g., phishing.csv, legit.csv) to the /data/ folder.")
        return pd.DataFrame()

    print(f"Found {len(raw_data_files)} raw data files.")
    
    all_samples = []
    for file_path in raw_data_files:
        try:
            print(f"Loading and sampling {os.path.basename(file_path)}...")
            df = pd.read_csv(file_path, on_bad_lines='skip')
            
            if 'label' not in df.columns or 'url' not in df.columns:
                print(f"Warning: Skipping {file_path}. Must contain 'label' and 'url' columns.")
                continue
            
            sample_df = df.sample(frac=fraction, random_state=random_state)
            all_samples.append(sample_df)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    if not all_samples:
        print("Error: No valid data could be loaded.")
        return pd.DataFrame()
        
    combined_df = pd.concat(all_samples, ignore_index=True)
    combined_df = combined_df.sample(frac=0.1, random_state=random_state).reset_index(drop=True)
    
    print(f"Total raw training data prepared: {len(combined_df)} samples.")
    return combined_df

def main():
    print("--- Starting Data Pipeline ---")
    
    raw_df = load_and_sample_raw_data(
        data_dir=config.DATA_DIR,
        fraction=config.TRAIN_SAMPLE_FRACTION
    )
    
    if raw_df.empty:
        print("Data pipeline failed. Exiting.")
        return

    engineered_df = extract_features_from_dataframe(raw_df)
    
    engineered_df.to_csv(config.ENGINEERED_TRAIN_FILE, index=False)
    
    print(f"\n--- Data Pipeline Complete ---")
    print(f"Engineered training set saved to: {config.ENGINEERED_TRAIN_FILE}")
    print(f"Total features: {len(config.ALL_FEATURE_COLUMNS)}")

if __name__ == "__main__":
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not glob.glob(os.path.join(config.DATA_DIR, "*.csv")):
        print("Creating dummy data files...")
        dummy_phish = pd.DataFrame({
            'label': [1, 1],
            'url': ['facebook.com.login-support.ru', 'myetherwallets.kr/wallet']
        })
        dummy_phish.to_csv(os.path.join(config.DATA_DIR, 'phishing_data_1.csv'), index=False)
        
        dummy_legit = pd.DataFrame({
            'label': [0, 0],
            'url': ['google.com', 'https://www.millect.com/Plans']
        })
        dummy_legit.to_csv(os.path.join(config.DATA_DIR, 'legit_data_1.csv'), index=False)
        print(f"Dummy files created in {config.DATA_DIR}. Please replace them with your real data.")
        
    main()
