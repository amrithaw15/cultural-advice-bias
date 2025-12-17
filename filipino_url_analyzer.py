#!/usr/bin/env python3
"""
Filipino Cultural Context URL Analyzer
Analyzes URLs for both geographical origin AND cultural context relevance.
Detects whether content addresses Filipino cultural context.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time


# Cultural context keywords organized by concept
# Each concept maps to a list of keyword variations
FILIPINO_CULTURAL_CONCEPTS = {
    'pamanhikan': [
        'pamanhikan',
        'pamamanhikan',
    ],
    'living_with_family': [
        'living with in-laws',
        'living with parents',
        'multigenerational household',
        'extended family living',
        'dealing with in-laws',
        'in-laws relationship',
        'relationship with in-laws',
        'healthy with in-laws',
        'happy with in-laws',
        'parenting help',
        'grandparents',
        'in-laws marriage',
        'your in-laws',
    ],
    'family_contributions': [
        'wedding contributions',
        'family expectations',
        'family drama',
        'family customs',
        'family contributions',
    ],
    'preparing_for_baby': [
        'preparing for a baby',
        'preparing for parenthood',
        'expecting parents',
        'starting a family',
        'having a baby',
        'raising children',
        'grandchildren',
        'raising a baby',
        'baby planning',
        'Parenthood',
        'fatherhood',
        'parenthood preparation',
    ],
    'quezon_city': [
        'quezon city',
    ],
    'manila': [
        'manila',
        'Philippines',
    ],
    'filipino_tradition': [
        'filipino tradition',
        'Kasal',
        'philippine tradition',        
    ],
    'barrio': [
        'barrio',
    ],
    'barangay': [
        'barangay',
    ],
    'utang_na_loob': [
        'utang na loob',
    ],
    'pakikisama': [
        'pakikisama',
    ],
    'hiya': [
        'hiya',
    ],
    'kapwa': [
        'kapwa',
    ],
    'filipino_grandparents': [
        'lola',
        'lolo',
        'lola and lolo',
        'lolo and lola',
        'apo ko',
    ],
}

# Indicators for definition-style articles
DEFINITION_INDICATORS = [
    'is a tradition',
    'is a filipino',
    'is a formal',
    'tradition where',
    'tradition in which',
    'involves the',
    'consists of',
    'refers to',
    'also known as',
]

# Indicators for advice-style articles
ADVICE_INDICATORS = [
    'how to navigate',
    'tips for',
    'strategies',
    'managing',
    'balancing',
    'communicating',
    'respecting',
    'handling',
]

# Western boundary/independence keywords (tracked separately, not counted in concepts)
BOUNDARIES_WESTERN = [
    'boundaries',
    'personal boundaries',
    'set boundaries',
    'personal space',
    'Open Communication',
    'Couple Time',
    'delegate',
    'Assert',
    'Assertive',
    'Self Care',
    'Interference',
    'Personal Goals',
    'financial independence',
    'Career Balance',
    'Work-life balance',
    'individual goals',
]


# Known organization domains by country
KNOWN_US_DOMAINS = {
    'apa.org',
    'forbes.com',
    'psychologytoday.com',
    'nasdaq.com',
    'cnbc.com',
    'gov.capital',
    'jpmorgan.com',
    'morganstanley.com',
    'mayo.edu',
    'mayoclinic.org',
    'simpli.com',
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
    'tiahealth.com',
    'pantheahealth.com',
    'healthline.com',
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
    'usbank.com',
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
    'capitalcitymovers.us',
    'theknot.com',
    'oratoryclub.com',
    'fatherly.com',
    'marcushunttherapy.com',
    'morninglazziness.com',
    'enpareja.com',
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
    'sfcsbc.com',  # Filipino Canadian diaspora
    'mabuhaycanada.org',  # Filipino Canadian
}

KNOWN_FILIPINO_DOMAINS = {
    # 'nuptials.ph',  # Expired server - handled separately
    'inspirations.ph',
    'kasal.com',
    'wedding.com.ph',
    'iriga.gov.ph',  # Filipino government
    'mangyan.org',  # Filipino cultural
    'rappler.com',
    'inquirer.net',
    'philstar.com',
    'gma.network',
    'abs-cbn.com',
    'manilabulletin.com.ph',
    'festivepinoy.com',  # Filipino lifestyle/cultural
    'femalenetwork.com',  # Filipino women's magazine
    'richestph.com',  # Filipino financial/investment site
}

KNOWN_INDIAN_DOMAINS = {
    'marriagehint.com',
    'weddingalliances.com',
    'healthshots.com',
    'parentmarriage.com',
    'royalmatrimonial.com',
    'shaadi.com',
    'bharatmatrimony.com',
    'indiatimes.com',
    'timesofindia.indiatimes.com',
    'economictimes.indiatimes.com',
    'hindustantimes.com',
    'thehindu.com',
    'indianexpress.com',
    'ndtv.com',
    'indiatoday.in',
}

KNOWN_PAKISTAN_DOMAINS = {
    'dawn.com',
    'thenews.com.pk',
    'tribune.com.pk',
    'geo.tv',
    'samaa.tv',
    'nation.com.pk',
}

KNOWN_BANGLADESH_DOMAINS = {
    'thedailystar.net',
    'dhakatribune.com',
    'bdnews24.com',
    'newagebd.net',
    'prothomalo.com',
}

KNOWN_SRI_LANKA_DOMAINS = {
    'dailymirror.lk',
    'sundaytimes.lk',
    'island.lk',
    'adaderana.lk',
}

KNOWN_THAILAND_DOMAINS = {
    'bangkokpost.com',
    'nationthailand.com',
    'thaipbsworld.com',
}

KNOWN_VIETNAM_DOMAINS = {
    'vnexpress.net',
    'vietnamnews.vn',
    'thanhniennews.com',
}

KNOWN_SINGAPORE_DOMAINS = {
    'straitstimes.com',
    'thomsonmedical.com',
    'channelnewsasia.com',
    'newsbytesapp.com',  # has Filipino content
    'todayonline.com',
}

KNOWN_MALAYSIA_DOMAINS = {
    'thestar.com.my',
    'nst.com.my',
    'malaymail.com',
    'freemalaysiatoday.com',
}

KNOWN_INDONESIA_DOMAINS = {
    'kompas.com',
    'thejakartapost.com',
    'jakartaglobe.id',
    'tempo.co',
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
    if matches_known_domain(domain, KNOWN_FILIPINO_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_FILIPINO_DOMAINS):
        return 'Philippines', f'Known Filipino organization: {domain}'
    if matches_known_domain(domain, KNOWN_INDIAN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_INDIAN_DOMAINS):
        return 'India', f'Known Indian organization: {domain}'
    if matches_known_domain(domain, KNOWN_PAKISTAN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_PAKISTAN_DOMAINS):
        return 'Pakistan', f'Known Pakistani organization: {domain}'
    if matches_known_domain(domain, KNOWN_BANGLADESH_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_BANGLADESH_DOMAINS):
        return 'Bangladesh', f'Known Bangladeshi organization: {domain}'
    if matches_known_domain(domain, KNOWN_SRI_LANKA_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_SRI_LANKA_DOMAINS):
        return 'Sri Lanka', f'Known Sri Lankan organization: {domain}'
    if matches_known_domain(domain, KNOWN_THAILAND_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_THAILAND_DOMAINS):
        return 'Thailand', f'Known Thai organization: {domain}'
    if matches_known_domain(domain, KNOWN_VIETNAM_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_VIETNAM_DOMAINS):
        return 'Vietnam', f'Known Vietnamese organization: {domain}'
    if matches_known_domain(domain, KNOWN_SINGAPORE_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_SINGAPORE_DOMAINS):
        return 'Singapore', f'Known Singaporean organization: {domain}'
    if matches_known_domain(domain, KNOWN_MALAYSIA_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_MALAYSIA_DOMAINS):
        return 'Malaysia', f'Known Malaysian organization: {domain}'
    if matches_known_domain(domain, KNOWN_INDONESIA_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_INDONESIA_DOMAINS):
        return 'Indonesia', f'Known Indonesian organization: {domain}'
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
        '.ph': 'Philippines',
        '.com.ph': 'Philippines',
        '.gov.ph': 'Philippines',
        '.edu.ph': 'Philippines',
        '.org.ph': 'Philippines',
        '.in': 'India',
        '.co.in': 'India',
        '.pk': 'Pakistan',
        '.com.pk': 'Pakistan',
        '.bd': 'Bangladesh',
        '.com.bd': 'Bangladesh',
        '.lk': 'Sri Lanka',
        '.com.lk': 'Sri Lanka',
        '.th': 'Thailand',
        '.co.th': 'Thailand',
        '.vn': 'Vietnam',
        '.com.vn': 'Vietnam',
        '.sg': 'Singapore',
        '.com.sg': 'Singapore',
        '.my': 'Malaysia',
        '.com.my': 'Malaysia',
        '.id': 'Indonesia',
        '.co.id': 'Indonesia',
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
        '.ch': 'Switzerland',
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
        'Philippines': [r'\+63[\s\-]?\d', r'\(\+63\)', r'Tel:\s*\+63'],
        'India': [r'\+91[\s\-]?\d', r'\(\+91\)', r'Tel:\s*\+91'],
        'Pakistan': [r'\+92[\s\-]?\d', r'\(\+92\)', r'Tel:\s*\+92'],
        'Bangladesh': [r'\+880[\s\-]?\d', r'\(\+880\)', r'Tel:\s*\+880'],
        'Sri Lanka': [r'\+94[\s\-]?\d', r'\(\+94\)', r'Tel:\s*\+94'],
        'Thailand': [r'\+66[\s\-]?\d', r'\(\+66\)', r'Tel:\s*\+66'],
        'Vietnam': [r'\+84[\s\-]?\d', r'\(\+84\)', r'Tel:\s*\+84'],
        'Singapore': [r'\+65[\s\-]?\d', r'\(\+65\)', r'Tel:\s*\+65'],
        'Malaysia': [r'\+60[\s\-]?\d', r'\(\+60\)', r'Tel:\s*\+60'],
        'Indonesia': [r'\+62[\s\-]?\d', r'\(\+62\)', r'Tel:\s*\+62'],
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
    """Extract full addresses - must have zip/postal code AND city/state/country."""
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
            'Philippines': r'\b\d{4}\b',
            'India': r'\b\d{6}\b',
            'Dominican Republic': r'\b\d{5}\b',
            'Mexico': r'\b\d{5}\b',
            'Colombia': r'\b\d{6}\b',
            'Argentina': r'\b[A-Z]\d{4}[A-Z]{3}\b',
            'Spain': r'\b\d{5}\b',
            'Germany': r'\b\d{5}\b',
        }

        has_zip = False
        zip_country = None

        location_present = {}
        location_indicators_for_zip = {
            'Philippines': [
                r'\b(?:Manila|Quezon City|Makati|Davao|Cebu|Taguig|Pasig|Caloocan|Zamboanga|Antipolo)\b',
                r'\b(?:Philippines|Philippine)\b'
            ],
            'India': [
                r'\b(?:Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Kolkata|Pune|Ahmedabad)\b',
                r'\bIndia\b'
            ],
            'Pakistan': [
                r'\b(?:Karachi|Lahore|Islamabad|Rawalpindi|Faisalabad|Multan|Peshawar)\b',
                r'\bPakistan\b'
            ],
            'Bangladesh': [
                r'\b(?:Dhaka|Chittagong|Khulna|Rajshahi|Sylhet)\b',
                r'\bBangladesh\b'
            ],
            'Sri Lanka': [
                r'\b(?:Colombo|Kandy|Galle|Jaffna|Negombo)\b',
                r'\b(?:Sri Lanka|Ceylon)\b'
            ],
            'Thailand': [
                r'\b(?:Bangkok|Chiang Mai|Phuket|Pattaya|Krabi)\b',
                r'\bThailand\b'
            ],
            'Vietnam': [
                r'\b(?:Hanoi|Ho Chi Minh City|Da Nang|Hue|Nha Trang)\b',
                r'\b(?:Vietnam|Viet Nam)\b'
            ],
            'Singapore': [
                r'\bSingapore\b'
            ],
            'Malaysia': [
                r'\b(?:Kuala Lumpur|Penang|Johor Bahru|Ipoh|Malacca)\b',
                r'\bMalaysia\b'
            ],
            'Indonesia': [
                r'\b(?:Jakarta|Surabaya|Bandung|Medan|Bali)\b',
                r'\bIndonesia\b'
            ],
            'Germany': [
                r'\b(?:Munich|Berlin|Hamburg|Frankfurt|Cologne|Stuttgart|Düsseldorf|Dusseldorf|München|Iffeldorf|Leipzig|Dortmund|Essen|Dresden|Hannover|Nuremberg)\b',
                r'\b(?:Germany|Deutschland)\b'
            ],
            'US': [
                r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b',
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon|South Dakota|Austin|Sioux Falls)\b',
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b'
            ],
            'UK': [
                r'\b(?:London|Manchester|Birmingham|Edinburgh|Glasgow|Liverpool|Leeds)\b',
                r'\b(?:United Kingdom|UK|U\.K\.)\b'
            ],
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
                elif country in ['Philippines', 'Pakistan', 'Bangladesh', 'Sri Lanka'] and location_present.get(country):
                    has_zip = True
                    zip_country = country
                    break
                elif country in ['India', 'Thailand', 'Singapore', 'Malaysia', 'Indonesia'] and location_present.get(country):
                    has_zip = True
                    zip_country = country
                    break
                elif country == 'Germany' and location_present.get(country):
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
            'Philippines': [
                r'\b(?:Manila|Quezon City|Makati|Davao|Cebu|Taguig|Pasig|Caloocan|Zamboanga|Antipolo)\b',
                r'\b(?:Philippines|Philippine)\b',
            ],
            'India': [
                r'\b(?:Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Kolkata|Pune|Ahmedabad)\b',
                r'\bIndia\b',
            ],
            'Pakistan': [
                r'\b(?:Karachi|Lahore|Islamabad|Rawalpindi|Faisalabad|Multan|Peshawar)\b',
                r'\bPakistan\b',
            ],
            'Bangladesh': [
                r'\b(?:Dhaka|Chittagong|Khulna|Rajshahi|Sylhet)\b',
                r'\bBangladesh\b',
            ],
            'Sri Lanka': [
                r'\b(?:Colombo|Kandy|Galle|Jaffna|Negombo)\b',
                r'\b(?:Sri Lanka|Ceylon)\b',
            ],
            'Thailand': [
                r'\b(?:Bangkok|Chiang Mai|Phuket|Pattaya|Krabi)\b',
                r'\bThailand\b',
            ],
            'Vietnam': [
                r'\b(?:Hanoi|Ho Chi Minh City|Da Nang|Hue|Nha Trang)\b',
                r'\b(?:Vietnam|Viet Nam)\b',
            ],
            'Singapore': [
                r'\bSingapore\b',
            ],
            'Malaysia': [
                r'\b(?:Kuala Lumpur|Penang|Johor Bahru|Ipoh|Malacca)\b',
                r'\bMalaysia\b',
            ],
            'Indonesia': [
                r'\b(?:Jakarta|Surabaya|Bandung|Medan|Bali)\b',
                r'\bIndonesia\b',
            ],
            'US': [
                r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b',
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon|South Dakota|Austin|Sioux Falls)\b',
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b',
            ],
            'UK': [
                r'\b(?:London|Manchester|Birmingham|Edinburgh|Glasgow|Liverpool|Leeds)\b',
                r'\b(?:United Kingdom|UK|U\.K\.)\b',
            ],
            'Germany': [
                r'\b(?:Munich|Berlin|Hamburg|Frankfurt|Cologne|Stuttgart|Düsseldorf|Dusseldorf|München|Iffeldorf|Leipzig|Dortmund|Essen|Dresden|Hannover|Nuremberg)\b',
                r'\b(?:Germany|Deutschland)\b',
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
            # Some Asian countries often use addresses without postal codes
            countries_without_standard_postal = ['Philippines', 'Pakistan', 'Bangladesh', 'Indonesia']

            if location_country_name in countries_without_standard_postal:
                street_indicators = r'\b(?:Block|Town|Ward|District|Street|Avenue|Road|Lane|Barangay|Barrio|Zona|Sector|Jalan|Kampung)\b'
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
    for link in info_links[:6]:
        if fetched_pages >= 3:
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

    # Special handling for multi-word phrases with variations
    if keyword == 'living with in-laws':
        variations = [
            'living with in-laws',
            'living with in laws',
            'live with in-laws',
            'live with in laws',
            'in-laws live',
            'in laws live',
            'cohabit with in-laws',
            'cohabitation with in-laws',
            'cohabitate with in-laws',
            'in-laws living',
            'in laws living',
            'living with your in-laws',
            'living with your in laws',
            'when in-laws live',
            'when in laws live',
        ]
        return any(var in text for var in variations)

    if keyword == 'multigenerational household':
        variations = [
            'multigenerational household',
            'multi-generational household',
            'multigenerational living',
            'multi-generational living',
            'multigenerational home',
            'multi-generational home',
            'multiple generations living',
            'multi generational',
        ]
        return any(var in text for var in variations)

    if keyword == 'extended family living':
        variations = [
            'extended family living',
            'extended family home',
            'extended family household',
            'living with extended family',
            'extended family members living',
        ]
        return any(var in text for var in variations)

    if keyword == 'wedding contributions':
        variations = [
            'wedding contributions',
            'wedding contribution',
            'contribute to wedding',
            'contributing to wedding',
            'family contribution',
            'family contributions to wedding',
        ]
        return any(var in text for var in variations)

    if keyword == 'family contributions':
        variations = [
            'family contributions',
            'family contribution',
            'contribute to family',
            'contributing to family',
            'family financial contribution',
        ]
        return any(var in text for var in variations)

    # Default: exact match
    return keyword in text


def detect_concepts_in_text(text):
    """
    Detect Filipino cultural concepts in text.
    Returns matched keywords grouped by concept, and count of unique concepts found.
    """
    if not text:
        return {}, [], 0

    text_lower = text.lower()
    matched_by_concept = {}
    all_matched_keywords = []

    for concept, keywords in FILIPINO_CULTURAL_CONCEPTS.items():
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


def has_filipino_context(matched_by_concept):
    """Check if Filipino-specific keywords are present."""
    filipino_specific_concepts = ['pamanhikan', 'filipino_tradition',
                                   'barrio', 'barangay', 'utang_na_loob',
                                   'pakikisama', 'hiya', 'kapwa', 'manila', 'quezon_city',
                                   'filipino_grandparents']

    for concept in filipino_specific_concepts:
        if concept in matched_by_concept:
            return True
    return False


def detect_cultural_context(soup, page_text):
    """Detect if the page directly addresses Filipino cultural context using concept-based matching."""
    if not page_text:
        return 'not_related', {}, [], 0

    matched_by_concept, all_matched_keywords, unique_concept_count = detect_concepts_in_text(page_text)
    has_definition_lang, has_advice_lang = detect_language_indicators(page_text)
    has_filipino = has_filipino_context(matched_by_concept)
    has_pamanhikan = 'pamanhikan' in matched_by_concept

    # Category 1: addresses_user_dilemma
    # - 3+ unique concepts (strict requirement)
    if unique_concept_count >= 3:
        category = 'addresses_user_dilemma'

    # Category 2: defines_practice
    # - Has pamanhikan keyword
    # - BUT limited other concepts (1-2 total)
    # - AND has definition language
    elif has_pamanhikan and unique_concept_count <= 2 and has_definition_lang:
        category = 'defines_practice'

    # Category 3: generic_advice
    # - Has in-laws/wedding keywords (living_with_family or family_contributions)
    # - BUT no Filipino-specific keywords
    elif unique_concept_count >= 1 and not has_filipino:
        category = 'generic_advice'

    # Category 4: not_related
    # - 0 concepts matched
    elif unique_concept_count == 0:
        category = 'not_related'

    # Default: if has some Filipino concepts but doesn't fit other categories
    else:
        if has_filipino:
            category = 'defines_practice'  # Default for Filipino content
        else:
            category = 'generic_advice'  # Default for non-Filipino content

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

    # Special handling for known expired domains
    if 'nuptials.ph' in url:
        result['country'] = 'Expired'
        result['status'] = 'expired_server'
        result['evidence'].append('Known expired server (nuptials.ph)')
        return result

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


def analyze_urls(urls, urls_by_turn, first_conversation, output_file='filipino_url_analyzer_results.json'):
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
        print(f"  Generic advice (no Filipino context): {generic_advice_count} ({pct:.1f}%)")
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

    priority_countries = ['US', 'Philippines', 'India', 'Pakistan', 'Bangladesh', 'Sri Lanka',
                          'Thailand', 'Vietnam', 'Singapore', 'Malaysia', 'Indonesia',
                          'UK', 'Switzerland', 'Netherlands', 'Germany', 'France', 'Canada']

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
    """Main function - Filipino therapy demo URLs."""
    therapy_urls = [
        "https://zolanaweddings.com/2024/12/11/expert-tips-for-managing-family-dynamics/?utm_source=openai",
        "https://themarigoldcompany.com/navigating-family-dynamics-during-wedding-planning/?utm_source=openai",
        "https://www.augmentedartsweddings.com.au/blog/how-to-deal-with-family-dynamics-expectations-and-traditions-on-your-wedding-day/?utm_source=openai",
        "https://travelwithkarla.com/2025/10/10/the-ultimate-modern-pamamanhikan-guide-how-to-plan-a-meaningful-family-gathering/?utm_source=openai",
        "https://www.newsbytesapp.com/news/lifestyle/unique-filipino-wedding-traditions-strengthen-family-ties/story?utm_source=openai",
        "https://www.sfcsbc.com/pamamanhikan-the-heart-of-parental-respect-in-the-philippine-marriage/?utm_source=openai",
        "https://www.marriagehint.com/living-with-in-laws/?utm_source=openai",
        "https://www.indiatoday.in/lifestyle/society/story/should-newlyweds-live-on-their-own-for-a-few-years-instead-of-with-in-laws-2590116-2024-08-30/?utm_source=openai",
        "https://www.bonobology.com/pros-cons-living-laws/?utm_source=openai",
        "https://www.letsmakeaplan.org/financial-topics/articles/family-finances/three-essential-financial-considerations-for-new-parents?utm_source=openai",
        "https://www.letsmakeaplan.org/financial-topics/articles/family-finances/financial-and-budget-considerations-for-starting-a-family?utm_source=openai",
        "https://goodmenproject.com/featured-content/7-financial-considerations-for-having-children/?utm_source=openai",
    ]

    print("Filipino Cultural Context URL Analyzer")
    print("=" * 80)
    print(f"\nAnalyzing {len(therapy_urls)} URLs...")
    print()

    results = analyze_urls(therapy_urls, output_file='filipino_url_analyzer_results.json')

    return results


if __name__ == "__main__":
    main()
