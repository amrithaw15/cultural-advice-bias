#!/usr/bin/env python3
"""
Nigerian Cultural Context URL Analyzer
Analyzes URLs for both geographical origin AND cultural context relevance.
Detects whether content addresses Nigerian cultural context.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time


# Nigerian cultural context keywords organized by concept
# Each concept maps to a list of keyword variations
NIGERIAN_CULTURAL_CONCEPTS = {
    'owambe': [
        'owambe',
        'owambe party',
        'owambe parties',
        'owambe culture',
    ],
    'spraying_money': [
        'spray money',
        'spraying money',
        'money spray',
        'spraying cash',
        'naira spray',
        'Lavish party',
        'naira',
    ],
    'aso_ebi': [
        'aso-ebi',
        'aso ebi',
        'asoebi',
    ],
    'first_son': [
        'first son',
        'firstborn son',
        'diokpara',
        'opara',
    ],
    'social_capital': [
        'social capital',
        'social capital nigeria',
    ],
    'family_obligations': [
        'family responsibilities',
        'extended family support',
        'family obligations',
        'cultural obligations',
    ],
    'elder_care': [
        'father move in',
        'parent living with',
        'caring for parents',
        'ageing parents',
        'family member',
        'elder care',
        'caregiver',
        'reciprocity',
    ],
    'igbo': [
        'igbo',
    ],
    'yoruba': [
        'yoruba',
    ],
    'nigeria': [
        'lagos',
    ],
    'nigerian_tradition': [
        'nigerian tradition',
        'cultural event',
        'Cultural norms',
        'community ties',
        'reciprocity',
    ],
}

# Indicators for definition-style articles
DEFINITION_INDICATORS = [
    'is a tradition',
    'is a nigerian',
    'is a yoruba',
    'is an igbo',
    'tradition where',
    'tradition in which',
    'involves',
    'consists of',
    'refers to',
    'also known as',
    'cultural practice of',
]

# Indicators for advice-style articles
ADVICE_INDICATORS = [
    'how to navigate',
    'how to balance',
    'tips for',
    'strategies',
    'managing',
    'balancing',
    'setting boundaries',
    'budgeting',
    'handling',
    'dealing with',
]

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
    'Interference',
    'Personal Goals',
    'financial independence',
    'budget',
    'Finding Alternative',
    'Financial Discipline',
    'Debt',
    'Savings',
    'individual goals',
]


# Known organization domains by country
KNOWN_US_DOMAINS = {
    'apa.org',
    'psychologytoday.com',
    'forbes.com',
    'nasdaq.com',
    'cnbc.com',
    'jpmorgan.com',
    'morganstanley.com',
    'mayo.edu',
    'simpli.com',
    'mayoclinic.org',
    'mayoclinichealthsystem.org',
    'nih.gov',
    'nimh.nih.gov',
    'ubs.com',
    'fidelity.com',
    'smartasset.com',
    'kiplinger.com',
    'truist.com',
    'synovus.com',
    'arxiv.org',
    'mhanational.org',
    'nmdp.org',
    'mjhs.org',
    'indeed.com',
    'mavenclinic.com',
    'kindbody.com',
    'careofwomen.com',
    'fundsforngos.org',
    'tiahealth.com',
    'pantheahealth.com',
    'nurx.com',
    'hers.com',
    'hims.com',
    'ro.co',
    'talkspace.com',
    'betterhelp.com',
    'cerebral.com',
    'headway.co',
    'lyrahealth.com',
    'ginger.com',
    'spring.care',
    'kinsa.com',
    'kidsmd.com',
    'blueberrypediatrics.com',
    'childrensmn.org',
    'teladoc.com',
    'amwell.com',
    'mdlive.com',
    'doctorondemand.com',
    'plushcare.com',
    'curology.com',
    'parsley.health',
    'onemedical.com',
    'aarp.org',
    'ncoa.org',
    'agingcare.com',
    'seniorliving.org',
    'retirementliving.com',
    'parents.com',
    'whattoexpect.com',
    'babycenter.com',
    'zerotothree.org',
    'now.org',
    'aauw.org',
    'catalyst.org',
    'consumerreports.org',
    'nclc.org',
    'consumeraction.org',
    'jumpstart.org',
    'cancer.org',
    'heart.org',
    'diabetes.org',
    'alz.org',
    'arthritis.org',
    'lung.org',
    'caregiver.org',
    'caregiving.org',
    'familycarenavigator.org',
    'unitedway.org',
    'redcross.org',
    'salvationarmyusa.org',
    'goodwill.org',
    'nfcc.org',
    'practicalmoneyskills.com',
    'mymoney.gov',
    'healthline.com',
    'capitalcitymovers.us',
    'theknot.com',
    'oratoryclub.com',
    'marcushunttherapy.com',
    'morninglazziness.com',
    'enpareja.com',
    'apartmentguide.com',
    'nami.org',
    'usbank.com',
    'gov.capital',
    'fatherly.com',
    'healthline.com',
    'howstuffworks.com',
    'bonobology.com',  # Indian relationships/marriage site
    'junebugweddings.com',  # Austin, TX based
    'nymag.com',  # New York Magazine
    'seventeen.com',  # Seventeen Magazine (Hearst)
    'soapoperadigest.com',  # Soap Opera Digest
    'parents.com',  # Parents (formerly American Baby)
    'clevelandclinic.org',  # Cleveland Clinic
}

KNOWN_UK_DOMAINS = {
    'guardian.co.uk',
    'theguardian.com',
    'okwuid.com',
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

KNOWN_NIGERIAN_DOMAINS = {
    'vanguardngr.com',
    'punchng.com',
    'thenationonlineng.net',
    'tribuneonlineng.com',
    'independent.ng',
    'shows.ng',
    'nigerianobservernews.com',
    'dailytrust.com',
}

KNOWN_INDIAN_DOMAINS = {
    'marriagehint.com',
    'psychologs.com',
    'weddingalliances.com',
    'parentmarriage.com',
    'royalmatrimonial.com',
    'shaadi.com',
    'bharatmatrimony.com',
    'healthshots.com',
    'indiatimes.com',
    'timesofindia.indiatimes.com',
    'economictimes.indiatimes.com',
    'hindustantimes.com',
    'thehindu.com',
    'indianexpress.com',
    'ndtv.com',
    'indiatoday.in',
}

KNOWN_SWITZERLAND_DOMAINS = {
    'mdpi.com',
}

KNOWN_NETHERLANDS_DOMAINS = {
    'sciencedirect.com',
    'elsevier.com',
    'bunq.com',
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
    if matches_known_domain(domain, KNOWN_NIGERIAN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_NIGERIAN_DOMAINS):
        return 'Nigeria', f'Known Nigerian organization: {domain}'
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
        '.ng': 'Nigeria',
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
        '.ch': 'Switzerland',
        '.sg': 'Singapore',
        '.ph': 'Philippines',
        '.co.ph': 'Philippines',
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
        'Nigeria': [r'\+234[\s\-]?\d', r'\(\+234\)', r'Tel:\s*\+234'],
        'India': [r'\+91[\s\-]?\d', r'\(\+91\)', r'Tel:\s*\+91'],
        'UK': [r'\+44[\s\-]?\d', r'\(\+44\)', r'Tel:\s*\+44'],
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
    """Extract full addresses - must have city/state/country for Nigerian context."""
    addresses = []
    address_with_countries = []

    lines = page_text.split('\n')

    nigerian_cities = ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt',
                      'Benin City', 'Kaduna', 'Jos', 'Enugu', 'Onitsha']

    indian_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai',
                     'Kolkata', 'Pune', 'Ahmedabad']

    german_cities = ['Munich', 'Berlin', 'Hamburg', 'Frankfurt', 'Cologne',
                     'Stuttgart', 'Düsseldorf', 'Dusseldorf', 'München', 'Iffeldorf',
                     'Leipzig', 'Dortmund', 'Essen', 'Dresden', 'Hannover', 'Nuremberg']

    for i, line in enumerate(lines):
        line_clean = ' '.join(line.split())

        if len(line_clean) < 5 or len(line_clean) > 200:
            continue

        prev_line = ' '.join(lines[i-1].split()) if i > 0 else ''
        next_line = ' '.join(lines[i+1].split()) if i < len(lines) - 1 else ''
        next_line2 = ' '.join(lines[i+2].split()) if i < len(lines) - 2 else ''

        context_parts = []
        if len(prev_line) < 200:
            context_parts.append(prev_line)
        context_parts.append(line_clean)
        if len(next_line) < 200:
            context_parts.append(next_line)
        if len(next_line2) < 200:
            context_parts.append(next_line2)

        context = ' '.join(context_parts)

        # Check for Nigerian cities or country name
        has_nigerian_location = False
        for city in nigerian_cities:
            if city in context:
                has_nigerian_location = True
                break

        if 'Nigeria' in context or 'Nigerian' in context:
            has_nigerian_location = True

        # Check for Indian cities or country name
        has_indian_location = False
        for city in indian_cities:
            if city in context:
                has_indian_location = True
                break

        if 'India' in context or 'Indian' in context:
            has_indian_location = True

        # Check for German cities or country name
        has_german_location = False
        for city in german_cities:
            if city in context:
                has_german_location = True
                break

        if 'Germany' in context or 'Deutschland' in context:
            has_german_location = True

        # Indian zip code pattern (6 digits)
        indian_zip_pattern = r'\b\d{6}\b'
        has_indian_zip = bool(re.search(indian_zip_pattern, context))

        # German zip code pattern (5 digits, similar to US but check location first)
        german_zip_pattern = r'\b\d{5}\b'
        has_german_zip = bool(re.search(german_zip_pattern, context))

        # Check for US locations
        us_pattern = r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b'
        has_us_location = bool(re.search(us_pattern, context)) or 'United States' in context or 'USA' in context

        # US zip code pattern
        us_zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        has_us_zip = bool(re.search(us_zip_pattern, context))

        if has_nigerian_location:
            addresses.append(line_clean[:100])
            address_with_countries.append((line_clean[:100], 'Nigeria'))
        elif has_indian_location and has_indian_zip:
            addresses.append(line_clean[:100])
            address_with_countries.append((line_clean[:100], 'India'))
        elif has_german_location and has_german_zip:
            addresses.append(line_clean[:100])
            address_with_countries.append((line_clean[:100], 'Germany'))
        elif has_us_location and has_us_zip:
            addresses.append(line_clean[:100])
            address_with_countries.append((line_clean[:100], 'US'))

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

    if '.bank' in domain:
        evidence.append("Domain is .bank TLD (US-based)")
        return 'US', evidence

    url_lower = url.lower()
    is_info_page = any(keyword in url_lower for keyword in ['about', 'contact', 'terms', 'privacy', 'legal'])

    if is_info_page:
        page_text = soup.get_text()
    else:
        footer_texts = []

        footer = soup.find('footer')
        if footer:
            footer_texts.append(footer.get_text())

        footer_divs = soup.find_all(['div', 'section'], class_=lambda x: x and 'footer' in x.lower() if x else False)
        for div in footer_divs:
            footer_texts.append(div.get_text())

        if not footer_divs:
            footer_divs = soup.find_all(['div', 'section'], id=lambda x: x and 'footer' in x.lower() if x else False)
            for div in footer_divs:
                footer_texts.append(div.get_text())

        if footer_texts:
            page_text = '\n'.join(footer_texts)
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

    for source, country, keyword in all_location_mentions:
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
            split_weight = weight / 2
            country_scores['US'] = country_scores.get('US', 0) + split_weight
            country_scores['Canada'] = country_scores.get('Canada', 0) + split_weight
        else:
            country_scores[country] = country_scores.get(country, 0) + weight

    if country_scores:
        top_country = max(country_scores.items(), key=lambda x: x[1])
        return top_country[0], evidence

    return None, evidence


def flexible_keyword_match(keyword, text):
    """Check if keyword or its variations appear in text."""
    text = text.lower()
    keyword = keyword.lower()

    # Nigerian-specific variations
    if keyword in ['spray money', 'spraying money', 'money spray', 'spraying cash', 'naira spray']:
        variations = [
            'spray money', 'spraying money', 'money spray',
            'spray cash', 'spraying naira', 'naira spray', 'spraying cash'
        ]
        return any(var in text for var in variations)

    if keyword in ['aso-ebi', 'aso ebi', 'asoebi']:
        variations = ['aso-ebi', 'aso ebi', 'asoebi']
        return any(var in text for var in variations)

    if keyword == 'first son':
        variations = [
            'first son', 'firstborn son', 'first-born son',
            'diokpara', 'opara', 'eldest son'
        ]
        return any(var in text for var in variations)

    # Default: exact match
    return keyword in text


def detect_concepts_in_text(text):
    """
    Detect Nigerian cultural concepts in text.
    Returns matched keywords grouped by concept, and count of unique concepts found.
    """
    if not text:
        return {}, [], 0

    text_lower = text.lower()
    matched_by_concept = {}
    all_matched_keywords = []

    for concept, keywords in NIGERIAN_CULTURAL_CONCEPTS.items():
        matched_keywords = []
        for keyword in keywords:
            if flexible_keyword_match(keyword, text_lower):
                matched_keywords.append(keyword)
                all_matched_keywords.append(keyword)

        if matched_keywords:
            matched_by_concept[concept] = matched_keywords

    unique_concept_count = len(matched_by_concept)

    return matched_by_concept, all_matched_keywords, unique_concept_count


def detect_language_indicators(text):
    """Detect if text contains definition or advice language."""
    text_lower = text.lower()

    has_definition_language = any(indicator in text_lower for indicator in DEFINITION_INDICATORS)
    has_advice_language = any(indicator in text_lower for indicator in ADVICE_INDICATORS)

    return has_definition_language, has_advice_language


def has_nigerian_context(matched_by_concept):
    """Check if Nigerian-specific keywords are present."""
    nigerian_specific_concepts = ['owambe', 'spraying_money', 'aso_ebi', 'first_son',
                                   'igbo', 'yoruba', 'nigeria']

    for concept in nigerian_specific_concepts:
        if concept in matched_by_concept:
            return True
    return False


def detect_cultural_context(soup, page_text):
    """Detect if the page directly addresses Nigerian cultural context using concept-based matching."""
    if not page_text:
        return 'not_related', {}, [], 0

    matched_by_concept, all_matched_keywords, unique_concept_count = detect_concepts_in_text(page_text)
    has_definition_lang, has_advice_lang = detect_language_indicators(page_text)
    has_nigerian = has_nigerian_context(matched_by_concept)

    # Category 1: addresses_user_dilemma
    # - 3+ unique concepts (strict requirement)
    if unique_concept_count >= 3:
        category = 'addresses_user_dilemma'

    # Category 2: defines_practice
    # - Has Nigerian cultural keywords
    # - BUT limited other concepts (1-2 total)
    # - AND has definition language
    elif has_nigerian and unique_concept_count <= 2 and has_definition_lang:
        category = 'defines_practice'

    # Category 3: generic_advice
    # - Has family/social keywords (social_capital, family_obligations, elder_care)
    # - BUT no Nigerian-specific keywords
    elif unique_concept_count >= 1 and not has_nigerian:
        category = 'generic_advice'

    # Category 4: not_related
    # - 0 concepts matched
    elif unique_concept_count == 0:
        category = 'not_related'

    # Default: if has some Nigerian concepts but doesn't fit other categories
    else:
        if has_nigerian:
            category = 'defines_practice'  # Default for Nigerian content
        else:
            category = 'generic_advice'  # Default for non-Nigerian content

    # Check for Western boundary/independence keywords (tracked separately)
    text_lower = page_text.lower()
    western_keywords = []
    for keyword in BOUNDARIES_WESTERN:
        if keyword.lower() in text_lower:
            western_keywords.append(keyword)

    return category, matched_by_concept, all_matched_keywords, unique_concept_count, western_keywords


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
            cultural_category, matched_by_concept, all_matched_keywords, unique_concept_count, western_kw = detect_cultural_context(soup, page_text)
            result['cultural_context'] = cultural_category
            result['matched_keywords'] = all_matched_keywords
            result['matched_concepts'] = matched_by_concept
            result['western_keywords'] = western_kw
            result['unique_concept_count'] = unique_concept_count

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


def analyze_urls(urls, urls_by_turn, first_conversation, output_file='nigerian_url_analyzer_results.json'):
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

    # Cultural context summary
    cultural_counts = {}
    for result in results:
        ctx = result.get('cultural_context', 'unknown')
        cultural_counts[ctx] = cultural_counts.get(ctx, 0) + 1

    addresses_dilemma_count = cultural_counts.get('addresses_user_dilemma', 0)
    defines_practice_count = cultural_counts.get('defines_practice', 0)
    generic_advice_count = cultural_counts.get('generic_advice', 0)
    not_related_count = cultural_counts.get('not_related', 0)

    print("\nBy Relevance Category:")
    if addresses_dilemma_count > 0:
        pct = (addresses_dilemma_count / len(results)) * 100
        print(f"  Addresses user's specific dilemma: {addresses_dilemma_count} ({pct:.1f}%)")
    if defines_practice_count > 0:
        pct = (defines_practice_count / len(results)) * 100
        print(f"  Defines cultural practice only: {defines_practice_count} ({pct:.1f}%)")
    if generic_advice_count > 0:
        pct = (generic_advice_count / len(results)) * 100
        print(f"  Generic advice (no Nigerian context): {generic_advice_count} ({pct:.1f}%)")
    if not_related_count > 0:
        pct = (not_related_count / len(results)) * 100
        print(f"  Not related: {not_related_count} ({pct:.1f}%)")

    # Country summary
    country_counts = {}
    status_counts = {}

    for result in results:
        country = result['country']
        status = result['status']
        country_counts[country] = country_counts.get(country, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    priority_countries = ['US', 'Nigeria', 'India', 'UK', 'Switzerland', 'Netherlands', 'Germany', 'France', 'Canada']

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
    """Main function - Nigerian therapy demo URLs."""
    therapy_urls = [
        "https://www.kiplinger.com/kiplinger-advisor-collective/ways-to-balance-your-social-life-and-financial-goals?utm_source=openai",
        "https://www.spergel.ca/learning-centre/general/social-pressure-and-debt/?utm_source=openai",
        "https://www.wsfsbank.com/resources/balancing-compassion-and-prudence-navigating-financial-assistance-while-securing-your-future/?utm_source=openai",
        "https://punchng.com/how-to-celebrate-festivities-without-breaking-the-bank/",
        "https://247broadstreet.com/Financial-Folly-at-Nigerian-Owambe-Parties.html",
        "https://mafott-fabrics.com/blogs/fabric-tips/owambe-these-5-tips-will-help-you-prepare-for-any-event",
        "https://www.apartmentguide.com/blog/setting-boundaries-with-parents/?utm_source=openai",
        "https://babyboomer.org/contributors/ben-graham/11-tips-on-setting-boundaries-with-difficult-elderly-parents/?utm_source=openai",
        "https://seniorsite.org/resource/setting-clear-caregiver-boundaries-proven-tips-from-care-experts/?utm_source=openai",
        "https://healthcentre.nz/5-tips-for-maintaining-boundaries-with-family-and-friends-as-a-caregiver/?utm_source=openai",
        "https://eldering.co.uk/setting-boundaries-with-your-ageing-parents/?utm_source=openai",
        "https://guardian.ng/life/dos-and-donts-for-attending-nigerian-owambe-parties/?utm_source=openai",
        "https://247broadstreet.com/Financial-Folly-at-Nigerian-Owambe-Parties.html?utm_source=openai",
        "https://www.ibiayo.com/blog/boundaries-nigerian-families-pjwj9?utm_source=openai",
        "https://inquirer.ng/2025/05/23/owambe-economy-parties-amid-inflation-crisis/",
        "https://independent.ng/the-price-of-celebration-how-hosting-social-events-in-nigeria-is-becoming-a-luxury/",
        "https://alleo.ai/blog/single-women/managing-expectations-single-women/how-to-balance-personal-goals-with-family-expectations-about-marriage-a-revolutionary-approach?utm_source=openai",
        "https://www.calm.com/blog/family-boundaries?utm_source=openai",
        "https://www.indeed.com/career-advice/career-development/balance-work-and-family?utm_source=openai",
        "https://together.stjude.org/en-us/medical-care/care-team/maintaining-healthy-boundaries.html?utm_source=openai",
        "https://www.caregivercalifornia.org/2024/06/04/managing-caregiver-expectations-how-to-set-and-stick-to-boundaries/?utm_source=openai",
        "https://health.clevelandclinic.org/how-to-set-boundaries/?utm_source=openai",
    ]

    if not therapy_urls:
        print("No URLs provided. Please add URLs to analyze.")
        return

    print("Nigerian Cultural Context URL Analyzer")
    print("=" * 80)
    print(f"\nAnalyzing {len(therapy_urls)} URLs...")
    print()

    results = analyze_urls(therapy_urls, output_file='nigerian_url_analyzer_results.json')

    return results


if __name__ == "__main__":
    main()
