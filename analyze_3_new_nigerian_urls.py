#!/usr/bin/env python3
"""
Analyze only the 3 new Nigerian URLs
"""
import json
from nigerian_url_analyzer import analyze_url
import time

# The 3 new URLs with their turn numbers
new_urls = [
    ("https://independent.ng/the-price-of-celebration-how-hosting-social-events-in-nigeria-is-becoming-a-luxury/", 1),
    ("https://punchng.com/how-to-celebrate-festivities-without-breaking-the-bank/", 1),
    ("https://healthcentre.nz/5-tips-for-maintaining-boundaries-with-family-and-friends-as-a-caregiver/?utm_source=openai", 3)
]

print("Analyzing 3 new Nigerian URLs...")
print("=" * 80)

results = []

for i, (url, turn_number) in enumerate(new_urls, 1):
    print(f"\n[{i}/3] Analyzing: {url}")
    print(f"  Turn: {turn_number}")

    result = analyze_url(url)
    result['turn_number'] = turn_number
    results.append(result)

    print(f"  Status: {result['status']}")
    print(f"  Country: {result['country']}")
    print(f"  Cultural Context: {result['cultural_context']}")
    print(f"  Unique Concepts: {result['unique_concept_count']}")
    if result['matched_keywords']:
        print(f"  Matched Keywords: {', '.join(result['matched_keywords'][:5])}")

    time.sleep(2)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for result in results:
    print(f"\nURL: {result['url']}")
    print(f"  Turn: {result['turn_number']}")
    print(f"  Country: {result['country']}")
    print(f"  Category: {result['cultural_context']}")
    print(f"  Concepts: {result['unique_concept_count']}")

# Save results to a temporary file for review
with open('new_urls_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 80)
print("Results saved to: new_urls_analysis.json")
print("\nYou can now manually add these to nigerian_therapy_bias_results.json")
