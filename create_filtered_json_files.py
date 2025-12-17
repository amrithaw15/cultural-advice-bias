#!/usr/bin/env python3
"""
Create filtered versions of the JSON files by removing specific URLs
"""
import json

# URLs to remove from each file
urls_to_remove = {
    'indian_therapy_bias_results.json': [
        'https://manish-kumar.medium.com/balancing-family-responsibilities-and-financial-independence-an-indian-perspective-ec5a66619001?utm_source=openai',
        'https://plutuseducation.com/blog/advantages-and-disadvantages-of-joint-family/?utm_source=openai',
        'https://www.kenwoodmgt.com/industry-articles/the-legacy-conversation-how-to-talk-to-your-family-about-financial-planning?utm_source=openai',
        'https://www.letsmakeaplan.org/financial-topics/articles/financial-planning/navigate-financial-conversations-with-family-without-tension?utm_source=openai',
        'https://medwinpublisher.org/index.php/PPRIJ/article/view/8636?utm_source=openai',
        'https://parentpowered.com/blog/family-engagement/strategies-for-equitable-family-engagement/',
        'https://www.pathsoflearning.net/13647/7-ideas-for-engaging-family-conversations-about-education-values/',
    ],
    'filipino_therapy_bias_results.json': [
        'https://brideandbreakfast.ph/2021/09/29/avoiding-issues-with-in-laws/?utm_source=openai',
        'https://www.letsmakeaplan.org/financial-topics/articles/family-finances/four-financial-considerations-when-preparing-for-a-baby?utm_source=openai',
        'https://www.surrogatealternatives.com/preparing-for-parenthood-essential-tips-for-intended-parents-to-build-a-strong-future/?utm_source=openai',
        'https://www.letsmakeaplan.org/financial-topics/articles/planning-for-couples/planning-for-the-arrival-of-a-child?utm_source=openai',
        'https://weddedwonders.com/articles/engagement/managing-family-expectations-and-setting-boundaries-during-wedding-planning/',
        'https://www.theylivehappilyeverafter.com/blog/parents-involved-in-wedding-planning-traditions?utm_source=openai',
        'https://www.yourweddinglists.com/how-to-handle-family-expectations-during-wedding-planning/?utm_source=openai',
    ],
    'nigerian_therapy_bias_results.json': [
        'https://rexclarkeadventures.com/nigerian-owambe-tourist/?utm_source=openai',
        'https://moneymatters.ng/how-to-save-for-holidays-in-nigeria/?utm_source=openai',
    ],
}

for input_file, urls_list in urls_to_remove.items():
    print(f"\nProcessing: {input_file}")
    print("=" * 80)

    # Read the original file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_count = len(data['url_analysis'])
    print(f"Original URL count: {original_count}")
    print(f"URLs to remove: {len(urls_list)}")

    # Remove URLs from url_analysis
    data['url_analysis'] = [
        entry for entry in data['url_analysis']
        if entry['url'] not in urls_list
    ]

    # Remove URLs from urls_by_turn
    for turn, turn_urls in data['url_collection_summary']['urls_by_turn'].items():
        data['url_collection_summary']['urls_by_turn'][turn] = [
            url for url in turn_urls
            if url not in urls_list
        ]

    # Update total_unique_urls
    new_count = len(data['url_analysis'])
    data['url_collection_summary']['total_unique_urls'] = new_count

    print(f"New URL count: {new_count}")
    print(f"Removed: {original_count - new_count} URLs")

    # Create output filename
    output_file = input_file.replace('.json', '2.json')

    # Save the filtered data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output_file}")

    # Verify the removal
    removed_urls = []
    for url in urls_list:
        found = any(entry['url'] == url for entry in data['url_analysis'])
        if not found:
            removed_urls.append(url)

    print(f"Verified removal of {len(removed_urls)} URLs")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("Created 3 new files:")
print("  - indian_therapy_bias_results2.json (43 -> 36 URLs)")
print("  - filipino_therapy_bias_results2.json (41 -> 34 URLs)")
print("  - nigerian_therapy_bias_results2.json (34 -> 32 URLs)")
