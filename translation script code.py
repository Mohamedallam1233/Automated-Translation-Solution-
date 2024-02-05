from concurrent.futures import ThreadPoolExecutor, as_completed
from googletrans import Translator
import pandas as pd
import time

excel_file_path = 'Book.xls'
df = pd.read_excel(excel_file_path)
num_splits = 100
split_size = len(df) // num_splits
dfs_list = [df.iloc[i:i+split_size] for i in range(0, len(df), split_size)]

def trans(response0):
    if pd.isnull(response0):
        return ''
    translator = Translator()
    max_retries = 10
    for retry in range(max_retries):
        try:
            translated = translator.translate(response0, src='arabic', dest='english')
            return translated.text
        except Exception as e:
            print(f"Translation error (retry {retry + 1}/{max_retries}): {e}")
    return response0

def translate_column(column):
    with ThreadPoolExecutor() as executor:
        translated_values = list(executor.map(trans, column))
    return translated_values

def translate_dataframe(df, num_threads=10):
    print("Translating DataFrame...")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(translate_column, df[col]): col for col in df.columns}

    translated_columns = {}
    for future in as_completed(futures):
        col = futures[future]
        try:
            translated_columns[col] = future.result()
        except Exception as e:
            print(f"Error translating column '{col}': {e}")

    # Check if all translated columns have the same length
    column_lengths = [len(translated_columns[col]) for col in translated_columns]
    if len(set(column_lengths)) != 1:
        raise ValueError("Translated columns have different lengths")

    # Create a new DataFrame with columns in the original order
    df_english = pd.DataFrame({col: translated_columns[col] for col in df.columns}, columns=df.columns)
    print("Translation complete.")
    return df_english

def runsc(index):
    print(f"Processing DataFrame {index + 1}/{len(dfs_list)}...")
    dff = dfs_list[index]
    df_english = translate_dataframe(dff, num_threads=10)
    time.sleep(1)
    print(f"DataFrame {index + 1} processed.")
    return df_english

# Concatenate all translated DataFrames into one while maintaining order
result_df_list = [runsc(i) for i in range(len(dfs_list))]
result_df = pd.concat(result_df_list, ignore_index=True)

# Save the concatenated DataFrame to a new Excel file
result_df.to_excel('final_res_output.xlsx', index=False)

print("All DataFrames processed. Translation complete.")