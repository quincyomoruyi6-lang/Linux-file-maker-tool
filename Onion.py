#!/usr/bin/env python3
"""
Dark Web Scraper – Python‑only, uses Tor for anonymity.

DISCLAIMER:
- Use this ONLY for authorised security research and threat intelligence.
- Ensure your activities are legal in your jurisdiction.
- Do NOT access illegal content. The author assumes no liability.
- Always respect robots.txt and site terms of service.
"""

import sys
import time
import logging
import argparse
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
from stem.connection import connect


# ======================== CONFIGURATION ========================

TOR_SOCKS = 'socks5h://127.0.0.1:9050'
TOR_CONTROL_PORT = 9051
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
TIMEOUT = 30
LOG_LEVEL = logging.INFO


# ======================== LOGGING SETUP ========================

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('dark_scraper')


# ======================== TOR CONTROL FUNCTIONS ========================

def check_tor():
    """Verify that Tor SOCKS proxy is reachable."""
    try:
        r = requests.get('https://check.torproject.org/api/ip',
                         proxies={'http': TOR_SOCKS, 'https': TOR_SOCKS},
                         timeout=10)
        if r.json().get('IsTor'):
            logger.info('Tor is active – IP: %s', r.json().get('IP'))
            return True
        else:
            logger.error('Tor is not running – check your Tor service.')
            return False
    except Exception as e:
        logger.error('Cannot connect to Tor: %s', e)
        return False


def renew_tor_ip():
    """Request a new exit node from Tor (newnym signal)."""
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            logger.info('Tor IP renewed successfully.')
    except Exception as e:
        logger.error('Failed to renew Tor IP: %s', e)
        raise


# ======================== REQUEST SESSION WITH RETRIES ========================

def get_tor_session():
    """Create a requests.Session that routes through Tor with retries."""
    session = requests.Session()
    session.proxies = {'http': TOR_SOCKS, 'https': TOR_SOCKS}
    session.headers.update({'User-Agent': USER_AGENT})

    # Retry strategy for transient failures
    retry_strategy = Retry(
        total=MAX_RETRIES,
        read=MAX_RETRIES,
        connect=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET']
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


# ======================== FETCH AND PARSE ========================

def fetch_page(url, session, renew_ip=False):
    """
    Fetch a single .onion page.

    Args:
        url (str): The .onion URL to fetch.
        session (requests.Session): Session with Tor proxy.
        renew_ip (bool): Whether to request a new Tor circuit before fetch.

    Returns:
        BeautifulSoup object or None if failed.
    """
    if renew_ip:
        renew_tor_ip()
        time.sleep(2)  # Allow circuit to settle

    try:
        logger.info('Fetching: %s', url)
        resp = session.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        # Some .onion sites return weird encodings; fallback to utf-8
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        logger.info('Fetched %d bytes', len(resp.content))
        return soup
    except requests.exceptions.Timeout:
        logger.error('Timeout fetching %s', url)
    except requests.exceptions.HTTPError as e:
        logger.error('HTTP error %s: %s', url, e)
    except Exception as e:
        logger.error('Error fetching %s: %s', url, e)
    return None


def extract_links(soup, base_url):
    """Extract all href links from a BeautifulSoup object."""
    links = set()
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        # Skip empty, javascript, mailto, etc.
        if not href or href.startswith(('javascript:', 'mailto:', '#')):
            continue
        full_url = urljoin(base_url, href)
        # Only keep .onion links (optional: also keep same domain)
        if '.onion' in full_url:
            links.add(full_url)
    return links


# ======================== SIMPLE CRAWLER ========================

def crawl(start_url, max_depth=1, max_pages=20, renew_interval=5):
    """
    Recursively crawl .onion sites up to a given depth.

    Args:
        start_url (str): Starting .onion URL.
        max_depth (int): How many levels to follow.
        max_pages (int): Maximum total pages to fetch.
        renew_interval (int): Renew IP every N pages.

    Returns:
        dict: {url: {'title': ..., 'links': [...], 'text': ...}}
    """
    if not check_tor():
        logger.error('Tor is not available. Exiting.')
        sys.exit(1)

    session = get_tor_session()
    visited = set()
    to_visit = [(start_url, 0)]  # (url, depth)
    results = {}
    page_count = 0

    while to_visit and page_count < max_pages:
        url, depth = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        # Renew IP every 'renew_interval' pages for anonymity
        renew = (page_count % renew_interval == 0) and page_count > 0
        soup = fetch_page(url, session, renew_ip=renew)

        if not soup:
            continue

        # Store basic data
        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        links = extract_links(soup, url)
        results[url] = {
            'title': title,
            'links': list(links),
            'text': soup.get_text(separator=' ', strip=True)[:500]  # preview
        }
        logger.info('Page %d: %s – %s', page_count+1, title[:50], url)
        page_count += 1

        # Add new links to queue (only if within depth)
        if depth < max_depth:
            for link in links:
                if link not in visited and link not in [u for u, _ in to_visit]:
                    to_visit.append((link, depth + 1))

        # Polite delay between requests
        time.sleep(1)

    logger.info('Crawling finished. Visited %d pages.', len(visited))
    return results


# ======================== COMMAND‑LINE INTERFACE ========================

def main():
    parser = argparse.ArgumentParser(
        description='Crawl .onion sites over Tor.',
        epilog='Example: python dark_crawler.py http://protonmailrmez3lotccipshtkleegetolb73fuirgp7rfuxlyz3qs.onion/ -d 2 -p 10'
    )
    parser.add_argument('url', help='Starting .onion URL')
    parser.add_argument('-d', '--depth', type=int, default=1,
                        help='Maximum crawl depth (default: 1)')
    parser.add_argument('-p', '--pages', type=int, default=20,
                        help='Maximum pages to fetch (default: 20)')
    parser.add_argument('-r', '--renew', type=int, default=5,
                        help='Renew Tor IP every N pages (default: 5)')
    parser.add_argument('-o', '--output', help='Save results to a text file')
    args = parser.parse_args()

    # Validate URL has .onion
    if '.onion' not in args.url:
        logger.warning('URL does not contain .onion – are you sure?')

    logger.info('Starting crawl: %s (depth=%d, max_pages=%d)',
                args.url, args.depth, args.pages)

    results = crawl(args.url, args.depth, args.pages, args.renew)

    # Print summary
    print('\n' + '='*60)
    print(f'Crawled {len(results)} pages:')
    for url, data in results.items():
        print(f'  {url} – {data["title"]}')
        if data['links']:
            print(f'    Links: {len(data["links"])} found')
    print('='*60)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            for url, data in results.items():
                f.write(f'URL: {url}\n')
                f.write(f'Title: {data["title"]}\n')
                f.write(f'Links: {", ".join(data["links"][:10])}\n')
                f.write(f'Preview: {data["text"]}\n')
                f.write('-'*60 + '\n')
        logger.info('Results saved to %s', args.output)


if __name__ == '__main__':
    main()
