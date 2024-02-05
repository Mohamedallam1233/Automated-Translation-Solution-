import json
import Levenshtein
with open('cities.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
def get_city_name_en(city_name_ar):
    for entry in data[0]['data']:
        if entry['city_name_ar'] == city_name_ar:
            return entry['city_name_en']
    return None

def most_similar_word(target_word, word_list):
    similarity_scores = {word: Levenshtein.distance(target_word, word) for word in word_list}
    most_similar = min(similarity_scores, key=similarity_scores.get)
    return most_similar
def cites_in_ar():
    return [entry['city_name_ar'] for entry in data[0]['data']]

def get_match_score_for_cites(city_name_ar):
    most_similar = most_similar_word(city_name_ar, cites_in_ar())
    return get_city_name_en(most_similar)

