#!/usr/bin/env python3
import json

# Load files
with open('nigerian_therapy_bias_results2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('new_urls_analysis.json', 'r', encoding='utf-8') as f:
    new_urls = json.load(f)

# URLs to remove
old_urls = [
    'https://timesofindia.indiatimes.com/life-style/relationships/web-stories/8-unsaid-responsibilities-of-the-eldest-child/photostory/111729305.cms?utm_source=openai',
    'https://www.iiardjournals.org/get/IJRCP/VOL.%209%20NO.%202%202024/THE%20LACK%20OF%20WINE%2077-90.pdf?utm_source=openai',
    'https://nesgroup.org/events/selfcare-and-financial-health--creating-a-sustainable-balance?utm_source=openai',
]

print("Before:", len(data['url_analysis']))

# Remove old URLs
data['url_analysis'] = [e for e in data['url_analysis'] if e['url'] not in old_urls]
print("After removing old:", len(data['url_analysis']))

# Add new URLs
data['url_analysis'].extend(new_urls)
print("After adding new:", len(data['url_analysis']))

# Sort by turn
data['url_analysis'].sort(key=lambda x: x['turn_number'])

# Fix urls_by_turn
for turn in data['url_collection_summary']['urls_by_turn']:
    data['url_collection_summary']['urls_by_turn'][turn] = [
        u for u in data['url_collection_summary']['urls_by_turn'][turn] if u not in old_urls
    ]

# Add new URLs to urls_by_turn
for new_url in new_urls:
    turn = str(new_url['turn_number'])
    if new_url['url'] not in data['url_collection_summary']['urls_by_turn'][turn]:
        data['url_collection_summary']['urls_by_turn'][turn].append(new_url['url'])

# Update count
data['url_collection_summary']['total_unique_urls'] = len(data['url_analysis'])

# Save
with open('nigerian_therapy_bias_results2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved! Final count:", len(data['url_analysis']))
