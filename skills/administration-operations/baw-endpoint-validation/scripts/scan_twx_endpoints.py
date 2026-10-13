#!/usr/bin/env python3
"""
scan_twx_endpoints.py — BAW Endpoint Transition Scanner
Scans a BAW TWX export for hardcoded server references that will break after
promotion to a new environment.

Usage:
    python scan_twx_endpoints.py --twx <path.twx> --source-map '{"old.server.com": "dmgr", "db.old.com": "db-host"}'
    python scan_twx_endpoints.py --twx <path.twx> --source-map-file source_map.json

stdlib only — no pip dependencies required.
"""

import argparse
import json
import os
import re
import sys
import zipfile
# BAW-internal context roots — localhost references to these are valid on any stand-alone server
_BAW_INTERNAL_ROOTS = re.compile(
    r'localhost[^/]*/('
    r'portal|teamworks|rest/bpm|ProcessPortal|BPMTaskList|BusinessSpace|'
    r'bpm/explorer|lombardi|baw|wle|rest/system'
    r')',
    re.IGNORECASE,
)

# Patterns that indicate a line has runtime significance
_CRITICAL_PATTERNS = [
    re.compile(r'<url\b[^>]*>', re.IGNORECASE),
    re.compile(r'<endpoint\b[^>]*>', re.IGNORECASE),
    re.compile(r'<wsdlUrl\b[^>]*>', re.IGNORECASE),
    re.compile(r'<restUrl\b[^>]*>', re.IGNORECASE),
    re.compile(r'<hostname\b[^>]*>', re.IGNORECASE),
    re.compile(r'<host\b[^>]*>', re.IGNORECASE),
    re.compile(r'jdbc:', re.IGNORECASE),
    re.compile(r'https?://', re.IGNORECASE),
    re.compile(r'<serverURL\b[^>]*>', re.IGNORECASE),
    re.compile(r'<serviceURL\b[^>]*>', re.IGNORECASE),
    re.compile(r'<targetAddress\b[^>]*>', re.IGNORECASE),
    re.compile(r'urlTemplate\s*=\s*["\']', re.IGNORECASE),
    re.compile(r'<urlTemplate\b', re.IGNORECASE),
]

_WARNING_PATTERNS = [
    re.compile(r'<script\b', re.IGNORECASE),
    re.compile(r'<ns\d+:script\b', re.IGNORECASE),
    re.compile(r'<defaultValue\b', re.IGNORECASE),
    re.compile(r'<parameter\b', re.IGNORECASE),
    re.compile(r'<value\b', re.IGNORECASE),
]

# File types to skip (binary/compiled)
_SKIP_EXTENSIONS = {'.jar', '.class', '.png', '.gif', '.jpg', '.jpeg', '.ico', '.zip'}


def is_baw_internal_localhost(line_text: str) -> bool:
    """Return True if the localhost reference points to a known BAW-internal context root."""
    return bool(_BAW_INTERNAL_ROOTS.search(line_text))


def classify_severity(line_text: str, matched_term: str = '') -> str:
    """Return 'critical', 'warning', or 'info' based on line context.

    localhost references to BAW-internal URLs (/portal, /teamworks, etc.) are
    downgraded to 'warning' because they resolve correctly on any stand-alone server.
    """
    # Downgrade BAW-internal localhost URLs before applying critical patterns
    if 'localhost' in matched_term.lower() and is_baw_internal_localhost(line_text):
        return 'warning'

    for pattern in _CRITICAL_PATTERNS:
        if pattern.search(line_text):
            return 'critical'
    for pattern in _WARNING_PATTERNS:
        if pattern.search(line_text):
            return 'warning'
    return 'info'


def scan_content(content: str, source_terms: list, filename: str) -> list:
    """Scan text content for occurrences of source_terms. Returns list of finding dicts."""
    findings = []
    lines = content.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for term in source_terms:
            if term.lower() in line.lower():
                severity = classify_severity(line, matched_term=term)
                # Add a hint when a localhost URL is downgraded to warning
                note = ''
                if severity == 'warning' and 'localhost' in term.lower() and is_baw_internal_localhost(line):
                    note = ' [BAW-internal — resolves locally, no change needed]'
                findings.append({
                    'file': filename,
                    'line': lineno,
                    'matched_pattern': term,
                    'severity': severity,
                    'context_snippet': line.strip()[:200] + note,
                })
    return findings


def is_text_file(name: str) -> bool:
    """Return True if the file is likely text-based (XML, JS, etc.)."""
    _, ext = os.path.splitext(name.lower())
    if ext in _SKIP_EXTENSIONS:
        return False
    # Allow .xml, .js, .json, .html, .properties, .wsdl, .xsd, and no-extension
    return True


def scan_twx(twx_path: str, source_map: dict) -> dict:
    """
    Open the TWX (ZIP) file and scan all text entries for source endpoint references.
    Returns a dict with 'findings' (list), 'files_scanned', 'binary_files_skipped'.
    """
    source_terms = list(source_map.keys())
    if not source_terms:
        return {'error': 'source-map is empty — nothing to search for.', 'findings': []}

    findings = []
    files_scanned = 0
    binary_skipped = 0

    try:
        with zipfile.ZipFile(twx_path, 'r') as zf:
            for entry in zf.infolist():
                if entry.is_dir():
                    continue
                if not is_text_file(entry.filename):
                    binary_skipped += 1
                    continue
                try:
                    raw = zf.read(entry.filename)
                    # Try UTF-8, fall back to latin-1
                    try:
                        content = raw.decode('utf-8')
                    except UnicodeDecodeError:
                        content = raw.decode('latin-1', errors='replace')
                    files_scanned += 1
                    file_findings = scan_content(content, source_terms, entry.filename)
                    findings.extend(file_findings)
                except Exception as e:
                    # Record read errors but continue
                    findings.append({
                        'file': entry.filename,
                        'line': 0,
                        'matched_pattern': '(read error)',
                        'severity': 'info',
                        'context_snippet': f'Error reading file: {e}',
                    })
    except zipfile.BadZipFile:
        return {'error': f'"{twx_path}" is not a valid ZIP/TWX file.', 'findings': []}
    except FileNotFoundError:
        return {'error': f'TWX file not found: "{twx_path}"', 'findings': []}

    # Sort: critical first, then warning, then info
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    findings.sort(key=lambda f: severity_order.get(f['severity'], 9))

    return {
        'findings': findings,
        'files_scanned': files_scanned,
        'binary_files_skipped': binary_skipped,
        'source_terms_searched': source_terms,
    }


def _safe_print(text: str) -> None:
    """Print text to stdout, replacing unencodable characters for non-UTF-8 consoles."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or 'ascii', errors='replace').decode(sys.stdout.encoding or 'ascii'))


def summarise(result: dict) -> None:
    """Print a human-readable summary to stdout."""
    if 'error' in result:
        print(f'ERROR: {result["error"]}', file=sys.stderr)
        return

    findings = result['findings']
    critical = [f for f in findings if f['severity'] == 'critical']
    warnings = [f for f in findings if f['severity'] == 'warning']
    info = [f for f in findings if f['severity'] == 'info']

    _safe_print('\n=== TWX Endpoint Scan Results ===')
    _safe_print(f'Files scanned : {result["files_scanned"]}')
    _safe_print(f'Binary skipped: {result["binary_files_skipped"]}')
    _safe_print(f'Terms searched: {", ".join(result["source_terms_searched"])}')
    _safe_print('')
    _safe_print(f'[CRITICAL] : {len(critical)}')
    _safe_print(f'[WARNING]  : {len(warnings)}')
    _safe_print(f'[INFO]     : {len(info)}')

    if critical:
        _safe_print('\n--- Critical Findings ---')
        for f in critical:
            _safe_print(f'  [{f["file"]}:{f["line"]}] "{f["matched_pattern"]}"')
            _safe_print(f'    {f["context_snippet"]}')

    if warnings:
        _safe_print('\n--- Warnings ---')
        for f in warnings:
            _safe_print(f'  [{f["file"]}:{f["line"]}] "{f["matched_pattern"]}"')
            _safe_print(f'    {f["context_snippet"]}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Scan a BAW TWX export for hardcoded server endpoint references.'
    )
    parser.add_argument('--twx', required=True, help='Path to the .twx file')
    parser.add_argument(
        '--json', action='store_true',
        help='Emit results as a single JSON object instead of human-readable text. '
             'Useful for programmatic consumption by agents.',
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--source-map',
        help='JSON object mapping source hostnames/IPs to labels. '
             'Example: \'{"old.server.com": "dmgr", "10.0.0.1": "db-host"}\'',
    )
    source_group.add_argument(
        '--source-map-file',
        help='Path to a UTF-8 JSON file containing the source map (avoids shell quoting issues). '
             'File must contain a JSON object, e.g. {"old.server.com": "dmgr"}',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load source map from file or inline string
    if args.source_map_file:
        try:
            with open(args.source_map_file, encoding='utf-8') as fh:
                source_map = json.load(fh)
        except FileNotFoundError:
            print(f'ERROR: --source-map-file not found: "{args.source_map_file}"', file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f'ERROR: --source-map-file is not valid JSON: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        try:
            source_map = json.loads(args.source_map)
        except json.JSONDecodeError as e:
            print(f'ERROR: --source-map is not valid JSON: {e}', file=sys.stderr)
            sys.exit(1)

    result = scan_twx(args.twx, source_map)

    if 'error' in result:
        print(f'ERROR: {result["error"]}', file=sys.stderr)
        sys.exit(1)

    if args.json:
        _safe_print(json.dumps(result, indent=2))
    else:
        summarise(result)

    # Exit with non-zero if there are critical findings
    critical_count = sum(1 for f in result['findings'] if f['severity'] == 'critical')
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == '__main__':
    main()
