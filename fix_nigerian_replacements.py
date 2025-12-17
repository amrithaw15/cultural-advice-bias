#!/usr/bin/env python3
"""
Properly replace the 3 URLs in Nigerian JSON files
"""
import json

# URLs to remove
urls_to_remove = [
    'https://timesofindia.indiatimes.com/life-style/relationships/web-stories/8-unsaid-responsibilities-of-the-eldest-child/photostory/111729305.cms?utm_source=openai',
    'https://www.iiardjournals.org/get/IJRCP/VOL.%209%20NO.%202%202024/THE%20LACK%20OF%20WINE%2077-90.pdf?utm_source=openai',
    'https://nesgroup.org/events/selfcare-and-financial-health--creating-a-sustainable-balance?utm_source=openai',
]

# Load the new URLs analysis
with open('new_urls_analysis.json', 'r', encoding='utf-8') as f:
    new_urls_data = json.load(f)

print("=" * 80)
print("FIXING NIGERIAN URL REPLACEMENTS")
print("=" * 80)

# Process both files
for filename in ['nigerian_therapy_bias_results.json', 'nigerian_therapy_bias_results2.json']:
    print(f"\nProcessing: {filename}")

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"  Original count: {len(data['url_analysis'])}")

    # Remove old URLs from url_analysis
    data['url_analysis'] = [
        entry for entry in data['url_analysis']
        if entry['url'] not in urls_to_remove
    ]

    print(f"  After removal: {len(data['url_analysis'])}")

    # Add new URLs to url_analysis
    data['url_analysis'].extend(new_urls_data)

    print(f"  After adding new: {len(data['url_analysis'])}")

    # Sort by turn_number to maintain order
    data['url_analysis'].sort(key=lambda x: x['turn_number'])

    # Update urls_by_turn - already done in the JSON, just verify
    for turn, turn_urls in data['url_collection_summary']['urls_by_turn'].items():
        # Remove old URLs
        data['url_collection_summary']['urls_by_turn'][turn] = [
            url for url in turn_urls if url not in urls_to_remove
        ]

    # Add new URLs to urls_by_turn if not already there
    for new_url_entry in new_urls_data:
        turn = str(new_url_entry['turn_number'])
        if new_url_entry['url'] not in data['url_collection_summary']['urls_by_turn'][turn]:
            data['url_collection_summary']['urls_by_turn'][turn].append(new_url_entry['url'])

    # Update total count
    data['url_collection_summary']['total_unique_urls'] = len(data['url_analysis'])

    # Save
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved with {len(data['url_analysis'])} URLs")

    # Verify
    urls = [r['url'] for r in data['url_analysis']]
    print(f"  Verification:")
    print(f"    independent.ng: {'✓' if any('independent.ng' in u for u in urls) else '✗'}")
    print(f"    punchng/how-to-celebrate: {'✓' if any('how-to-celebrate-festivities' in u for u in urls) else '✗'}")
    print(f"    healthcentre.nz: {'✓' if any('healthcentre.nz' in u for u in urls) else '✗'}")
    print(f"    timesofindia (should be gone): {'✗ STILL THERE!' if any('timesofindia' in u for u in urls) else '✓'}")
    print(f"    iiardjournals (should be gone): {'✗ STILL THERE!' if any('iiardjournals' in u for u in urls) else '✓'}")
    print(f"    nesgroup (should be gone): {'✗ STILL THERE!' if any('nesgroup' in u for u in urls) else '✓'}")

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
