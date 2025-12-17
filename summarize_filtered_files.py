#!/usr/bin/env python3
"""
Summarize the three new filtered JSON files
"""
import json

files = [
    'nigerian_therapy_bias_results2.json',
    'indian_therapy_bias_results2.json',
    'filipino_therapy_bias_results2.json'
]

for filename in files:
    print(f"\n{'='*80}")
    print(f"{filename.replace('_', ' ').replace('.json', '').replace('2', ' 2').upper()}")
    print(f"{'='*80}")

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_urls = len(data['url_analysis'])
    print(f"Total URLs: {total_urls}")

    # Count categories
    categories = {}
    for result in data['url_analysis']:
        cat = result['cultural_context']
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        pct = (count/total_urls)*100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    # Count countries - show ALL
    countries = {}
    for result in data['url_analysis']:
        country = result['country']
        countries[country] = countries.get(country, 0) + 1

    print("\nCountries:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        pct = (count/total_urls)*100
        print(f"  {country}: {count} ({pct:.1f}%)")

print("\n" + "="*80)
