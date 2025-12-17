#!/usr/bin/env python3
"""
Test gcubedesignandbuild.com URL to see why it's failing
"""
import requests
from bs4 import BeautifulSoup

url = "https://gcubedesignandbuild.com/the-tradition-of-pamamanhikan-in-the-philippines-some-tips-to-prevent-plate-throwing/"

print(f"Testing: {url}")
print("=" * 80)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    print(f"Status Code: {response.status_code}")
    print(f"Final URL: {response.url}")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get full text
        full_text = soup.get_text()
        print(f"\nPage text length: {len(full_text)} characters")

        # Check for keywords
        print("\nKeyword checks:")
        print(f"  'pamamanhikan' in text: {'pamamanhikan' in full_text.lower()}")
        print(f"  'pamanhikan' in text: {'pamanhikan' in full_text.lower()}")
        print(f"  'philippines' in text: {'philippines' in full_text.lower()}")
        print(f"  'filipino' in text: {'filipino' in full_text.lower()}")

        # Check for address
        print(f"\n  'Lipa City' in text: {'Lipa City' in full_text}")
        print(f"  'Batangas' in text: {'Batangas' in full_text}")
        print(f"  'Fatima St' in text: {'Fatima St' in full_text}")

        # Check footer
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text()
            print(f"\nFooter found! Length: {len(footer_text)} characters")
            print(f"  'Lipa City' in footer: {'Lipa City' in footer_text}")
            print(f"  'Batangas' in footer: {'Batangas' in footer_text}")

            # Show first 500 chars of footer
            print(f"\nFirst 500 chars of footer:")
            print(footer_text[:500])
        else:
            print("\n✗ No footer element found")

        # Check title
        title = soup.find('title')
        if title:
            print(f"\nPage Title: {title.get_text()}")

        # Check for potential blocks
        if len(full_text) < 500:
            print("\n⚠ WARNING: Very short page text - might be blocked or JS-rendered")
            print(f"First 500 chars of full text:")
            print(full_text[:500])

except Exception as e:
    print(f"Error: {e}")
