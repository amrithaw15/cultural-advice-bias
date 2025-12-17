#!/usr/bin/env python3
"""
URL Analyzer Script
Analyzes a list of URLs to determine their geographical origin and accessibility.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time


# Known organization domains by country
KNOWN_US_DOMAINS = {
    'apa.org',
    'psychologytoday.com',
    'nasdaq.com',
    'cnbc.com',
    'jpmorgan.com',
    'morganstanley.com',
    'mayo.edu',
    'mayoclinic.org',
    'nih.gov',
    'nimh.nih.gov',
    'ubs.com',  # UBS (US site - ubs.com/us)
    'fidelity.com',  # Fidelity - US financial services
    'smartasset.com',  # SmartAsset - US financial planning
    'kiplinger.com',  # Kiplinger - US financial publisher
    'truist.com',  # Truist Bank - US
    'synovus.com',  # Synovus Bank - US
}

KNOWN_UK_DOMAINS = {
    'guardian.co.uk',
    'theguardian.com',
    'bbc.co.uk',
    'bbc.com',
    'springer.com',  # Springer Nature, based in London, UK
    'link.springer.com',
}

KNOWN_INDIAN_DOMAINS = {
    'timesofindia.indiatimes.com',
    'hindustantimes.com',
    'economictimes.indiatimes.com',
    'livemint.com',  # Mint - HT Media
    'indianexpress.com',  # The Indian Express
    'thehindu.com',  # The Hindu
    'ndtv.com',  # NDTV
    'firstpost.com',  # Firstpost
    'thequint.com',  # The Quint
    'news18.com',  # News18
    'india.com',  # India.com
    'dnaindia.com',  # DNA India
    'business-standard.com',  # Business Standard
    'financialexpress.com',  # The Financial Express
    'moneycontrol.com',  # Moneycontrol
    'zeebiz.com',  # Zee Business
    'bharatleads.com',  # Bharat Leads (Indian site)
}

KNOWN_SWITZERLAND_DOMAINS = {
    'mdpi.com',  # MDPI publisher, based in Basel
}

KNOWN_NETHERLANDS_DOMAINS = {
    'sciencedirect.com',  # Elsevier
    'elsevier.com',
}


def check_known_domains(url):
    """Check if URL matches known organization domains."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove 'www.' prefix for matching
    domain_without_www = domain.replace('www.', '')

    # Check known US domains
    if domain in KNOWN_US_DOMAINS or domain_without_www in KNOWN_US_DOMAINS:
        return 'US', f'Known US organization: {domain}'

    # Check known UK domains
    if domain in KNOWN_UK_DOMAINS or domain_without_www in KNOWN_UK_DOMAINS:
        return 'UK', f'Known UK organization: {domain}'

    # Check known Indian domains
    if domain in KNOWN_INDIAN_DOMAINS or domain_without_www in KNOWN_INDIAN_DOMAINS:
        return 'India', f'Known Indian organization: {domain}'

    # Check known Switzerland domains
    if domain in KNOWN_SWITZERLAND_DOMAINS or domain_without_www in KNOWN_SWITZERLAND_DOMAINS:
        return 'Switzerland', f'Known Swiss publisher: {domain}'

    # Check known Netherlands domains
    if domain in KNOWN_NETHERLANDS_DOMAINS or domain_without_www in KNOWN_NETHERLANDS_DOMAINS:
        return 'Netherlands', f'Known Netherlands publisher: {domain}'

    # Check if domain contains "american"
    if 'american' in domain:
        return 'US', f'Domain contains "american": {domain}'

    # Check if domain ends with .edu (typically US)
    if domain.endswith('.edu'):
        return 'US', f'Domain ends with .edu: {domain}'

    return None, None


def extract_domain_info(url):
    """Extract domain and check for country-specific TLDs."""
    parsed = urlparse(url)
    domain = parsed.netloc

    # Country-specific TLD mappings
    country_tlds = {
        '.co.in': 'India',
        '.uk': 'UK',
        '.co.uk': 'UK',
        '.gov.uk': 'UK',
        '.ac.uk': 'UK',
        '.us': 'US',
        '.gov': 'US',  # US government
        '.mil': 'US',  # US military
        '.ca': 'Canada',
        '.au': 'Australia',
        '.de': 'Germany',
        '.fr': 'France',
    }

    for tld, country in country_tlds.items():
        if domain.endswith(tld):
            return country, f"Domain TLD: {tld}"

    # .edu often indicates US universities
    if domain.endswith('.edu'):
        return 'US', 'Domain TLD: .edu (typically US)'

    return None, None


def find_country_mentions(text):
    """Find mentions of countries in text."""
    countries = {
        'US': ['United States', 'USA', 'U.S.A', 'U.S.', 'America'],
        'UK': ['United Kingdom', 'UK', 'U.K.', 'Britain', 'England', 'Scotland', 'Wales'],
        'India': ['India', 'Indian'],
        'Canada': ['Canada', 'Canadian'],
        'Australia': ['Australia', 'Australian'],
        'Switzerland': ['Switzerland', 'Swiss', 'Basel', 'Zurich', 'Geneva'],
        'Indonesia': ['Indonesia', 'Indonesian', 'Jakarta', 'Bima, NTB'],
        'Pakistan': ['Pakistan', 'Pakistani', 'Multan', 'Karachi', 'Lahore'],
        'Netherlands': ['Netherlands', 'Dutch', 'Amsterdam'],
        'Germany': ['Germany', 'German', 'Berlin'],
        'France': ['France', 'French', 'Paris'],
    }

    text_lower = text.lower()
    found = []

    for country, keywords in countries.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append((country, keyword))

    return found


def detect_phone_country_code(text):
    """Detect country from phone number country codes."""
    phone_patterns = {
        'US/Canada': [
            r'\+1[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',  # +1-XXX-XXX-XXXX or +1 (XXX) XXX-XXXX
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',  # (XXX) XXX-XXXX
            r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',  # XXX-XXX-XXXX
            r'\(\+1\)',
            r'Tel:\s*\+1',
        ],
        'UK': [r'\+44[\s\-]?\d', r'\(\+44\)', r'Tel:\s*\+44'],
        'India': [r'\+91[\s\-]?\d', r'\(\+91\)', r'Tel:\s*\+91'],
        'Indonesia': [r'\+62[\s\-]?\d', r'\(\+62\)', r'Tel:\s*\+62'],
        'Pakistan': [r'\+92[\s\-]?\d', r'\(\+92\)', r'Tel:\s*\+92'],
        'Switzerland': [r'\+41[\s\-]?\d', r'\(\+41\)', r'Tel:\s*\+41'],
        'Netherlands': [r'\+31[\s\-]?\d', r'\(\+31\)', r'Tel:\s*\+31'],
    }

    found = []
    for country, patterns in phone_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                found.append((country, f"Phone pattern detected"))
                break

    return found


def extract_addresses_from_text(page_text):
    """Extract full addresses - must have zip/postal code AND city/state/country (location alone is not enough)."""
    addresses = []
    address_with_countries = []  # Track which country is in each address

    # Split text into lines to analyze context
    lines = page_text.split('\n')

    for i, line in enumerate(lines):
        line_clean = ' '.join(line.split())  # Clean whitespace

        # Skip very short lines, but also skip very long lines (likely article text)
        if len(line_clean) < 20 or len(line_clean) > 150:
            continue

        # Check current line + 1-2 adjacent lines for address components
        # This handles multi-line addresses like:
        # "Bahnbogen 21, 81671 Munich"
        # "Germany"
        prev_line = ' '.join(lines[i-1].split()) if i > 0 else ''
        next_line = ' '.join(lines[i+1].split()) if i < len(lines) - 1 else ''
        next_line2 = ' '.join(lines[i+2].split()) if i < len(lines) - 2 else ''

        # Combine current line with adjacent lines (but keep each under 150 chars to avoid article text)
        context_parts = []
        if len(prev_line) < 150:
            context_parts.append(prev_line)
        context_parts.append(line_clean)
        if len(next_line) < 150:
            context_parts.append(next_line)
        if len(next_line2) < 150:
            context_parts.append(next_line2)

        context = ' '.join(context_parts)

        # Look for specific location markers (zip codes, postal codes)
        zip_patterns = {
            'US': r'\b\d{5}(?:-\d{4})?\b',  # US zip code
            'UK': r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b',  # UK postcode
            'India': r'\b\d{6}\b',  # India PIN (6 digits) - only as supporting evidence
            'Germany': r'\b\d{5}\b',  # German postal code (5 digits)
        }

        has_zip = False
        zip_country = None

        # First, detect which location indicators are present in the context
        location_present = {}
        location_indicators_for_zip = {
            'India': [r'\b(?:Mumbai|Delhi|Bangalore|Kolkata|Chennai|Hyderabad|Pune|Ahmedabad)\b', r'\bIndia\b'],
            'Germany': [r'\b(?:Munich|Berlin|Hamburg|Frankfurt|Cologne|Stuttgart|Düsseldorf|Dusseldorf)\b', r'\bGermany\b'],
            'US': [
                r'\b(?:CA|NY|TX|FL|MA|IL|PA|OH|MI|GA|NC|NJ|VA|WA|AZ|CO|OR)\b',
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon)\b',
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b'
            ],
            'UK': [r'\b(?:London|Manchester|Birmingham|Edinburgh|Glasgow|Liverpool|Leeds)\b', r'\b(?:United Kingdom|UK|U\.K\.)\b'],
            'Pakistan': [r'\b(?:Lahore|Karachi|Islamabad|Rawalpindi|Multan|Faisalabad)\b', r'\bPakistan\b'],
            'Indonesia': [r'\b(?:Jakarta|Surabaya|Bandung|Medan|Bima)\b', r'\bIndonesia\b'],
        }

        for country, patterns in location_indicators_for_zip.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    location_present[country] = True
                    break

        # Now match zip codes with the country whose location indicator is present
        for country, pattern in zip_patterns.items():
            if re.search(pattern, context):
                # UK has unique format, always trust it
                if country == 'UK':
                    has_zip = True
                    zip_country = country
                    break
                # For India, Germany, US (all use digits), check which country's location is present
                elif country == 'India' and location_present.get('India'):
                    has_zip = True
                    zip_country = country
                    break
                elif country == 'Germany' and location_present.get('Germany'):
                    has_zip = True
                    zip_country = country
                    break
                elif country == 'US' and location_present.get('US'):
                    has_zip = True
                    zip_country = country
                    break
                # If US zip pattern matches but no specific location found, assume US as fallback
                elif country == 'US' and not location_present:
                    has_zip = True
                    zip_country = country
                    break

        # Look for city/state/country names (but need more than just this)
        location_indicators = {
            'US': [
                r'\b(?:CA|NY|TX|FL|MA|IL|PA|OH|MI|GA|NC|NJ|VA|WA|AZ|CO|OR)\b',  # State codes
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon)\b',  # State names
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b',  # Country names
            ],
            'UK': [
                r'\b(?:London|Manchester|Birmingham|Edinburgh|Glasgow|Liverpool|Leeds)\b',
                r'\b(?:United Kingdom|UK|U\.K\.)\b',
            ],
            'India': [
                r'\b(?:Mumbai|Delhi|Bangalore|Kolkata|Chennai|Hyderabad|Pune|Ahmedabad)\b',
                r'\bIndia\b',
            ],
            'Pakistan': [
                r'\b(?:Lahore|Karachi|Islamabad|Rawalpindi|Multan|Faisalabad)\b',
                r'\bPakistan\b',
            ],
            'Indonesia': [
                r'\b(?:Jakarta|Surabaya|Bandung|Medan|Bima)\b',
                r'\bIndonesia\b',
            ],
            'Germany': [
                r'\b(?:Munich|Berlin|Hamburg|Frankfurt|Cologne|Stuttgart|Düsseldorf|Dusseldorf)\b',
                r'\bGermany\b',
            ],
        }

        has_location = False
        location_country_name = None
        for country, patterns in location_indicators.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    has_location = True
                    location_country_name = country
                    break
            if has_location:
                break

        # Simplified address validation:
        # An address is valid ONLY if: zip/postal code AND city/state/country
        # This is simple and reliable
        is_valid_address = False
        location_country = None

        if has_zip and has_location:
            # Zip + location = valid address
            is_valid_address = True
            location_country = zip_country or location_country_name

        if is_valid_address:
            addresses.append(line_clean[:100])
            if location_country:
                address_with_countries.append((line_clean[:100], location_country))

    return addresses, address_with_countries


def analyze_page_content(soup, url):
    """Analyze page content for geographical indicators."""
    evidence = []
    country_scores = {}
    is_academic_publisher = False
    is_bank = False
    all_addresses = []
    all_phone_numbers = []
    all_location_mentions = []

    # Check if this is an academic publisher (international content)
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')
    academic_publishers = ['mdpi.com', 'springer.com', 'sciencedirect.com', 'elsevier.com',
                          'frontiersin.org', 'arxiv.org', 'nature.com', 'science.org']
    if any(pub in domain for pub in academic_publishers):
        is_academic_publisher = True

    # Check if this is a .bank domain - these are definitively US
    if '.bank' in domain:
        evidence.append("Domain is .bank TLD (US-based)")
        return 'US', evidence  # Return immediately - .bank domains are always US

    # 1. Collect information from main page (footer, copyright, entire page)
    page_text = soup.get_text()

    # Look for physical addresses anywhere on page
    addresses_found, addresses_with_country = extract_addresses_from_text(page_text)
    if addresses_found:
        for addr in addresses_found[:3]:  # Top 3 addresses
            all_addresses.append(('main_page', addr))
            evidence.append(f"Physical address found: {addr[:50]}...")
    # Track addresses that have explicit country indicators
    for addr, country in addresses_with_country[:3]:
        all_location_mentions.append(('address', country, f'in address: {addr[:30]}'))

    # Removed: find_country_mentions() - too much noise from article content

    # Look for phone numbers anywhere on page
    phone_numbers = detect_phone_country_code(page_text)
    if phone_numbers:
        for country, _ in phone_numbers:
            all_phone_numbers.append(('main_page', country))
            evidence.append(f"Phone number found: {country}")

    # 2. Check meta tags - for detecting international content
    # Removed: find_country_mentions() on meta tags - rely on address detection instead
    meta_countries = []

    # 3. Fetch About/Contact/Terms pages and collect information
    info_links = soup.find_all('a', href=re.compile(r'about|contact|terms|privacy|legal', re.I))
    fetched_pages = 0
    for link in info_links[:6]:  # Check first 6 links
        if fetched_pages >= 3:  # Limit to 3 additional page fetches
            break

        href = link.get('href')
        href_lower = href.lower() if href else ''
        if href and any(keyword in href_lower for keyword in ['about', 'contact', 'terms', 'privacy', 'legal']):
            full_url = urljoin(url, href)
            evidence.append(f"Checking {href[:30]}...")

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                info_response = requests.get(full_url, headers=headers, timeout=5, allow_redirects=True)
                if info_response.status_code == 200:
                    info_soup = BeautifulSoup(info_response.content, 'html.parser')
                    info_text = info_soup.get_text()

                    page_type = 'terms' if 'terms' in href.lower() else 'about/contact'

                    # Collect addresses from info pages
                    info_addresses, info_addr_countries = extract_addresses_from_text(info_text)
                    if info_addresses:
                        for addr in info_addresses[:2]:
                            all_addresses.append((page_type, addr))
                            evidence.append(f"{page_type} page address: {addr[:40]}...")
                    # Track addresses with country indicators
                    for addr, country in info_addr_countries[:2]:
                        all_location_mentions.append((page_type + '_address', country, f'in address: {addr[:30]}'))

                    # Collect phone numbers from info pages
                    info_phones = detect_phone_country_code(info_text)
                    if info_phones:
                        for country, _ in info_phones:
                            all_phone_numbers.append((page_type, country))
                            evidence.append(f"{page_type} page phone: {country}")

                    # Removed: find_country_mentions() on info pages - rely on address detection instead

                    fetched_pages += 1
            except:
                pass

    # 4. Now apply scoring based on collected evidence
    # Check if academic publisher has international content
    unique_meta_countries = list(set([c for source, c, kw in all_location_mentions if source == 'meta']))
    is_international_content = is_academic_publisher and len(unique_meta_countries) > 2

    if is_international_content:
        evidence.append(f"Academic publisher with multiple countries in meta (international content)")

    # PRIORITY 1: Location mentions (city/country names)
    # HIGHEST priority for addresses, then terms/about pages
    for source, country, keyword in all_location_mentions:
        if is_international_content and source == 'meta':
            # Don't use meta tags for international academic content
            continue

        # Weight based on source - ADDRESSES HAVE HIGHEST PRIORITY
        if 'address' in source:
            weight = 25  # Addresses are most reliable (city/state/zip in actual address)
        elif source == 'terms':
            weight = 20  # Terms pages are very reliable
        elif source == 'about/contact':
            weight = 15  # About/contact pages are reliable
        elif source == 'main_page':
            weight = 10  # Main page mentions are good
        else:  # meta
            weight = 2

        country_scores[country] = country_scores.get(country, 0) + weight

    # PRIORITY 3: Phone numbers (LOWER - could be call centers)
    for source, country in all_phone_numbers:
        # Phone numbers are weak evidence
        weight = 2

        if country == 'US/Canada':
            country_scores['US'] = country_scores.get('US', 0) + weight
            country_scores['Canada'] = country_scores.get('Canada', 0) + weight
        else:
            country_scores[country] = country_scores.get(country, 0) + weight

    # LAST RESORT: Try author names if no other evidence
    if not country_scores:
        author_tags = soup.find_all('meta', attrs={'name': re.compile(r'author', re.I)})
        for tag in author_tags:
            author_name = tag.get('content', '')
            if author_name:
                if any(indicator in author_name.lower() for indicator in ['kumar', 'sharma', 'singh', 'patel']):
                    evidence.append(f"Author name suggests India: {author_name}")
                    country_scores['India'] = country_scores.get('India', 0) + 0.1
                elif any(indicator in author_name.lower() for indicator in ['muhammad', 'ahmad', 'khan']):
                    evidence.append(f"Author name suggests Pakistan: {author_name}")
                    country_scores['Pakistan'] = country_scores.get('Pakistan', 0) + 0.1

    # Determine country from scores
    if country_scores:
        top_country = max(country_scores.items(), key=lambda x: x[1])
        return top_country[0], evidence

    return None, evidence


def analyze_url(url):
    """Analyze a single URL."""
    result = {
        'url': url,
        'status': 'unknown',
        'status_code': None,
        'country': 'Unknown',
        'evidence': []
    }

    try:
        # First check known organizations (highest priority)
        known_country, known_evidence = check_known_domains(url)
        if known_country:
            result['country'] = known_country
            result['evidence'].append(known_evidence)
        else:
            # Then check domain TLD
            domain_country, domain_evidence = extract_domain_info(url)
            if domain_country:
                result['country'] = domain_country
                result['evidence'].append(domain_evidence)

        # Try to fetch the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        result['status_code'] = response.status_code

        if response.status_code == 200:
            result['status'] = 'working'

            # Parse the page content
            soup = BeautifulSoup(response.content, 'html.parser')
            content_country, content_evidence = analyze_page_content(soup, url)

            if content_evidence:
                result['evidence'].extend(content_evidence)

            # Priority: known_country > domain_country > content_country
            # If we already have a known organization match, keep it (highest priority)
            if known_country:
                if content_country and content_country != known_country:
                    result['evidence'].append(f"Content analysis suggested: {content_country} (but known organization is {known_country})")
            # If content analysis found a country and we don't have domain evidence, use content analysis
            elif content_country and not domain_country:
                result['country'] = content_country
            # If both found countries and they match, keep it
            elif content_country and domain_country and content_country == domain_country:
                result['country'] = domain_country
            # If they conflict, prefer domain evidence as it's more reliable
            elif content_country and domain_country and content_country != domain_country:
                result['evidence'].append(f"Content analysis suggested: {content_country} (but domain says {domain_country})")

        elif response.status_code == 404:
            result['status'] = '404'
            result['evidence'].append('Page not found (404)')
        else:
            result['status'] = f'error_{response.status_code}'
            result['evidence'].append(f'HTTP status code: {response.status_code}')

    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['evidence'].append('Request timed out after 10 seconds')
    except requests.exceptions.ConnectionError:
        result['status'] = 'connection_error'
        result['evidence'].append('Could not connect to URL')
    except Exception as e:
        result['status'] = 'error'
        result['evidence'].append(f'Error: {str(e)}')

    return result


def analyze_urls(urls, output_file='url_analysis_results.json'):
    """Analyze a list of URLs and save results to JSON."""
    print(f"Analyzing {len(urls)} URLs...")
    print("=" * 80)

    results = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Analyzing: {url}")
        result = analyze_url(url)
        results.append(result)

        print(f"  Status: {result['status']}")
        print(f"  Country: {result['country']}")
        if result['evidence']:
            # Handle Unicode characters in evidence
            try:
                print(f"  Evidence: {result['evidence'][0]}")
            except UnicodeEncodeError:
                print(f"  Evidence: {result['evidence'][0].encode('ascii', 'ignore').decode('ascii')}")

        # Be respectful with rate limiting
        time.sleep(1)

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Analysis complete! Results saved to: {output_file}")

    # Print summary
    print("\nSummary:")
    print("-" * 80)
    country_counts = {}
    status_counts = {}

    for result in results:
        country = result['country']
        status = result['status']
        country_counts[country] = country_counts.get(country, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    # Define priority order for countries
    priority_countries = ['US', 'UK', 'India', 'Switzerland', 'Indonesia', 'Pakistan',
                          'Netherlands', 'Canada', 'Australia', 'Germany', 'France']

    print("\nBy Country:")
    # First show priority countries that were found
    for country in priority_countries:
        if country in country_counts:
            count = country_counts[country]
            percentage = (count / len(results)) * 100
            print(f"  {country}: {count} ({percentage:.1f}%)")

    # Then show any other countries found (not in priority list)
    for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
        if country not in priority_countries:
            percentage = (count / len(results)) * 100
            print(f"  {country}: {count} ({percentage:.1f}%)")

    print("\nBy Status:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")

    return results


def main():
    """Main function - example usage."""
    # Actual URLs from therapy bias demo
    therapy_urls = [
        "https://www.udel.edu/academics/colleges/canr/cooperative-extension/fact-sheets/communicating-about-money/?utm_source=openai",
        "https://www.morganstanley.com/articles/family-finances?utm_source=openai",
        "https://flatwater.bank/investments/insights/discussing-financial-matters?utm_source=openai",
        "https://ejournal.tsb.ac.id/index.php/jpi/article/view/2124?utm_source=openai",
        "https://journal.seisense.com/jom/article/view/116?utm_source=openai",
        "https://www.mdpi.com/2071-1050/14/14/8780?utm_source=openai",
        "https://www.cnb.com/private-banking/insights/share-wealth-with-family.html?utm_source=openai",
        "https://americasaves.org/resource-center/insights/protecting-your-peace-with-financial-boundaries/?utm_source=openai",
        "https://www.thepennyhoarder.com/budgeting/set-financial-boundaries/?utm_source=openai",
        "https://www.vaia.com/en-us/explanations/psychology/cognitive-psychology/personal-values/?utm_source=openai",
        "https://files.eric.ed.gov/fulltext/EJ1162037.pdf?utm_source=openai",
        "https://business.columbia.edu/cgi-strategy/chazen-global-insights/leverage-your-values-better-decision-making?utm_source=openai",
        "https://www.mdpi.com/2077-1444/14/8/981?utm_source=openai",
        "https://link.springer.com/article/10.1007/s10490-017-9509-0?utm_source=openai",
        "https://www.mdpi.com/2076-0760/14/6/371?utm_source=openai",
        "https://www.psychologytoday.com/us/blog/singletons/202411/the-power-of-family-traditions-count-the-ways?utm_source=openai",
        "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1523315/full?utm_source=openai",
        "https://www.nasdaq.com/articles/financial-planning-families-6-tips-balancing-budgets-and-goals?utm_source=openai",
        "https://arxiv.org/abs/2208.09558?utm_source=openai",
        "https://journals.kmanpub.com/index.php/jprfc/article/view/2603?utm_source=openai",
        "https://www.sciencedirect.com/science/article/abs/pii/S0167487020300283?utm_source=openai",
        "https://www.kendallcottonbronk.com/s/family-purpose-an-empirical-investigation-of-collective-purpose.pdf?utm_source=openai",
        "https://www.psychologytoday.com/us/blog/the-human-spark/201309/the-familys-contribution?utm_source=openai",
        "https://bharatleads.com/joint-families-were-a-tradition/?utm_source=openai",
        "https://www.amu.apus.edu/area-of-study/education/resources/family-communication-strategies/?utm_source=openai",
        "https://www.edu.com/blog/building-strong-parent-communication-5-essential-strategies-to-start-the-school-year-right?utm_source=openai",
        "https://www.merceradvisors.com/insights/family-finance/nurturing-financial-independence-in-adult-children-of-wealthy-families/?utm_source=openai",
        "https://www.cuofco.org/resources/how-help-your-adult-child-achieve-financial-independence?utm_source=openai",
        "https://www.jpmorgan.com/insights/wealth-planning/family-wealth-planning/how-parents-can-create-financially-independent-adults?utm_source=openai",
        "https://res.org.uk/mediabriefing/pooling-resources-in-family-networks-new-evidence-from-mexico-of-the-positive-impact-on-investment-in-children-s-education/?utm_source=openai",
    ]

    print("URL Analyzer - Therapy Bias Demo URLs")
    print("=" * 80)
    print(f"\nAnalyzing {len(therapy_urls)} URLs from therapy bias demo...")
    print()

    # Analyze URLs and save to specific file
    results = analyze_urls(therapy_urls, output_file='therapy_urls_analysis.json')

    return results


if __name__ == "__main__":
    main()
