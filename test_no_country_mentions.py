#!/usr/bin/env python3
"""
Test the analyzer without find_country_mentions() - saves to test_results.json
"""

import sys
import os

# Add parent directory to path to import url_analyzer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from url_analyzer_no_country_mentions import analyze_urls

def main():
    # New set of URLs to analyze - Dominican therapy demo URLs
    new_urls = [
        "https://www.cnbc.com/video/2024/07/12/como-crear-lmites-financieros-con-sus-hijos.html?utm_source=openai",
        "https://www.dropbox.com/es/resources/household-budget?utm_source=openai",
        "https://www.incharge.org/es/educacion-financiera/presupuesto-ahorro/consejos-de-presupuesto-familiares/?utm_source=openai",
        "https://www.univision.com/estilo-de-vida/bienestar/7-formas-de-organizarte-si-eres-un-trabajador-freelance?utm_source=openai",
        "https://www.bunq.com/es-es/blog/how-to-balance-a-9-to-5-job-with-a-side-hustle?utm_source=openai",
        "https://www.infoautonomo.es/noticias/como-mantener-un-equilibrio-entre-la-vida-laboral-y-personal-como-freelance?utm_source=openai",
        "https://www.nmdp.org/patients/transplant-support/patient-support-center/living-now/expressing-gratitude-to-your-caregiver?utm_source=openai",
        "https://www.premieriwm.com/insights/love-and-money-how-to-strengthen-your-relationship-through-financial-transparency?utm_source=openai",
        "https://www.agingcare.com/articles/gratitude-can-change-your-life-151985.htm?utm_source=openai",
        "https://www.cnb.com/private-banking/insights/share-wealth-with-family.html?utm_source=openai",
        "https://americasaves.org/resource-center/insights/protecting-your-peace-with-financial-boundaries/?utm_source=openai",
        "https://www.experian.com/blogs/ask-experian/how-to-set-financial-boundaries/?utm_source=openai",
        "https://linkedphone.com/the-freelancers-guide-to-freelancing-on-upwork-vs-fiverr/?utm_source=openai",
        "https://www.simplybusiness.com/resource/start-tutoring-business/?utm_source=openai",
        "https://www.fiverr.com/resources/guides/business/fiverr-vs-upwork?utm_source=openai",
        "https://www.fdic.gov/espanol/programa-money-smart?utm_source=openai",
        "https://www.habitat.org/financial-education/es?utm_source=openai",
        "https://centrolatinoeducacionfinanciera.org/?utm_source=openai",
    ]

    print("Testing Analyzer WITHOUT find_country_mentions()")
    print("=" * 80)
    print(f"\nAnalyzing {len(new_urls)} URLs...")
    print("Results will be saved to: test_no_country_mentions_results.json")
    print()

    # Analyze URLs and save to test file
    results = analyze_urls(new_urls, output_file='test_no_country_mentions_results.json')

    return results


if __name__ == "__main__":
    main()
