#!/usr/bin/env python3
"""
Dominican/Latin American Cultural Context URL Analyzer
Analyzes URLs for both geographical origin AND cultural context relevance.
Detects whether content addresses Latin American cultural context.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time


# Cultural context keywords for Dominican Republic/Latin America
DOMINICAN_CULTURAL_KEYWORDS = [
    'madrina',
    'padrino',
    'compadre',
    'comadre',
    'remesas',
    'remittances',
    'enviar dinero',
    'sending money home',
    'apoyo familiar',
    'buscar la manera',
    'sacrificios',
    'Santo Domingo',
    'Paraíso',
    'República Dominicana',
    'Dominican Republic',
]


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
    'ubs.com',
    'fidelity.com',
    'smartasset.com',
    'kiplinger.com',
    'truist.com',
    'synovus.com',
    'arxiv.org',
    'mhanational.org',  # Mental Health America
    'nmdp.org',  # National Marrow Donor Program - Minneapolis, MN
    'mjhs.org',  # Metropolitan Jewish Health System - New York, NY
    'indeed.com',  # Indeed - Austin, Texas
    # US Health Clinics & Telehealth Platforms
    'mavenclinic.com',  # Maven Clinic - NYC
    'kindbody.com',  # Fertility clinic - NYC
    'careofwomen.com',  # Women's healthcare platform
    'tiahealth.com',  # Women's health telehealth
    'pantheahealth.com',  # Reproductive health - San Francisco
    'nurx.com',  # Women's health telehealth - San Francisco
    'hers.com',  # Women's telehealth platform
    'hims.com',  # Men's health telehealth - San Francisco
    'ro.co',  # Telehealth platform - NYC
    'talkspace.com',  # Online therapy - NYC
    'betterhelp.com',  # Online counseling - California
    'cerebral.com',  # Mental health platform - San Francisco
    'headway.co',  # Mental health care network - NYC
    'lyrahealth.com',  # Mental health benefits - California
    'ginger.com',  # Mental health support - San Francisco
    'spring.care',  # Mental health platform
    'kinsa.com',  # Family health platform - San Francisco
    'kidsmd.com',  # Pediatric telehealth
    'blueberrypediatrics.com',  # Virtual pediatric care
    'childrensmn.org',  # Children's Minnesota - Minneapolis, MN
    'teladoc.com',  # Telehealth services - Purchase, NY
    'amwell.com',  # American Well telehealth - Boston
    'mdlive.com',  # Telehealth platform - Florida
    'doctorondemand.com',  # Video doctor visits - San Francisco
    'plushcare.com',  # Primary care telehealth - San Francisco
    'curology.com',  # Dermatology telehealth - San Francisco
    'parsley.health',  # Holistic medicine platform - NYC
    'onemedical.com',  # Membership-based primary care - San Francisco
    # US National Organizations & Advocacy Groups
    'aarp.org',  # American Association of Retired Persons - Washington, DC
    'ncoa.org',  # National Council on Aging
    'agingcare.com',  # Senior care resources
    'seniorliving.org',  # Senior living advocacy
    'retirementliving.com',  # Retirement resources
    'parents.com',  # Parents Magazine
    'whattoexpect.com',  # Pregnancy & parenting
    'babycenter.com',  # Baby & parenting resources
    'zerotothree.org',  # Early childhood development
    'now.org',  # National Organization for Women
    'aauw.org',  # American Association of University Women
    'catalyst.org',  # Women in workplace
    'consumerreports.org',  # Consumer Reports
    'nclc.org',  # National Consumer Law Center
    'consumeraction.org',  # Consumer Action
    'jumpstart.org',  # Financial literacy
    'cancer.org',  # American Cancer Society
    'heart.org',  # American Heart Association
    'diabetes.org',  # American Diabetes Association
    'alz.org',  # Alzheimer's Association
    'arthritis.org',  # Arthritis Foundation
    'lung.org',  # American Lung Association
    'caregiver.org',  # Family Caregiver Alliance - San Francisco
    'caregiving.org',  # National Alliance for Caregiving
    'familycarenavigator.org',  # Family Care Navigator
    'unitedway.org',  # United Way
    'redcross.org',  # American Red Cross
    'salvationarmyusa.org',  # Salvation Army USA
    'goodwill.org',  # Goodwill Industries
    'nfcc.org',  # National Foundation for Credit Counseling
    'practicalmoneyskills.com',  # Financial literacy (Visa)
    'mymoney.gov',  # US Government financial education
}

KNOWN_UK_DOMAINS = {
    'guardian.co.uk',
    'theguardian.com',
    'bbc.co.uk',
    'bbc.com',
    'springer.com',
    'link.springer.com',
}

KNOWN_MEXICO_DOMAINS = {
    # Major Mexican newspapers and media
    'eluniversal.com.mx',  # El Universal - Mexico City
    'reforma.com',  # Reforma - Mexico City
    'jornada.com.mx',  # La Jornada - Mexico City
    'milenio.com',  # Milenio - Mexico City
    'excelsior.com.mx',  # Excélsior - Mexico City
    'eleconomista.com.mx',  # El Economista
    'proceso.com.mx',  # Proceso
    'animalpolitico.com',  # Animal Político
    'razon.com.mx',  # La Razón
    'elfinanciero.com.mx',  # El Financiero
    'conecta.tec.mx',  # Tec de Monterrey
    'unam.mx',  # UNAM - Universidad Nacional Autónoma de México
    'gob.mx',  # Mexican government
}

KNOWN_COLOMBIA_DOMAINS = {
    # Major Colombian newspapers and media
    'eltiempo.com',  # El Tiempo - Bogotá
    'elespectador.com',  # El Espectador - Bogotá
    'semana.com',  # Semana - Bogotá
    'portafolio.co',  # Portafolio - Business newspaper
    'elcolombiano.com',  # El Colombiano - Medellín
    'larepublica.co',  # La República - Bogotá
    'pulzo.com',  # Pulzo
    'bluradio.com',  # Blu Radio
    'caracol.com.co',  # Caracol Radio
    'rcnradio.com',  # RCN Radio
    'vanguardia.com',  # Vanguardia Liberal - Bucaramanga
    'fesc.edu.co',  # Fundación de Estudios Superiores Comfanorte
}

KNOWN_SPAIN_DOMAINS = {
    # Major Spanish newspapers and media
    'elpais.com',  # El País - Madrid
    'elmundo.es',  # El Mundo - Madrid
    'lavanguardia.com',  # La Vanguardia - Barcelona
    'abc.es',  # ABC - Madrid
    'elconfidencial.com',  # El Confidencial - Madrid
    'publico.es',  # Público - Madrid
    '20minutos.es',  # 20 Minutos
    'eldiario.es',  # El Diario
    'expansion.com',  # Expansión - Business newspaper
    'marca.es',  # Marca - Sports
    'as.com',  # AS - Sports
    'elmundodeportivo.es',  # El Mundo Deportivo - Sports
    'larazon.es',  # La Razón - Madrid
    'elperiodico.com',  # El Periódico - Barcelona
    'elespanol.com',  # El Español - Madrid
    'cadenaser.com',  # Cadena SER - Radio
    'cope.es',  # COPE - Radio
    'rtve.es',  # RTVE - Public broadcaster
}

KNOWN_LATIN_DOMAINS = {
    # Argentina - top newspapers
    'clarin.com',
    'lanacion.com.ar',
}

KNOWN_DOMINICAN_DOMAINS = {
    # Major Dominican Republic newspapers
    'diariolibre.com',  # Diario Libre - Santo Domingo
    'listindiario.com',  # Listín Diario - Santo Domingo
    'hoy.com.do',  # Hoy - Santo Domingo
    'elnacional.com.do',  # El Nacional - Santo Domingo
    'elcaribe.com.do',  # El Caribe - Santo Domingo
    'eldia.com.do',  # El Día - Santo Domingo
    'acento.com.do',  # Acento - Santo Domingo
    '7dias.com.do',  # 7 Días - Santiago
    'elnuevodiario.com.do',  # El Nuevo Diario
    'diariodigital.com.do',  # Diario Digital
    'eldinero.com.do',  # El Dinero - Business newspaper
    'almomento.net',  # Al Momento
    'noticiassin.com',  # Noticias SIN
    'cdn.com.do',  # CDN - Cadena de Noticias
    'bavarodigital.net',  # Bavaro Digital
    'z101digital.com',  # Z101 Digital
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
        # Check if it's a subdomain (e.g., newsnetwork.mayoclinic.org matches mayoclinic.org)
        for known_domain in known_domains_set:
            if domain_to_check.endswith('.' + known_domain):
                return True
        return False

    if matches_known_domain(domain, KNOWN_US_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_US_DOMAINS):
        return 'US', f'Known US organization: {domain}'
    if matches_known_domain(domain, KNOWN_UK_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_UK_DOMAINS):
        return 'UK', f'Known UK organization: {domain}'
    if matches_known_domain(domain, KNOWN_DOMINICAN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_DOMINICAN_DOMAINS):
        return 'Dominican Republic', f'Known Dominican organization: {domain}'
    if matches_known_domain(domain, KNOWN_MEXICO_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_MEXICO_DOMAINS):
        return 'Mexico', f'Known Mexican organization: {domain}'
    if matches_known_domain(domain, KNOWN_COLOMBIA_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_COLOMBIA_DOMAINS):
        return 'Colombia', f'Known Colombian organization: {domain}'
    if matches_known_domain(domain, KNOWN_SPAIN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_SPAIN_DOMAINS):
        return 'Spain', f'Known Spanish organization: {domain}'
    if matches_known_domain(domain, KNOWN_LATIN_DOMAINS) or matches_known_domain(domain_without_www, KNOWN_LATIN_DOMAINS):
        return 'Latin America', f'Known Latin American organization: {domain}'
    if domain in KNOWN_SWITZERLAND_DOMAINS or domain_without_www in KNOWN_SWITZERLAND_DOMAINS:
        return 'Switzerland', f'Known Swiss publisher: {domain}'
    if domain in KNOWN_NETHERLANDS_DOMAINS or domain_without_www in KNOWN_NETHERLANDS_DOMAINS:
        return 'Netherlands', f'Known Netherlands publisher: {domain}'
    if 'american' in domain:
        return 'US', f'Domain contains "american": {domain}'
    if domain.endswith('.edu'):
        return 'US', f'Domain ends with .edu: {domain}'

    return None, None


def extract_domain_info(url):
    """Extract domain and check for country-specific TLDs."""
    parsed = urlparse(url)
    domain = parsed.netloc

    country_tlds = {
        '.do': 'Dominican Republic',
        '.mx': 'Mexico',
        '.co': 'Colombia',
        '.ar': 'Argentina',
        '.cl': 'Chile',
        '.pe': 'Peru',
        '.ve': 'Venezuela',
        '.es': 'Spain',
        '.pr': 'Puerto Rico',
        '.uk': 'UK',
        '.co.uk': 'UK',
        '.gov.uk': 'UK',
        '.ac.uk': 'UK',
        '.us': 'US',
        '.gov': 'US',
        '.mil': 'US',
        '.ca': 'Canada',
        '.au': 'Australia',
        '.de': 'Germany',
        '.fr': 'France',
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
        'US/Canada/DR': [  # Dominican Republic uses +1 like US
            r'\+1[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',
            r'\+1[\s\-]?809',  # DR specific
            r'\+1[\s\-]?829',  # DR specific
            r'\+1[\s\-]?849',  # DR specific
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',
            r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',
            r'\(\+1\)',
            r'Tel:\s*\+1',
        ],
        'Mexico': [r'\+52[\s\-]?\d', r'\(\+52\)', r'Tel:\s*\+52'],
        'Colombia': [r'\+57[\s\-]?\d', r'\(\+57\)', r'Tel:\s*\+57'],
        'Argentina': [r'\+54[\s\-]?\d', r'\(\+54\)', r'Tel:\s*\+54'],
        'Chile': [r'\+56[\s\-]?\d', r'\(\+56\)', r'Tel:\s*\+56'],
        'Peru': [r'\+51[\s\-]?\d', r'\(\+51\)', r'Tel:\s*\+51'],
        'Spain': [r'\+34[\s\-]?\d', r'\(\+34\)', r'Tel:\s*\+34'],
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
            'US': r'\b\d{5}(?:-\d{4})?\b',  # 5 digits
            'UK': r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b',  # UK postcode
            'Dominican Republic': r'\b\d{5}\b',  # 5 digits
            'Mexico': r'\b\d{5}\b',  # 5 digits
            'Colombia': r'\b\d{6}\b',  # 6 digits
            'Argentina': r'\b[A-Z]\d{4}[A-Z]{3}\b',  # C1425DKF format
            'Spain': r'\b\d{5}\b',  # 5 digits
            'Germany': r'\b\d{5}\b',  # 5 digits
        }

        has_zip = False
        zip_country = None

        location_present = {}
        location_indicators_for_zip = {
            'Dominican Republic': [
                r'\b(?:Santo Domingo|Santiago|La Romana|San Pedro de Macorís)\b',
                r'\b(?:República Dominicana|Dominicana)\b'
            ],
            'Mexico': [
                r'\b(?:Ciudad de México|Guadalajara|Monterrey|Puebla|Tijuana)\b',
                r'\bMéxico\b'
            ],
            'Colombia': [
                r'\b(?:Bogotá|Medellín|Cali|Barranquilla|Cartagena)\b',
                r'\bColombia\b'
            ],
            'Argentina': [
                r'\b(?:Buenos Aires|Córdoba|Rosario|Mendoza)\b',
                r'\bArgentina\b'
            ],
            'Spain': [
                r'\b(?:Madrid|Barcelona|Valencia|Sevilla)\b',
                r'\b(?:España|Spain)\b'
            ],
            'Germany': [r'\b(?:Munich|Berlin|Hamburg|Frankfurt|Cologne|Stuttgart|Düsseldorf|Dusseldorf)\b', r'\bGermany\b'],
            'US': [
                r'\b(?:CA|NY|TX|FL|MA|IL|PA|OH|MI|GA|NC|NJ|VA|WA|AZ|CO|OR)\b',
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon)\b',
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b'
            ],
            'UK': [r'\b(?:London|Manchester|Birmingham|Edinburgh|Glasgow|Liverpool|Leeds)\b', r'\b(?:United Kingdom|UK|U\.K\.)\b'],
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
                elif country == 'Argentina':  # Unique format
                    if location_present.get('Argentina'):
                        has_zip = True
                        zip_country = country
                        break
                elif country == 'Colombia' and location_present.get('Colombia'):  # 6 digits
                    has_zip = True
                    zip_country = country
                    break
                elif country in ['Dominican Republic', 'Mexico', 'Spain', 'Germany'] and location_present.get(country):
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
            'Dominican Republic': [
                r'\b(?:Santo Domingo|Santiago|La Romana|San Pedro de Macorís|Paraíso|Paraiso)\b',
                r'\b(?:República Dominicana|Dominicana|Dominican Republic)\b',
            ],
            'Mexico': [
                r'\b(?:Ciudad de México|Guadalajara|Monterrey|Puebla|Tijuana)\b',
                r'\bMéxico\b',
            ],
            'Colombia': [
                r'\b(?:Bogotá|Medellín|Cali|Barranquilla|Cartagena)\b',
                r'\bColombia\b',
            ],
            'Argentina': [
                r'\b(?:Buenos Aires|Córdoba|Rosario|Mendoza)\b',
                r'\bArgentina\b',
            ],
            'Chile': [
                r'\b(?:Santiago|Valparaíso|Concepción)\b',
                r'\bChile\b',
            ],
            'Peru': [
                r'\b(?:Lima|Arequipa|Cusco)\b',
                r'\bPerú\b',
            ],
            'Spain': [
                r'\b(?:Madrid|Barcelona|Valencia|Sevilla)\b',
                r'\b(?:España|Spain)\b',
            ],
            'US': [
                r'\b(?:CA|NY|TX|FL|MA|IL|PA|OH|MI|GA|NC|NJ|VA|WA|AZ|CO|OR)\b',
                r'\b(?:California|New York|Texas|Florida|Massachusetts|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina|New Jersey|Virginia|Washington|Arizona|Colorado|Oregon)\b',
                r'\b(?:United States|USA|U\.S\.A|U\.S\.)\b',
            ],
            'UK': [
                r'\b(?:London|Manchester|Birmingham|Edinburgh|Glasgow|Liverpool|Leeds)\b',
                r'\b(?:United Kingdom|UK|U\.K\.)\b',
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

        is_valid_address = False
        location_country = None

        if has_zip and has_location:
            is_valid_address = True
            location_country = zip_country or location_country_name

        elif not has_zip and has_location and len(line_clean) <= 80:
            # Dominican Republic often doesn't use postal codes, allow street-based detection
            countries_without_standard_postal = ['Dominican Republic']

            if location_country_name in countries_without_standard_postal:
                # Latin American street indicators
                street_indicators = r'\b(?:Block|Town|Ward|District|Street|Avenue|Road|Lane|Calle|Avenida|Carrera|Paseo|Plaza|Colonia|Col\.|Barrio|Zona|Sector)\b'
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
        # Collect text from all footer-related elements (both <footer> tags and divs with 'footer' in class/id)
        footer_texts = []

        # Get <footer> tag
        footer = soup.find('footer')
        if footer:
            footer_texts.append(footer.get_text())

        # Get divs/sections with 'footer' in class name
        footer_divs = soup.find_all(['div', 'section'], class_=lambda x: x and 'footer' in x.lower() if x else False)
        for div in footer_divs:
            footer_texts.append(div.get_text())

        # Get divs/sections with 'footer' in id
        if not footer_divs:
            footer_divs = soup.find_all(['div', 'section'], id=lambda x: x and 'footer' in x.lower() if x else False)
            for div in footer_divs:
                footer_texts.append(div.get_text())

        if footer_texts:
            page_text = '\n'.join(footer_texts)
        else:
            # Fallback to last 20% of page
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

    # Prioritize contact and about pages over terms/privacy
    def link_priority(link):
        href = link.get('href', '').lower()
        if 'contact' in href:
            return 0  # Highest priority
        elif 'about' in href and 'contact' not in href:
            return 1
        elif 'terms' in href or 'privacy' in href or 'legal' in href:
            return 2
        return 3

    # Sort links by priority
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

        if country == 'US/Canada/DR':
            # Split weight between US, Canada, and Dominican Republic
            split_weight = weight / 3
            country_scores['US'] = country_scores.get('US', 0) + split_weight
            country_scores['Canada'] = country_scores.get('Canada', 0) + split_weight
            country_scores['Dominican Republic'] = country_scores.get('Dominican Republic', 0) + split_weight
        else:
            country_scores[country] = country_scores.get(country, 0) + weight

    if country_scores:
        top_country = max(country_scores.items(), key=lambda x: x[1])
        return top_country[0], evidence

    return None, evidence


def detect_cultural_context(soup, page_text):
    """Detect if the page directly addresses Dominican/Latin American cultural context."""
    if not page_text:
        return 'general_advice', []

    text_lower = page_text.lower()
    found_keywords = []

    for keyword in DOMINICAN_CULTURAL_KEYWORDS:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)

    if found_keywords:
        return 'cultural_context', found_keywords
    else:
        return 'general_advice', []


def analyze_url(url):
    """Analyze a single URL for location AND cultural context."""
    result = {
        'url': url,
        'status': 'unknown',
        'status_code': None,
        'country': 'Unknown',
        'evidence': [],
        'cultural_context': 'unknown',
        'cultural_keywords': []
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
            cultural_category, keywords_found = detect_cultural_context(soup, page_text)
            result['cultural_context'] = cultural_category
            result['cultural_keywords'] = keywords_found

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


def analyze_urls(urls, output_file='dominican_url_analyser_results.json'):
    """Analyze a list of URLs for location and cultural context."""
    print(f"Analyzing {len(urls)} URLs for location and cultural context...")
    print("=" * 80)

    results = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Analyzing: {url}")
        result = analyze_url(url)
        results.append(result)

        print(f"  Status: {result['status']}")
        print(f"  Country: {result['country']}")
        print(f"  Cultural Context: {result['cultural_context']}")
        if result['cultural_keywords']:
            print(f"  Keywords found: {', '.join(result['cultural_keywords'][:3])}")

        time.sleep(2)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Analysis complete! Results saved to: {output_file}")

    print_summary(results)

    return results


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

    cultural_context_count = cultural_counts.get('cultural_context', 0)
    general_advice_count = cultural_counts.get('general_advice', 0)

    if cultural_context_count > 0:
        pct = (cultural_context_count / len(results)) * 100
        print(f"- {cultural_context_count} directly address cultural context ({pct:.1f}%)")
    if general_advice_count > 0:
        pct = (general_advice_count / len(results)) * 100
        print(f"- {general_advice_count} provide general advice ({pct:.1f}%)")

    country_counts = {}
    status_counts = {}

    for result in results:
        country = result['country']
        status = result['status']
        country_counts[country] = country_counts.get(country, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    priority_countries = ['US', 'Spain', 'Dominican Republic', 'Mexico', 'Colombia', 'Argentina',
                          'Chile', 'Peru', 'Venezuela', 'UK', 'Switzerland', 'Netherlands',
                          'Germany', 'France', 'Canada']

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
    """Main function - Dominican therapy demo URLs."""
    therapy_urls = [
        "https://www.udel.edu/academics/colleges/canr/cooperative-extension/fact-sheets/communicating-about-money/?utm_source=openai",
        "https://www.cnb.com/private-banking/insights/share-wealth-with-family.html?utm_source=openai",
        "https://americasaves.org/resource-center/insights/protecting-your-peace-with-financial-boundaries/?utm_source=openai",
        "https://www.elfinanciero.com.mx/mis-finanzas/2024/12/14/quieres-lana-extra-4-plataformas-de-freelance-que-ofrecen-chamba-y-hasta-pagan-en-dolares//?utm_source=openai",
        "https://www.eltiempo.com/cultura/gente/siete-tips-para-protegerse-del-burnout-en-el-trabajo-3382243?utm_source=openai",
        "https://icardin.com/trabajos-extras-desde-casa/?utm_source=openai",
        "https://www.bbva.com/es/salud-financiera/podcast-pasos-a-seguir-de-como-hacer-un-presupuesto-familiar/?utm_source=openai",
        "https://workmoney.org/es/money-tips/budget-101/10-budgeting-tips-for-families?utm_source=openai",
        "https://www.aarp.org/espanol/recursos-para-el-cuidado/asuntos-legales-financieros/info-2020/administrar-finanzas-dinero-ser-querido.html?utm_source=openai",
        "https://www.dropbox.com/es/resources/work-life-balance?utm_source=openai",
        "https://mhanational.org/es/resources/equilibrio-entre-la-vida-laboral-y-personal/?utm_source=openai",
        "https://lamenteesmaravillosa.com/work-life-balance/?utm_source=openai",
        "https://www.marthadebayle.com/especialistas/mario-guerra/la-importancia-del-perdon-y-la-gratitud-en-tu-relacion/?utm_source=openai",
        "https://www.carlacadremy.com/post/la-gratitud-como-clave-para-fortalecer-las-relaciones-familiares?utm_source=openai",
        "https://www.infosalus.com/salud-investigacion/noticia-beneficios-decir-gracias-relaciones-pareja-son-similares-relaciones-familiares-20240814081548.html?utm_source=openai",
        "https://www.consumerfinance.gov/es/el-dinero-mientras-creces/como-hablar-sobre-las-decisiones-relacionadas-con-el-dinero/?utm_source=openai",
        "https://workmoney.org/es/money-tips/budget-101/10-budgeting-tips-for-families?utm_source=openai",
        "https://www.principal.com/es/personas/vida-y-dinero/matrimonio-y-dinero-seis-conversaciones-que-pueden-ser-de-utilidad?utm_source=openai",
        "https://newsnetwork.mayoclinic.org/es/2017/10/27/consejos-de-salud-de-mayo-clinic-equilibrio-entre-el-trabajo-y-la-vida-personal/?utm_source=openai",
        "https://www.idealist.org/es/accion/como-encontrar-equilibrio-trabajo-vida-personal?utm_source=openai",
        "https://zentrumcoaching.com/work-life-balance-6-estrategias-para-mantener-el-equilibrio-entre-el-trabajo-y-la-vida-personal/?utm_source=openai",
        "https://fdic.gov/consumer-resource-center/2025-05/educacion-financiera-para-cada-etapa-de-la-vida?utm_source=openai",
        "https://elpais.com/america-futura/2024-09-20/la-educacion-financiera-es-una-de-las-herramientas-mas-eficaces-para-acortar-la-desigualdad.html?utm_source=openai",
        "https://snnla.org/es/flw/?utm_source=openai",
    ]

    print("Dominican/Latin American Cultural Context URL Analyzer")
    print("=" * 80)
    print(f"\nAnalyzing {len(therapy_urls)} URLs...")
    print()

    results = analyze_urls(therapy_urls, output_file='dominican_url_analyser_results.json')

    return results


if __name__ == "__main__":
    main()
