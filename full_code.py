from concurrent.futures import ThreadPoolExecutor, as_completed
from googletrans import Translator
import pandas as pd
import json
import Levenshtein
import time

def load_city_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_city_name_en(city_name_ar, city_data):
    for entry in city_data[0]['data']:
        if entry['city_name_ar'] == city_name_ar:
            return entry['city_name_en']
    return None

def most_similar_word(target_word, word_list):
    similarity_scores = {word: Levenshtein.distance(target_word, word) for word in word_list}
    most_similar = min(similarity_scores, key=similarity_scores.get)
    return most_similar

def get_match_score_for_cities(city_name_ar, city_data):
    most_similar = most_similar_word(city_name_ar, cities_in_ar(city_data))
    return get_city_name_en(most_similar, city_data)

def cities_in_ar(city_data):
    return [entry['city_name_ar'] for entry in city_data[0]['data']]

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
            time.sleep(1)  # Adding a delay before retrying translation
    return response0

def translate_column(column, city_data):
    if column.name.lower() == 'city':
        return column.apply(lambda x: get_match_score_for_cities(x, city_data))
    else:
        with ThreadPoolExecutor() as executor:
            translated_values = list(executor.map(trans, column))
            time.sleep(1)  # Adding a delay between translations
        return translated_values

def translate_dataframe(df, num_threads=10, city_data=None):
    print("Translating DataFrame...")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(translate_column, df[col], city_data): col for col in df.columns}

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

def process_dataframes(dfs_list, num_threads=10, city_data=None):
    for idx, dff in enumerate(dfs_list, 1):
        print(f"Processing DataFrame {idx}/{len(dfs_list)}...")
        translate_dataframe(dff, num_threads=num_threads, city_data=city_data)
        time.sleep(1)  # Adding a delay between processing DataFrames

def run_proj(excel_file_path, city_json_file, output_file):
    df = pd.read_excel(excel_file_path)

    # Load city data
    city_data = load_city_data(city_json_file)

    # Split data into frames
    num_splits = 100
    split_size = len(df) // num_splits
    dfs_list = [df.iloc[i:i + split_size] for i in range(0, len(df), split_size)]

    # Process and translate dataframes
    process_dataframes(dfs_list, city_data=city_data)

    # Save the concatenated DataFrame to a new Excel file
    result_df = pd.concat(dfs_list, ignore_index=True)
    result_df.to_excel(f'{output_file}.xlsx', index=False)

    print("All DataFrames processed. Translation complete.")

def main():
    excel_file_path = input("enter path of the file : ")
    run_proj(excel_file_path, 'cities.json', 'result')

if __name__ == "__main__":
    main()