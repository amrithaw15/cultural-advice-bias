#!/usr/bin/env python3
"""
Analyze new set of URLs - saves to new_urls_analysis.json
"""

import sys
import os

# Add parent directory to path to import url_analyzer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from url_analyzer import analyze_urls

def main():
    # New set of URLs to analyze
    new_urls = [
        "https://www.livemint.com/money/personal-finance/financial-independence-family-finances-financial-enmeshment-financial-literacy-family-budget-family-money-dynamics-11731166569582.html?utm_source=openai",
        "https://academyfamilybusiness.org/blog/managing-family-expectations-balancing-family-interests-with-business-needs?utm_source=openai",
        "https://www.shaadiabroad.com/blog/balancing-family-expectations-and-personal-choices?utm_source=openai",
        "https://www.truist.com/resources/wealth/center-for-family-legacy/strengthening-the-family-bond?utm_source=openai",
        "https://www.ubs.com/us/en/wealth-management/insights/article.1858823.html?utm_source=openai",
        "https://www.synovus.com/personal/resource-center/financial-newsletters/2022/april/strategies-for-balancing-family-and-financial-security/?utm_source=openai",
        "https://journey-wealth.com/the-generosity-gap-balancing-support-and-independence-in-families/?utm_source=openai",
        "https://www.merceradvisors.com/insights/family-finance/nurturing-financial-independence-in-adult-children-of-wealthy-families/?utm_source=openai",
        "https://preggytomommy.com/how-to-balance-familys-financial-priorities/?utm_source=openai",
        "https://medium.com/%40laurentgrindler/balancing-act-essential-tips-for-financial-planning-in-big-families-48163982c38e?utm_source=openai",
        "https://www.kiplinger.com/article/saving/t023-c032-s015-keys-to-balancing-your-personal-and-financial-life.html?utm_source=openai",
        "https://www.nasdaq.com/articles/financial-planning-families-6-tips-balancing-budgets-and-goals?utm_source=openai",
        "https://familybusiness.org/content/Family-emotions-can-drive-business-decisions?utm_source=openai",
        "https://www.sdpep.org/strengthening_families?utm_source=openai",
        "https://cfeg.com/insights_research/family-unity-what-is-it-why-its-vital-and-how-to-achieve-it/?utm_source=openai",
    ]

    print("Analyzing New URL Set")
    print("=" * 80)
    print(f"\nAnalyzing {len(new_urls)} URLs...")
    print("Results will be saved to: new_urls_analysis.json")
    print()

    # Analyze URLs and save to new file
    results = analyze_urls(new_urls, output_file='new_urls_analysis.json')

    return results


if __name__ == "__main__":
    main()
