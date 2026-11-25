#!/usr/bin/env python3
"""Validate measurable TOPIM copy constraints. Input is a UTF-8 JSON file."""
import argparse
import json
import re
from collections import Counter

def validate(data, mode, keyword=None):
    errors = []
    seen = set()
    def field(text, low, high, label, unique=False):
        if not isinstance(text, str):
            errors.append(f'{label}: expected string'); return
        if not low <= len(text) <= high:
            errors.append(f'{label}: {len(text)} characters; expected {low}..{high}')
        if text != text.strip() or '\n' in text or '\r' in text:
            errors.append(f'{label}: whitespace at edges or line break')
        key = re.sub(r'\W+', ' ', text.casefold()).strip()
        if unique and key in seen:
            errors.append(f'{label}: duplicate')
        if unique: seen.add(key)
    if mode == 'full':
        sets = data.get('sets', [])
        if not isinstance(sets, list):
            errors.append('sets: expected list'); sets = []
        if len(sets) != 2: errors.append('Expected 2 audience sets')
        audiences = []
        for i, group in enumerate(sets, 1):
            if not isinstance(group, dict):
                errors.append(f'Set {i}: expected object'); continue
            audiences.append(group.get('audience'))
            headlines = group.get('headlines', [])
            descriptions = group.get('descriptions', [])
            if not isinstance(headlines, list):
                errors.append(f'Set {i}: headlines must be list'); headlines = []
            if not isinstance(descriptions, list):
                errors.append(f'Set {i}: descriptions must be list'); descriptions = []
            if len(headlines) != 20: errors.append(f'Set {i}: expected 20 headlines')
            if len(descriptions) != 20: errors.append(f'Set {i}: expected 20 descriptions')
            counts = Counter()
            for j, item in enumerate(headlines, 1):
                if not isinstance(item, dict):
                    errors.append(f'Set {i} headline {j}: expected object'); continue
                counts[item.get('angle')] += 1
                field(item.get('headline'),46,56,f'Set {i} headline {j}',True)
            if dict(counts) != {'site':7,'jtbd':7,'intrigue':6}:
                errors.append(f'Set {i}: wrong angle distribution')
            for j, text in enumerate(descriptions, 1):
                field(text,70,83,f'Set {i} description {j}',True)
        if Counter(audiences) != Counter(['beginner','experienced']):
            errors.append('Expected beginner and experienced audiences')
    elif mode in ('keyword', 'headlines'):
        rows = data.get('headlines', [])
        if not 10 <= len(rows) <= 15: errors.append('Expected 10..15 headlines')
        if mode == 'keyword' and not keyword: errors.append('Keyword is required')
        for i,text in enumerate(rows,1):
            field(text,46,56,f'Headline {i}',True)
            if keyword and isinstance(text,str) and not re.search(r'(?<!\w)'+re.escape(keyword)+r'(?!\w)',text,re.I):
                errors.append(f'Headline {i}: missing keyword')
    elif mode == 'tests':
        groups = data.get('groups', [])
        if not isinstance(groups, list):
            errors.append('groups: expected list'); groups = []
        if not 1 <= len(groups) <= 2:
            errors.append('Expected 1..2 test directions')
        for i, group in enumerate(groups, 1):
            if not isinstance(group, dict):
                errors.append(f'Group {i}: expected object'); continue
            for key in ('name', 'explanation'):
                value = group.get(key)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f'Group {i}: missing {key}')
            rows = group.get('headlines', [])
            if not isinstance(rows, list):
                errors.append(f'Group {i}: headlines must be a list'); rows = []
            if not 2 <= len(rows) <= 3:
                errors.append(f'Group {i}: expected 2..3 headlines')
            for j, text in enumerate(rows, 1):
                field(text,46,56,f'Group {i} headline {j}',True)
    elif mode in ('extensions', 'extension-titles'):
        rows = data.get('sitelinks', [])
        if not isinstance(rows, list):
            errors.append('sitelinks: expected list')
            rows = []
        if len(rows) != 8: errors.append('sitelinks: expected 8 items')
        for i, row in enumerate(rows, 1):
            if mode == 'extension-titles':
                field(row,1,30,f'sitelinks {i}',True)
            elif not isinstance(row, dict):
                errors.append(f'sitelinks {i}: expected title and description object')
            else:
                field(row.get('title'),1,30,f'sitelinks {i} title',True)
                field(row.get('description'),1,60,f'sitelinks {i} description',True)
        rows = data.get('clarifications', [])
        if not isinstance(rows, list):
            errors.append('clarifications: expected list')
            rows = []
        if not 3 <= len(rows) <= 4: errors.append('clarifications: wrong count')
        for i, text in enumerate(rows,1):
            field(text,1,25,f'clarifications {i}',True)
    else:
        errors.append(f'Unknown mode: {mode}')
    return errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--mode',choices=['full','keyword','headlines','tests','extensions','extension-titles'],default='full')
    parser.add_argument('--keyword')
    args = parser.parse_args()
    try:
        with open(args.input,encoding='utf-8') as f: data=json.load(f)
        if not isinstance(data,dict): raise ValueError('Expected JSON object')
        errors=validate(data,args.mode,args.keyword)
    except (OSError,ValueError,TypeError,AttributeError) as e:
        errors=[f'Invalid input: {e}']
    print(json.dumps({'ok':not errors,'errors':errors},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))
