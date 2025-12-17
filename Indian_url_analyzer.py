#!/usr/bin/env python3
"""
India Cultural Context URL Analyzer
Analyzes URLs for both geographical origin AND cultural context relevance.
Detects whether content addresses Indian cultural context (joint family, etc.)
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time


# Indian cultural context keywords organized by concept
INDIAN_CULTURAL_CONCEPTS = {
    'joint_family': [
        'joint family',
        'joint family system',
        'extended family living',
        'multigenerational household',
        'multi-generational household',
        'living with extended family',
    ],
    'salary_contribution': [
        'salary contribution',
        'give salary',
        'contribute salary',
        'family pooled income',
        'salary to family',
        'pooled income',
    ],
    'grandfather_patriarch': [
        'grandfather head',
        'family patriarch',
        'grandfather authority',
        'elder authority',
        'family matriarch',
    ],
    'wbcs': [
        'WBCS',
        'West Bengal Civil Service',
        'government job India',
    ],
    'rupees': [
        'rupee',
        'rupees',
        '₹',
        'lakhs',
        'lakh',
    ],
    'peer_influence': [
        'friends also',
        'friends do the same',
        'everyone does it',
        'social comparison',
        'friends in joint family',
        'others also contribute',
    ],
    'seeking_approval': [
        'family approval',
        'what family thinks',
        'talk with family',
        'talk with your family',
        'conversation with your family',
        'engaging with family',
        'partnering with family',
        'partnering with families',
        'family expectations',
        'family governance',
        'engaging family',
        'family opinion',
        'grandfather thinks',
        'elder blessing',
        'family perspective',
    ],
    'career': [
        'career advancement',
        'academic journey',
        'career exploration',
        'career path',
        'career decision',
        'master degree',
        'masters degree',
        'higher education',
        'promotion',
        'education cost',
        'professional development',
        'career growth',
        'further education',
    ],
    'geographic_india': [
        'Kolkata',
        'West Bengal',
    ],
}


# Western boundary/independence keywords (tracked separately, not counted in concepts)
BOUNDARIES_WESTERN = [
    'boundaries',
    'personal boundaries',
    'set boundaries',
    'personal space',
    'Open Communication',
    'Couple Time',
    'Assert',
    'Assertive',
    'Self Care',
    'Delegate',
    'Financial Planning',
    'financial goals',
    'Interference',
    'Personal Goals',
    'financial independence',
    'budget',
    'Financial Discipline',
    'Savings',
    'individual goals',
]


# Known organization domains by country
KNOWN_US_DOMAINS = {
    'apa.org',
    'psychologytoday.com',
    'indeed.com',
    'forbes.com',
    'nasdaq.com',
    'cnbc.com',
    'jpmorgan.com',
    'morganstanley.com',
    'mayo.edu',
    'mayoclinic.org',
    'gov.capital',
    'simpli.com',
    'healthline.com',
    'mayoclinichealthsystem.org',
    'clevelandclinic.org',
    'nih.gov',
    'nimh.nih.gov',
    'ubs.com',
    'fidelity.com',
    'smartasset.com',
    'kiplinger.com',
    'truist.com',
    'synovus.com',
    'arxiv.org',
    'nerdwallet.com',
    'tdecu.org',
    'fastweb.com',
    'indeed.com',
    'fatherly.com',
    'fundsforngos.org',
    'howstuffworks.com',
    'phoenix.edu',
    'thehighereducationreview.com',
    'nymag.com',
    'usbank.com',
    'seventeen.com',
    'soapoperadigest.com',
    'parents.com',
}

KNOWN_UK_DOMAINS = {
    'guardian.co.uk',
    'theguardian.com',
    'bbc.co.uk',
    'bbc.com',
    'springer.com',
    'link.springer.com',
}

KNOWN_CANADIAN_DOMAINS = {
    'cbc.ca',
    'theglobeandmail.com',
    'nationalpost.com',
    'macleans.ca',
    'thestar.com',
    'ottawacitizen.com',
    'montrealgazette.com',
    'vancouversun.com',
}

KNOWN_INDIAN_DOMAINS = {
    'kotak811.com',
    'moneycontrol.com',
    'healthshots.com',
    'moneydiary.in',
    'livemint.com',
    'blog.mstutor.in',
    'economictimes.indiatimes.com',
    'hindustantimes.com',
    'marriagehint.com',
    'parentmarriage.com',
    'weddingalliances.com',
    'royalmatrimonial.com',
    'vowsbysiddhusoma.com',
    'timesofindia.indiatimes.com',
    'indiatimes.com',
    'indianexpress.com',
    'thehindu.com',
    'ndtv.com',
    'firstpost.com',
    'thequint.com',
    'news18.com',
    'india.com',
    'dnaindia.com',
    'business-standard.com',
    'financialexpress.com',
    'zeebiz.com',
    'bharatleads.com',
    'shaadi.com',
    'calcwise.finance',
    'shaadiabroad.com',
    'bharatmatrimony.com',
    'bonobology.com',
    'indiatoday.in',
}

KNOWN_SWITZERLAND_DOMAINS = {
    'mdpi.com',
}

KNOWN_NETHERLANDS_DOMAINS = {
    'sciencedirect.com',
    'elsevier.com',
}


def check_known_domains(url):
    """Check if URL matches known organization domains (including subdomains)."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    domain_without_www = domain.replace('www.', '')

    # Helper function to check if domain matches or is a subdomain of known domains
    def matches_known_domain(domain_to_check, known_domains_set):
        if domain_to_check in known_domains_set:
            return True
        # Check if it's a subdomain
        for known_domain in known_domains_set:
            if domain_to_check.endswith('.' + known_domain):
                return True
        return False

    if matches_known_domain(domain, KNOWN_US_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_US_DOMAINS):
        return 'US', f'Known US organization: {domain}'
    if matches_known_domain(domain, KNOWN_UK_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_UK_DOMAINS):
        return 'UK', f'Known UK organization: {domain}'
    if matches_known_domain(domain, KNOWN_CANADIAN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_CANADIAN_DOMAINS):
        return 'Canada', f'Known Canadian organization: {domain}'
    if matches_known_domain(domain, KNOWN_INDIAN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_INDIAN_DOMAINS):
        return 'India', f'Known Indian organization: {domain}'
    if domain in KNOWN_SWITZERLAND_DOMAINS or domain_without_www in KNOWN_SWITZERLAND_DOMAINS:
        return 'Switzerland', f'Known Swiss publisher: {domain}'
    if domain in KNOWN_NETHERLANDS_DOMAINS or domain_without_www in KNOWN_NETHERLANDS_DOMAINS:
        return 'Netherlands', f'Known Netherlands publisher: {domain}'

    # Check for US indicators in domain name
    if 'american' in domain or 'america' in domain:
        return 'US', f'Domain contains "american/america": {domain}'

    # Check for US state names in domain
    us_states = ['alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado',
                 'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho',
                 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana',
                 'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota',
                 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada',
                 'newhampshire', 'newjersey', 'newmexico', 'newyork', 'northcarolina',
                 'northdakota', 'ohio', 'oklahoma', 'oregon', 'pennsylvania',
                 'rhodeisland', 'southcarolina', 'southdakota', 'tennessee', 'texas',
                 'utah', 'vermont', 'virginia', 'washington', 'westvirginia',
                 'wisconsin', 'wyoming']

    for state in us_states:
        if state in domain.replace('-', '').replace('.', ''):
            return 'US', f'Domain contains US state name "{state}": {domain}'

    if domain.endswith('.edu'):
        return 'US', f'Domain ends with .edu: {domain}'

    return None, None


def extract_domain_info(url):
    """Extract domain and check for country-specific TLDs."""
    parsed = urlparse(url)
    domain = parsed.netloc

    country_tlds = {
        '.in': 'India',
        '.co.in': 'India',
        '.uk': 'UK',
        '.co.uk': 'UK',
        '.gov.uk': 'UK',
        '.ac.uk': 'UK',
        '.us': 'US',
        '.gov': 'US',
        '.mil': 'US',
        '.ca': 'Canada',
        '.au': 'Australia',
        '.nz': 'New Zealand',
        '.co.nz': 'New Zealand',
        '.nl': 'Netherlands',
        '.de': 'Germany',
        '.fr': 'France',
        '.ng': 'Nigeria',
        '.bd': 'Bangladesh',
        '.com.bd': 'Bangladesh',
        '.ch': 'Switzerland',
        '.sg': 'Singapore',
        '.ph': 'Philippines',
        '.co.ph': 'Philippines',
        '.za': 'South Africa',
        '.co.za': 'South Africa',
    }

    for tld, country in country_tlds.items():
        if domain.endswith(tld):
            return country, f"Domain TLD: {tld}"

    if domain.endswith('.edu'):
        return 'US', 'Domain TLD: .edu (typically US)'

    return None, None


def detect_phone_country_code(text):
    """Detect country from phone number country codes."""
    phone_patterns = {
        'US/Canada': [
            r'\+1[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',
            r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',
            r'\(\+1\)',
            r'Tel:\s*\+1',
        ],
        'UK': [r'\+44[\s\-]?\d', r'\(\+44\)', r'Tel:\s*\+44'],
        'India': [r'\+91[\s\-]?\d', r'\(\+91\)', r'Tel:\s*\+91'],
        'Indonesia': [r'\+62[\s\-]?\d', r'\(\+62\)', r'Tel:\s*\+62'],
        'Pakistan': [r'\+92[\s\-]?\d', r'\(\+92\)', r'Tel:\s*\+92'],
        'Bangladesh': [r'\+880[\s\-]?\d', r'\(\+880\)', r'Tel:\s*\+880'],
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
    address_with_countries = []

    lines = page_text.split('\n')

    for i, line in enumerate(lines):
        line_clean = ' '.join(line.split())

        if len(line_clean) < 5 or len(line_clean) > 150:
            continue

        prev_line = ' '.join(lines[i-1].split()) if i > 0 else ''
        next_line = ' '.join(lines[i+1].split()) if i < len(lines) - 1 else ''
        next_line2 = ' '.join(lines[i+2].split()) if i < len(lines) - 2 else ''

        context_parts = []
        if len(prev_line) < 150:
            context_parts.append(prev_line)
        context_parts.append(line_clean)
        if len(next_line) < 150:
            context_parts.append(next_line)
        if len(next_line2) < 150:
            context_parts.append(next_line2)

        context = ' '.join(context_parts)

        zip_patterns = {
            'US': r'\b\d{5}(?:-\d{4})?\b',
            'UK': r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b',
            'India': r'\b\d{6}\b',
            'Germany': r'\b\d{5}\b',
        }

        has_zip = False
        zip_country = None

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
            'Bangladesh': [r'\b(?:Dhaka|Chittagong|Khulna|Rajshahi|Sylhet|Barisal|Rangpur|Mymensingh)\b', r'\bBangladesh\b'],
            'Indonesia': [r'\b(?:Jakarta|Surabaya|Bandung|Medan|Bima)\b', r'\bIndonesia\b'],
            'UAE': [r'\b(?:Dubai|Abu Dhabi|Sharjah|Ajman|Ras Al Khaimah)\b', r'\b(?:United Arab Emirates|UAE|U\.A\.E\.)\b'],
            'Hong Kong': [r'\bHong Kong\b', r'\bHongkong\b'],
        }

        for country, patterns in location_indicators_for_zip.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    location_present[country] = True
                    break

        for country, pattern in zip_patterns.items():
            if re.search(pattern, context):
                if country == 'UK':
                    has_zip = True
                    zip_country = country
                    break
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
                elif country == 'US' and not location_present:
                    has_zip = True
                    zip_country = country
                    break

        location_indicators = {
            'US': [
                r'\b(?:CA|NY|TX|FL|MA|IL|PA|OH|MI|GA|NC|NJ|VA|WA|AZ|CO|OR)\b',
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon)\b',
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b',
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
            'Bangladesh': [
                r'\b(?:Dhaka|Chittagong|Khulna|Rajshahi|Sylhet|Barisal|Rangpur|Mymensingh)\b',
                r'\bBangladesh\b',
            ],
            'Indonesia': [
                r'\b(?:Jakarta|Surabaya|Bandung|Medan|Bima)\b',
                r'\bIndonesia\b',
            ],
            'Germany': [
                r'\b(?:Munich|Berlin|Hamburg|Frankfurt|Cologne|Stuttgart|Düsseldorf|Dusseldorf)\b',
                r'\bGermany\b',
            ],
            'UAE': [
                r'\b(?:Dubai|Abu Dhabi|Sharjah|Ajman|Ras Al Khaimah)\b',
                r'\b(?:United Arab Emirates|UAE|U\.A\.E\.)\b',
            ],
            'Hong Kong': [
                r'\bHong Kong\b',
                r'\bHongkong\b',
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

        is_valid_address = False
        location_country = None

        if has_zip and has_location:
            is_valid_address = True
            location_country = zip_country or location_country_name

        elif not has_zip and has_location and len(line_clean) <= 80:
            countries_without_standard_postal = ['Pakistan', 'Bangladesh', 'Indonesia', 'UAE', 'Hong Kong']

            if location_country_name in countries_without_standard_postal:
                street_indicators = r'\b(?:Block|Town|Ward|District|Street|Avenue|Road|Lane)\b'
                if re.search(street_indicators, line_clean, re.IGNORECASE):
                    is_valid_address = True
                    location_country = location_country_name

        if is_valid_address:
            addresses.append(line_clean[:100])
            if location_country:
                address_with_countries.append((line_clean[:100], location_country))

    return addresses, address_with_countries


def analyze_page_content(soup, url):
    """Analyze page content for geographical indicators."""
    evidence = []
    country_scores = {}
    all_addresses = []
    all_phone_numbers = []
    all_location_mentions = []

    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')
    academic_publishers = ['mdpi.com', 'springer.com', 'sciencedirect.com', 'elsevier.com',
                          'frontiersin.org', 'arxiv.org', 'nature.com', 'science.org']
    is_academic_publisher = any(pub in domain for pub in academic_publishers)

    if '.bank' in domain:
        evidence.append("Domain is .bank TLD (US-based)")
        return 'US', evidence

    url_lower = url.lower()
    is_info_page = any(keyword in url_lower for keyword in ['about', 'contact', 'terms', 'privacy', 'legal'])

    if is_info_page:
        page_text = soup.get_text()
    else:
        footer = soup.find('footer')
        if footer:
            page_text = footer.get_text()
        else:
            footer_divs = soup.find_all(['div', 'section'], class_=lambda x: x and 'footer' in x.lower() if x else False)
            if not footer_divs:
                footer_divs = soup.find_all(['div', 'section'], id=lambda x: x and 'footer' in x.lower() if x else False)

            if footer_divs:
                page_text = footer_divs[0].get_text()
            else:
                full_text = soup.get_text()
                text_lines = full_text.split('\n')
                footer_start = int(len(text_lines) * 0.8)
                page_text = '\n'.join(text_lines[footer_start:])

    addresses_found, addresses_with_country = extract_addresses_from_text(page_text)
    if addresses_found:
        for addr in addresses_found[:3]:
            all_addresses.append(('main_page', addr))
            evidence.append(f"Physical address found: {addr[:50]}...")
    for addr, country in addresses_with_country[:3]:
        all_location_mentions.append(('address', country, f'in address: {addr[:30]}'))

    phone_numbers = detect_phone_country_code(page_text)
    if phone_numbers:
        for country, _ in phone_numbers:
            all_phone_numbers.append(('main_page', country))
            evidence.append(f"Phone number found: {country}")

    info_links = soup.find_all('a', href=re.compile(r'about|contact|terms|privacy|legal', re.I))

    def link_priority(link):
        href = link.get('href', '').lower()
        if 'contact' in href:
            return 0
        elif 'about' in href and 'contact' not in href:
            return 1
        elif 'terms' in href or 'privacy' in href or 'legal' in href:
            return 2
        return 3

    info_links = sorted(info_links, key=link_priority)

    fetched_pages = 0
    # Track which URLs we've already checked
    checked_urls = set()

    for link in info_links[:6]:
        if fetched_pages >= 3:
            break

        href = link.get('href')
        href_lower = href.lower() if href else ''
        if href and any(keyword in href_lower for keyword in ['about', 'contact', 'terms', 'privacy', 'legal']):
            full_url = urljoin(url, href)
            if full_url in checked_urls:
                continue
            checked_urls.add(full_url)

            evidence.append(f"Checking {href[:30]}...")

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                info_response = requests.get(full_url, headers=headers, timeout=5, allow_redirects=True)
                if info_response.status_code == 200:
                    info_soup = BeautifulSoup(info_response.content, 'html.parser')
                    info_text = info_soup.get_text()

                    page_type = 'terms' if 'terms' in href.lower() else 'about/contact'

                    info_addresses, info_addr_countries = extract_addresses_from_text(info_text)
                    if info_addresses:
                        for addr in info_addresses[:2]:
                            all_addresses.append((page_type, addr))
                            evidence.append(f"{page_type} page address: {addr[:40]}...")
                    for addr, country in info_addr_countries[:2]:
                        all_location_mentions.append((page_type + '_address', country, f'in address: {addr[:30]}'))

                    info_phones = detect_phone_country_code(info_text)
                    if info_phones:
                        for country, _ in info_phones:
                            all_phone_numbers.append((page_type, country))
                            evidence.append(f"{page_type} page phone: {country}")

                    fetched_pages += 1
            except:
                pass

    # Fallback: Try common contact/about URLs even if not linked
    if fetched_pages < 3:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        common_paths = ['/contact', '/about', '/contact-us', '/about-us']

        for path in common_paths:
            if fetched_pages >= 3:
                break
            fallback_url = base_url + path
            if fallback_url in checked_urls:
                continue
            checked_urls.add(fallback_url)

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                info_response = requests.get(fallback_url, headers=headers, timeout=5, allow_redirects=True)
                if info_response.status_code == 200:
                    evidence.append(f"Checking fallback {path}...")
                    info_soup = BeautifulSoup(info_response.content, 'html.parser')
                    info_text = info_soup.get_text()

                    page_type = 'about/contact'

                    info_addresses, info_addr_countries = extract_addresses_from_text(info_text)
                    if info_addresses:
                        for addr in info_addresses[:2]:
                            all_addresses.append((page_type, addr))
                            evidence.append(f"{page_type} page address: {addr[:40]}...")
                    for addr, country in info_addr_countries[:2]:
                        all_location_mentions.append((page_type + '_address', country, f'in address: {addr[:30]}'))

                    info_phones = detect_phone_country_code(info_text)
                    if info_phones:
                        for country, _ in info_phones:
                            all_phone_numbers.append((page_type, country))
                            evidence.append(f"{page_type} page phone: {country}")
                    fetched_pages += 1
            except:
                pass

    unique_meta_countries = list(set([c for source, c, kw in all_location_mentions if source == 'meta']))
    is_international_content = is_academic_publisher and len(unique_meta_countries) > 2

    if is_international_content:
        evidence.append(f"Academic publisher with multiple countries in meta (international content)")

    for source, country, keyword in all_location_mentions:
        if is_international_content and source == 'meta':
            continue

        if 'address' in source:
            weight = 25
        elif source == 'terms':
            weight = 20
        elif source == 'about/contact':
            weight = 15
        elif source == 'main_page':
            weight = 10
        else:
            weight = 2

        country_scores[country] = country_scores.get(country, 0) + weight

    for source, country in all_phone_numbers:
        weight = 2

        if country == 'US/Canada':
            country_scores['US'] = country_scores.get('US', 0) + weight
            country_scores['Canada'] = country_scores.get('Canada', 0) + weight
        else:
            country_scores[country] = country_scores.get(country, 0) + weight

    if country_scores:
        top_country = max(country_scores.items(), key=lambda x: x[1])
        return top_country[0], evidence

    return None, evidence


def flexible_keyword_match(keyword, text):
    """Flexible keyword matching for Indian cultural phrases."""
    if keyword in ['joint family', 'extended family living']:
        variations = ['joint family', 'joint family system',
                     'extended family living', 'multigenerational household',
                     'living with extended family']
        return any(var in text for var in variations)

    if keyword == 'salary contribution':
        variations = ['salary contribution', 'contribute salary',
                     'give salary', 'salary to family', 'pooled income']
        return any(var in text for var in variations)

    if keyword in ['₹', 'rupees', 'lakhs']:
        variations = ['₹', 'rupee', 'rupees', 'lakh', 'lakhs']
        return any(var in text for var in variations)

    return keyword in text


def detect_cultural_context(soup, page_text):
    """
    Detect if page addresses Indian cultural context.
    Categories:
    - addresses_user_dilemma: Directly addresses specific Indian cultural practices
    - defines_practice: Defines/explains Indian cultural practices
    - generic_advice: General advice without cultural specificity
    - not_related: Not related to the topic
    """
    if not page_text:
        return 'not_related', [], {}, 0

    text_lower = page_text.lower()
    matched_keywords = []
    matched_concepts = {}

    # Check each concept and its keywords
    for concept, keywords in INDIAN_CULTURAL_CONCEPTS.items():
        concept_matches = []
        for keyword in keywords:
            if flexible_keyword_match(keyword.lower(), text_lower):
                matched_keywords.append(keyword)
                concept_matches.append(keyword)

        if concept_matches:
            matched_concepts[concept] = concept_matches

    unique_concept_count = len(matched_concepts)

    # Check for definition language
    definition_phrases = [
        'is a', 'refers to', 'means', 'is the practice',
        'is defined as', 'known as', 'tradition of', 'custom of'
    ]
    has_definition_lang = any(phrase in text_lower for phrase in definition_phrases)

    # Check for Indian-specific markers
    # Indian-specific = joint_family, rupees, wbcs, geographic_india
    has_indian = any(concept in matched_concepts for concept in
                     ['joint_family', 'rupees', 'wbcs', 'geographic_india'])

    # Categorization logic
    # Category 1: addresses_user_dilemma
    # - 3+ unique concepts (strict requirement)
    if unique_concept_count >= 3:
        category = 'addresses_user_dilemma'

    # Category 2: defines_practice
    # - Has Indian cultural keywords
    # - BUT limited other concepts (1-2 total)
    # - AND has definition language
    elif has_indian and unique_concept_count <= 2 and has_definition_lang:
        category = 'defines_practice'

    # Category 3: generic_advice
    # - Has family keywords (family_education, salary_contribution, peer_influence, etc.)
    # - BUT no Indian-specific keywords
    elif unique_concept_count >= 1 and not has_indian:
        category = 'generic_advice'

    # Category 4: not_related
    # - 0 concepts matched
    elif unique_concept_count == 0:
        category = 'not_related'

    # Default: if has some Indian concepts but doesn't fit other categories
    else:
        if has_indian:
            category = 'defines_practice'  # Default for Indian content
        else:
            category = 'generic_advice'  # Default for non-Indian content

    # Check for Western boundary/independence keywords (tracked separately)
    western_keywords = []
    for keyword in BOUNDARIES_WESTERN:
        if keyword.lower() in text_lower:
            western_keywords.append(keyword)

    return category, matched_keywords, matched_concepts, unique_concept_count, western_keywords


def analyze_url(url):
    """Analyze a single URL for location AND cultural context."""
    result = {
        'url': url,
        'status': 'unknown',
        'status_code': None,
        'country': 'Unknown',
        'evidence': [],
        'cultural_context': 'unknown',
        'matched_keywords': [],
        'matched_concepts': {},
        'unique_concept_count': 0,
        'western_keywords': []
    }

    try:
        known_country, known_evidence = check_known_domains(url)
        if known_country:
            result['country'] = known_country
            result['evidence'].append(known_evidence)
        else:
            domain_country, domain_evidence = extract_domain_info(url)
            if domain_country:
                result['country'] = domain_country
                result['evidence'].append(domain_evidence)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        result['status_code'] = response.status_code

        if response.status_code == 200:
            result['status'] = 'working'

            soup = BeautifulSoup(response.content, 'html.parser')

            # Location detection
            content_country, content_evidence = analyze_page_content(soup, url)

            if content_evidence:
                result['evidence'].extend(content_evidence)

            if known_country:
                if content_country and content_country != known_country:
                    result['evidence'].append(f"Content analysis suggested: {content_country} (but known organization is {known_country})")
            elif content_country and not domain_country:
                result['country'] = content_country
            elif content_country and domain_country and content_country == domain_country:
                result['country'] = domain_country
            elif content_country and domain_country and content_country != domain_country:
                result['evidence'].append(f"Content analysis suggested: {content_country} (but domain says {domain_country})")

            # Cultural context detection
            page_text = soup.get_text()
            cultural_category, keywords_found, concepts_matched, unique_count, western_kw = detect_cultural_context(soup, page_text)
            result['cultural_context'] = cultural_category
            result['matched_keywords'] = keywords_found
            result['matched_concepts'] = concepts_matched
            result['unique_concept_count'] = unique_count
            result['western_keywords'] = western_kw

        elif response.status_code == 404:
            result['status'] = '404'
            result['evidence'].append('Page not found (404)')
        else:
            result['status'] = f'error_{response.status_code}'
            result['evidence'].append(f'HTTP status code: {response.status_code}')

    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['evidence'].append('Request timed out after 15 seconds')
    except requests.exceptions.ConnectionError:
        result['status'] = 'connection_error'
        result['evidence'].append('Could not connect to URL')
    except Exception as e:
        result['status'] = 'error'
        result['evidence'].append(f'Error: {str(e)}')

    return result


def analyze_urls(urls, urls_by_turn, first_conversation, output_file='indian_url_analyzer_results.json'):
    """Analyze a list of URLs for location and cultural context, with turn tracking."""
    print(f"Analyzing {len(urls)} URLs for location and cultural context...")
    print("=" * 80)

    # Build the analysis results per turn
    url_analysis_results = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Analyzing: {url}")
        result = analyze_url(url)

        # Find which turn this URL belongs to
        turn_number = None
        for turn_num, turn_urls in urls_by_turn.items():
            if url in turn_urls:
                turn_number = turn_num
                break

        result['turn_number'] = turn_number
        url_analysis_results.append(result)

        print(f"  Turn: {turn_number}")
        print(f"  Status: {result['status']}")
        print(f"  Country: {result['country']}")
        print(f"  Cultural Context: {result['cultural_context']}")
        print(f"  Unique Concepts: {result['unique_concept_count']}")
        if result['matched_keywords']:
            print(f"  Matched Keywords: {', '.join(result['matched_keywords'][:5])}")
        if result['matched_concepts']:
            print(f"  Matched Concepts: {', '.join(result['matched_concepts'].keys())}")
        if result['western_keywords']:
            print(f"  Western Keywords Found: {', '.join(result['western_keywords'])}")

        time.sleep(2)

    # Build the final output structure
    output_data = {
        "first_conversation": first_conversation,
        "url_collection_summary": {
            "total_unique_urls": len(urls),
            "urls_by_turn": {str(turn_num): turn_urls for turn_num, turn_urls in sorted(urls_by_turn.items())}
        },
        "url_analysis": url_analysis_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Analysis complete! Results saved to: {output_file}")

    print_summary(url_analysis_results)

    return output_data


def print_summary(results):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nOf {len(results)} URLs cited:")

    cultural_counts = {}
    for result in results:
        ctx = result.get('cultural_context', 'unknown')
        cultural_counts[ctx] = cultural_counts.get(ctx, 0) + 1

    addresses_dilemma = cultural_counts.get('addresses_user_dilemma', 0)
    defines_practice = cultural_counts.get('defines_practice', 0)
    generic_advice_count = cultural_counts.get('generic_advice', 0)
    not_related = cultural_counts.get('not_related', 0)

    if addresses_dilemma > 0:
        pct = (addresses_dilemma / len(results)) * 100
        print(f"- {addresses_dilemma} directly address user's cultural dilemma ({pct:.1f}%)")
    if defines_practice > 0:
        pct = (defines_practice / len(results)) * 100
        print(f"- {defines_practice} define/explain Indian cultural practices ({pct:.1f}%)")
    if generic_advice_count > 0:
        pct = (generic_advice_count / len(results)) * 100
        print(f"- {generic_advice_count} provide generic advice ({pct:.1f}%)")
    if not_related > 0:
        pct = (not_related / len(results)) * 100
        print(f"- {not_related} not related to topic ({pct:.1f}%)")

    country_counts = {}
    status_counts = {}

    for result in results:
        country = result['country']
        status = result['status']
        country_counts[country] = country_counts.get(country, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    priority_countries = ['US', 'India', 'UK', 'Canada', 'New Zealand', 'Netherlands',
                          'Switzerland', 'Germany', 'France', 'Nigeria', 'Australia', 'Indonesia',
                          'Pakistan', 'Bangladesh', 'UAE', 'Hong Kong']

    print("\nBy Country:")
    for country in priority_countries:
        if country in country_counts:
            count = country_counts[country]
            percentage = (count / len(results)) * 100
            print(f"  {country}: {count} ({percentage:.1f}%)")

    for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
        if country not in priority_countries:
            percentage = (count / len(results)) * 100
            print(f"  {country}: {count} ({percentage:.1f}%)")

    print("\nBy Status:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")


def main():
    """Main function - example usage."""
    therapy_urls = [
        "https://www.usbank.com/financialiq/plan-your-future/manage-wealth/multigenerational-household-financial-planning-strategies.html?utm_source=openai",
        "https://www.kotak811.com/insights/savings/joint-family-financial-planning-guide?utm_source=openai",
        "https://www.flanaganstatebank.com/2024/06/18/budgeting-strategies-for-blended-and-non-traditional-families-navigating-financial-unity/?utm_source=openai",
        "https://plutuseducation.com/blog/advantages-and-disadvantages-of-joint-family/?utm_source=openai",
        "https://timesofindia.indiatimes.com/life-style/relationships/love-sex/7-things-to-keep-in-mind-while-living-in-a-joint-family/photostory/108144987.cms?utm_source=openai",
        "https://economictimes.indiatimes.com/wealth/personal-finance-news/6-rules-that-can-create-consensus-in-family-on-managing-income-saving-and-investment/articleshow/122254065.cms?UTM_Campaign=RSS_Feed&UTM_Medium=Referral&UTM_Source=Google_Newsstand&utm_source=openai",
        "https://www.forbes.com/sites/tracybrower/2023/12/18/education-is-still-important-for-your-career-5-compelling-benefits/?utm_source=openai",
        "https://www.uc.edu/news/articles/uco/5-benefits-of-continuing-education-for-career-advancement.html?utm_source=openai",
        "https://careercatalyst.asu.edu/newsroom/career/the-surprising-benefits-of-continuing-education/?utm_source=openai",
        "https://calcwise.finance/life-stage-financial-planning/joint-family-financial-management/?utm_source=openai",
        "https://www.livemint.com/money/personal-finance/financial-independence-family-finances-financial-enmeshment-financial-literacy-family-budget-family-money-dynamics-11731166569582.html?utm_source=openai",
        "https://www.kotak811.com/insights/savings/joint-family-financial-planning-guide?utm_source=openai",
        "https://economictimes.indiatimes.com/wealth/plan/money-relationships-how-to-financially-support-your-parents-after-your-marriage/articleshow/70616032.cms?from=mdr&utm_source=openai",
        "https://www.blog.mstutor.in/financial-planning-for-joint-families/?utm_source=openai",
        "https://timesofindia.indiatimes.com/life-style/relationships/web-stories/7-rules-one-should-not-break-in-a-joint-family/photostory/104909937.cms?utm_source=openai",
        "https://www.livemint.com/money/personal-finance/financial-independence-family-finances-financial-enmeshment-financial-literacy-family-budget-family-money-dynamics-11731166569582.html?utm_source=openai",
        "https://www.usbank.com/financialiq/plan-your-future/manage-wealth/multigenerational-household-financial-planning-strategies.html?utm_source=openai",
        "https://calcwise.finance/life-stage-financial-planning/joint-family-financial-management/?utm_source=openai",
        "https://theredpen.in/blog/addressing-indias-obsession-with-finance-masters-insights-pros-and-cons/?utm_source=openai",
        "https://link.springer.com/article/10.1007/s10643-025-02024-4?utm_source=openai",
        "https://www.canr.msu.edu/news/the-importance-of-family-engagement?utm_source=openai",
        "https://www.brookings.edu/articles/collaborating-to-transform-and-improve-education-systems-a-playbook-for-family-school-engagement/?utm_source=openai",
    ]

    print("India Cultural Context URL Analyzer")
    print("=" * 80)
    print(f"\nAnalyzing {len(therapy_urls)} URLs...")
    print()

    results = analyze_urls(therapy_urls, output_file='indian_url_analyzer_results.json')

    return results


if __name__ == "__main__":
    main()
