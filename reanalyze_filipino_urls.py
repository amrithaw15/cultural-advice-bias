#!/usr/bin/env python3
"""
Re-analyze Filipino URLs after updates:
- Added filipino_grandparents concept (lola, lolo, apo)
- healthshots.com in KNOWN_INDIAN_DOMAINS
- healthline.com in KNOWN_US_DOMAINS
- Removed Babysitting from living_with_family
"""
import json
from filipino_url_analyzer import analyze_url
import time

# Read the current results file
with open('filipino_therapy_bias_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track changes
location_changes = []
category_changes = []
categories_before = {'addresses_user_dilemma': 0, 'defines_practice': 0, 'generic_advice': 0, 'not_related': 0, 'unknown': 0}
categories_after = {'addresses_user_dilemma': 0, 'defines_practice': 0, 'generic_advice': 0, 'not_related': 0, 'unknown': 0}
countries_before = {}
countries_after = {}

print("Re-analyzing Filipino URLs after updates...")
print("=" * 80)

# Re-analyze only working URLs
for i, result in enumerate(data['url_analysis']):
    url = result['url']
    old_category = result['cultural_context']
    old_country = result['country']

    categories_before[old_category] = categories_before.get(old_category, 0) + 1
    countries_before[old_country] = countries_before.get(old_country, 0) + 1

    # Only re-analyze if the URL was working before
    if result['status'] == 'working':
        print(f"\n[{i+1}/{len(data['url_analysis'])}] Re-analyzing: {url}")

        # Re-analyze the URL
        new_result = analyze_url(url)

        new_category = new_result['cultural_context']
        new_country = new_result['country']

        categories_after[new_category] = categories_after.get(new_category, 0) + 1
        countries_after[new_country] = countries_after.get(new_country, 0) + 1

        # Check if location changed
        if new_country != old_country:
            location_changes.append({
                'url': url,
                'old_country': old_country,
                'new_country': new_country,
                'evidence': new_result['evidence'][:2] if len(new_result['evidence']) > 0 else []
            })
            print(f"  *** LOCATION CHANGED: {old_country} -> {new_country}")
        else:
            print(f"  Location unchanged: {new_country}")

        # Check if category changed
        if new_category != old_category:
            category_changes.append({
                'url': url,
                'old_category': old_category,
                'new_category': new_category,
                'old_concepts': result['unique_concept_count'],
                'new_concepts': new_result['unique_concept_count']
            })
            print(f"  *** CATEGORY CHANGED: {old_category} -> {new_category}")
        else:
            print(f"  Category unchanged: {new_category}")

        # Update the result in the data
        data['url_analysis'][i] = new_result
        data['url_analysis'][i]['turn_number'] = result['turn_number']  # Preserve turn number

        time.sleep(2)  # Delay to avoid rate limiting
    else:
        # Keep the old result for non-working URLs
        categories_after[old_category] = categories_after.get(old_category, 0) + 1
        countries_after[old_country] = countries_after.get(old_country, 0) + 1
        print(f"\n[{i+1}/{len(data['url_analysis'])}] Skipping (status: {result['status']}): {url}")

# Save the updated results
with open('filipino_therapy_bias_results.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 80)
print("SUMMARY OF CHANGES")
print("=" * 80)

print("\nCategories BEFORE:")
for cat, count in sorted(categories_before.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  {cat}: {count}")

print("\nCategories AFTER:")
for cat, count in sorted(categories_after.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  {cat}: {count}")

print("\nCountries BEFORE:")
for country, count in sorted(countries_before.items(), key=lambda x: x[1], reverse=True):
    print(f"  {country}: {count}")

print("\nCountries AFTER:")
for country, count in sorted(countries_after.items(), key=lambda x: x[1], reverse=True):
    print(f"  {country}: {count}")

if location_changes:
    print(f"\n{len(location_changes)} URLs changed location:")
    for change in location_changes:
        print(f"\n  {change['url'][:80]}...")
        print(f"    {change['old_country']} -> {change['new_country']}")
        if change['evidence']:
            print(f"    Evidence: {change['evidence'][0]}")
else:
    print("\nNo URLs changed location")

if category_changes:
    print(f"\n{len(category_changes)} URLs changed category:")
    for change in category_changes:
        print(f"\n  {change['url'][:80]}...")
        print(f"    {change['old_category']} (concepts: {change['old_concepts']}) -> {change['new_category']} (concepts: {change['new_concepts']})")
else:
    print("\nNo URLs changed category")

print("\n" + "=" * 80)
print("Updated results saved to: filipino_therapy_bias_results.json")
