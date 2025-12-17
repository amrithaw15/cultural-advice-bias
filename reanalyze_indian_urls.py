#!/usr/bin/env python3
"""
Re-analyze Indian URLs after keyword changes
"""
import json
from Indian_url_analyzer import analyze_url

# Read the current results file
with open('indian_therapy_bias_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track changes
changes = []
categories_before = {'addresses_user_dilemma': 0, 'defines_practice': 0, 'generic_advice': 0, 'not_related': 0, 'unknown': 0}
categories_after = {'addresses_user_dilemma': 0, 'defines_practice': 0, 'generic_advice': 0, 'not_related': 0, 'unknown': 0}

print("Re-analyzing Indian URLs after removing financial keywords from career list...")
print("=" * 80)

# Re-analyze only working URLs
for i, result in enumerate(data['url_analysis']):
    url = result['url']
    old_category = result['cultural_context']
    categories_before[old_category] = categories_before.get(old_category, 0) + 1

    # Only re-analyze if the URL was working before
    if result['status'] == 'working':
        print(f"\n[{i+1}/{len(data['url_analysis'])}] Re-analyzing: {url}")

        # Re-analyze the URL
        new_result = analyze_url(url)

        new_category = new_result['cultural_context']
        categories_after[new_category] = categories_after.get(new_category, 0) + 1

        # Check if category changed
        if new_category != old_category:
            changes.append({
                'url': url,
                'old_category': old_category,
                'new_category': new_category,
                'old_concepts': result['unique_concept_count'],
                'new_concepts': new_result['unique_concept_count']
            })
            print(f"  *** CHANGED: {old_category} -> {new_category}")
        else:
            print(f"  No change: {new_category}")

        # Update the result in the data
        data['url_analysis'][i] = new_result
        data['url_analysis'][i]['turn_number'] = result['turn_number']  # Preserve turn number
    else:
        # Keep the old result for non-working URLs
        categories_after[old_category] = categories_after.get(old_category, 0) + 1
        print(f"\n[{i+1}/{len(data['url_analysis'])}] Skipping (status: {result['status']}): {url}")

# Save the updated results
with open('indian_therapy_bias_results.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 80)
print("SUMMARY OF CHANGES")
print("=" * 80)

print("\nCategories BEFORE:")
for cat, count in categories_before.items():
    print(f"  {cat}: {count}")

print("\nCategories AFTER:")
for cat, count in categories_after.items():
    print(f"  {cat}: {count}")

if changes:
    print(f"\n{len(changes)} URLs changed category:")
    for change in changes:
        print(f"\n  {change['url'][:80]}...")
        print(f"    {change['old_category']} (concepts: {change['old_concepts']}) -> {change['new_category']} (concepts: {change['new_concepts']})")
else:
    print("\nNo URLs changed category")

print("\n" + "=" * 80)
print("Updated results saved to: indian_therapy_bias_results.json")
