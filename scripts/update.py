#!/usr/bin/env python3
"""Build a Pi-hole domain blocklist from the public SGB API."""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = 'https://siberguvenlik.gov.tr/api/address/index'
PER_PAGE = 5000
DELAY_SECONDS = 2.0
OUTPUT = Path('domains.txt')
DOMAIN_RE = re.compile(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$', re.IGNORECASE)


def get_page(page):
    params = urllib.parse.urlencode({'type': 'domain', 'page': page, 'per-page': PER_PAGE})
    request = urllib.request.Request(f'{ENDPOINT}?{params}', headers={'User-Agent': 'sgb-pihole-list/1.0 (+public GitHub Actions feed)', 'Accept': 'application/json'})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or not isinstance(payload.get('models'), list):
                raise ValueError('Unexpected API response structure')
            return payload
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 5:
                raise
            retry_after = exc.headers.get('Retry-After') if isinstance(exc, urllib.error.HTTPError) else None
            delay = min(120, max(2 ** (attempt + 1), int(retry_after) if retry_after and retry_after.isdigit() else 0))
            print(f'Page {page}: retrying in {delay}s ({exc})', file=sys.stderr)
            time.sleep(delay)


def normalize(value):
    if not isinstance(value, str):
        return None
    host = value.strip().lower().rstrip('.')
    # Hostnames only. Never widen a specific subdomain to its parent.
    if not DOMAIN_RE.fullmatch(host):
        return None
    return host


def main():
    domains = set()
    first = get_page(1)
    total = first.get('totalCount')
    page_count = first.get('pageCount')
    if not isinstance(total, int) or total <= 0 or not isinstance(page_count, int) or page_count <= 0:
        raise RuntimeError('Invalid/empty API total; protecting existing list')
    if page_count > 5000:
        raise RuntimeError(f'Unexpected page count: {page_count}')
    print(f'API reports {total} records over {page_count} pages')
    fetched = 0
    for page in range(1, page_count + 1):
        payload = first if page == 1 else get_page(page)
        models = payload['models']
        if not models:
            raise RuntimeError(f'Page {page} was empty; protecting existing list')
        fetched += len(models)
        for record in models:
            if not isinstance(record, dict) or record.get('type') != 'domain':
                continue
            domain = normalize(record.get('url'))
            if domain:
                domains.add(domain)
        if page % 10 == 0 or page == page_count:
            print(f'Fetched page {page}/{page_count}; unique domains: {len(domains)}')
        if page != page_count:
            time.sleep(DELAY_SECONDS)
    # A changing source can cause small count drift; reject clearly truncated fetches.
    if fetched < total * 0.90:
        raise RuntimeError(f'Incomplete crawl ({fetched}/{total}); protecting existing list')
    if not domains:
        raise RuntimeError('No valid domains; protecting existing list')
    content = ''.join(f'{domain}\n' for domain in sorted(domains))
    old = OUTPUT.read_text(encoding='utf-8') if OUTPUT.exists() else None
    if content == old:
        print('No changes')
        return
    temporary = OUTPUT.with_suffix('.txt.tmp')
    temporary.write_text(content, encoding='utf-8')
    temporary.replace(OUTPUT)
    print(f'Updated {OUTPUT}: {len(domains)} domains; net lines change: {len(domains) - len(old.splitlines()) if old is not None else len(domains)}')


if __name__ == '__main__':
    main()
