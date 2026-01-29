"""
Download and update all sitemap data from Grokipedia.

This script uses multiple HTTP methods to ensure compatibility
with different network configurations (proxies, firewalls, etc.)

Usage:
    python scripts/download_sitemaps.py [--start N] [--end N] [--dry-run]
"""

import argparse
import os
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request, ProxyHandler, build_opener, install_opener
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET

# Bypass any proxy settings by installing a no-proxy handler
proxy_handler = ProxyHandler({})
opener = build_opener(proxy_handler)
install_opener(opener)

# Constants
SITEMAP_INDEX_URL = "https://assets.grokipedia.com/sitemap/sitemap-index.xml"
SITEMAP_BASE_URL = "https://assets.grokipedia.com/sitemap/sitemap-{:05d}.xml"
USER_AGENT = "GrokipediaSDK/1.0 (Python; +https://github.com/AppleLamps/grokipedia-sdk)"
RATE_LIMIT_DELAY = 0.3  # seconds between requests
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2.0

# XML namespaces
NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download and update Grokipedia sitemap data"
    )
    parser.add_argument('--start', type=int, default=1, help='Start from sitemap N')
    parser.add_argument('--end', type=int, default=None, help='End at sitemap N')
    parser.add_argument('--dry-run', action='store_true', help='Preview without changes')
    parser.add_argument('--force', action='store_true', help='Force update all')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL verification')
    return parser.parse_args()


def get_links_dir() -> Path:
    """Get the links directory path."""
    script_dir = Path(__file__).parent
    sdk_dir = script_dir.parent
    links_dir = sdk_dir / "grokipedia_sdk" / "links"
    
    if not links_dir.exists():
        print(f"Creating links directory: {links_dir}")
        links_dir.mkdir(parents=True, exist_ok=True)
    
    return links_dir


def fetch_url(url: str, ssl_verify: bool = True) -> Optional[str]:
    """Fetch URL content using urllib (built-in, uses system proxy)."""
    headers = {'User-Agent': USER_AGENT}
    request = Request(url, headers=headers)
    
    # SSL context
    if ssl_verify:
        context = ssl.create_default_context()
    else:
        context = ssl._create_unverified_context()
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            with urlopen(request, timeout=30, context=context) as response:
                return response.read().decode('utf-8')
        except HTTPError as e:
            print(f"  HTTP Error {e.code}: {e.reason}")
            if e.code == 404:
                return None
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except URLError as e:
            print(f"  URL Error: {e.reason}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            print(f"  Error: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    
    return None


def fetch_sitemap_index(ssl_verify: bool = True) -> List[Tuple[int, str]]:
    """Fetch and parse the sitemap index."""
    print(f"Fetching sitemap index...")
    print(f"URL: {SITEMAP_INDEX_URL}")
    
    content = fetch_url(SITEMAP_INDEX_URL, ssl_verify)
    if not content:
        print("Failed to fetch sitemap index")
        return []
    
    # Parse XML
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"XML Parse error: {e}")
        return []
    
    sitemaps = []
    for sitemap in root.findall('sm:sitemap', NS):
        loc = sitemap.find('sm:loc', NS)
        if loc is not None:
            url = loc.text
            # Extract sitemap number
            match = re.search(r'sitemap-(\d+)\.xml', url)
            if match:
                num = int(match.group(1))
                sitemaps.append((num, url))
    
    print(f"Found {len(sitemaps)} sitemaps")
    return sitemaps


def parse_sitemap_xml(content: str) -> List[Dict[str, str]]:
    """Parse sitemap XML and extract article data."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"  XML Parse error: {e}")
        return []
    
    articles = []
    for url_elem in root.findall('sm:url', NS):
        loc = url_elem.find('sm:loc', NS)
        lastmod = url_elem.find('sm:lastmod', NS)
        
        if loc is not None:
            url = loc.text
            lastmod_date = lastmod.text if lastmod is not None else ""
            
            # Extract article slug from URL
            if '/page/' in url:
                name = url.split('/page/')[-1]
            else:
                name = url.split('/')[-1]
            
            articles.append({
                'url': url,
                'name': name,
                'lastmod': lastmod_date
            })
    
    return articles


def write_sitemap_data(links_dir: Path, sitemap_num: int, articles: List[Dict[str, str]]) -> None:
    """Write sitemap data to local files."""
    sitemap_dir = links_dir / f"sitemap-{sitemap_num:05d}"
    sitemap_dir.mkdir(parents=True, exist_ok=True)
    
    # Write names.txt
    with open(sitemap_dir / "names.txt", 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(article['name'] + '\n')
    
    # Write urls.txt
    with open(sitemap_dir / "urls.txt", 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(article['url'] + '\n')
    
    # Write dates.txt
    with open(sitemap_dir / "dates.txt", 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(article['lastmod'] + '\n')


def main():
    args = parse_args()
    links_dir = get_links_dir()
    
    print("=" * 60)
    print("Grokipedia Sitemap Downloader")
    print("=" * 60)
    print(f"Links directory: {links_dir}")
    print(f"SSL Verification: {'Disabled' if args.no_ssl_verify else 'Enabled'}")
    print()
    
    # Fetch sitemap index
    sitemaps = fetch_sitemap_index(ssl_verify=not args.no_ssl_verify)
    if not sitemaps:
        print("\nFailed to fetch sitemap index. Try with --no-ssl-verify")
        return 1
    
    # Filter by range
    if args.end:
        sitemaps = [(n, u) for n, u in sitemaps if args.start <= n <= args.end]
    else:
        sitemaps = [(n, u) for n, u in sitemaps if n >= args.start]
    
    print(f"\nProcessing {len(sitemaps)} sitemaps (#{args.start} to #{sitemaps[-1][0] if sitemaps else 'N/A'})")
    if args.dry_run:
        print("DRY RUN MODE - No files will be written")
    print()
    
    # Process each sitemap
    updated = 0
    failed = 0
    
    for i, (sitemap_num, sitemap_url) in enumerate(sitemaps, 1):
        print(f"[{i}/{len(sitemaps)}] Downloading sitemap-{sitemap_num:05d}...", end=" ", flush=True)
        
        content = fetch_url(sitemap_url, ssl_verify=not args.no_ssl_verify)
        if not content:
            print("[FAILED]")
            failed += 1
            continue
        
        articles = parse_sitemap_xml(content)
        if not articles:
            print("[NO ARTICLES]")
            failed += 1
            continue
        
        if args.dry_run:
            print(f"[DRY RUN] {len(articles)} articles")
        else:
            write_sitemap_data(links_dir, sitemap_num, articles)
            print(f"[OK] {len(articles)} articles")
        
        updated += 1
        time.sleep(RATE_LIMIT_DELAY)
    
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total: {len(sitemaps)}")
    print(f"  Updated: {updated}")
    print(f"  Failed: {failed}")
    print("=" * 60)
    
    if args.dry_run:
        print("\nRun without --dry-run to apply changes")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
