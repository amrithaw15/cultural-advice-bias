#!/usr/bin/env python3
"""
Test address detection for nesgroup.org
"""
import requests
from bs4 import BeautifulSoup

url = "https://nesgroup.org/events/selfcare-and-financial-health--creating-a-sustainable-balance?utm_source=openai"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    # Check footer
    footer = soup.find('footer')
    if footer:
        footer_text = footer.get_text()
        print("\nFOOTER TEXT:")
        print("=" * 80)
        print(footer_text[:1000])

        # Check for address
        if 'Abuja' in footer_text or 'Nigeria' in footer_text:
            print("\n✓ Found Nigerian location in footer!")
        else:
            print("\n✗ Nigerian location NOT found in footer")

        # Look for the specific address
        lines = footer_text.split('\n')
        for i, line in enumerate(lines):
            if 'Unity Bank' in line or 'Herbert Macaulay' in line or 'Abuja' in line:
                print(f"\nLine {i}: {line.strip()}")
