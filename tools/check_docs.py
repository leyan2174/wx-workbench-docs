"""Local links, fences, prohibited local identifiers, and synthetic examples.

Only reads this documentation tree; never opens account data or follows symlinks.
"""
from pathlib import Path
import hashlib
import json
import re
import sqlite3
import struct
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def check_tree():
    problems = []
    count = 0
    for path in ROOT.rglob('*.md'):
        if path.is_symlink():
            problems.append(f'symlink: {path.relative_to(ROOT)}')
            continue
        text = path.read_text(encoding='utf-8')
        count += 1
        if len(re.findall(r'^```', text, re.M)) % 2:
            problems.append(f'unclosed fence: {path.relative_to(ROOT)}')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if re.match(r'https?://', target) or target.startswith('#'):
                continue
            clean = unquote(target.split('#', 1)[0].strip('<>'))
            dest = (path.parent / clean).resolve()
            if not dest.is_relative_to(ROOT) or not dest.exists():
                problems.append(f'broken/outside link: {path.relative_to(ROOT)} -> {target}')
        for pattern in [r'[A-Za-z]:[\\/]Users[\\/]', r'/Users/',
                        r'01a0[a-f0-9]{4}-[a-f0-9-]{27,}',
                        r'wxid_[A-Za-z0-9]{6,}', r'gh[pousr]_[A-Za-z0-9]{20,}']:
            if re.search(pattern, text):
                problems.append(f'private identifier pattern: {path.relative_to(ROOT)}')
    assert not problems, '\n'.join(problems)
    return count


def normalize_silk(data):
    if len(data) > 16 * 1024 * 1024:
        raise ValueError('limit')
    if data.startswith(b'\x02'):
        data = data[1:]
    if not data.startswith(b'#!SILK_V3'):
        raise ValueError('header')
    pos, count = 9, 0
    while pos < len(data):
        if pos + 2 > len(data):
            raise ValueError('truncated length')
        n = struct.unpack_from('<h', data, pos)[0]
        pos += 2
        if n == -1:
            if pos != len(data) or not count:
                raise ValueError('invalid end')
            return data
        if not 1 <= n <= 1024 or pos + n > len(data):
            raise ValueError('invalid packet')
        pos += n
        count += 1
        if count > 6000:
            raise ValueError('packet limit')
    if not count:
        raise ValueError('empty')
    return data + b'\xff\xff'


def synthetic_checks():
    checks = []
    assert hashlib.md5(b'abc').hexdigest() == '900150983cd24fb0d6963f7d28e17f72'
    checks.append('conversation-md5')
    assert bytes(x ^ 0x88 for x in bytes.fromhex('77507751')) == bytes.fromhex('ffd8ffd9')
    checks.append('legacy-xor')
    assert 16 + (16 - 16 % 16) == 32
    assert 54 - 15 - 32 - 2 == 5
    checks.append('dat-segment-boundaries')
    assert bytes(reversed(bytes(range(16))))[:9] == bytes([15,14,13,12,11,10,9,8,7])
    checks.append('sns-wrapper-order-only-not-wxisaac64')
    valid = b'\x02#!SILK_V3\x01\x00\x00'
    assert normalize_silk(valid) == b'#!SILK_V3\x01\x00\x00\xff\xff'
    for bad in [b'#!SILK_V3', b'#!SILK_V3\x01', b'#!SILK_V3\x02\x00\x00',
                b'#!SILK_V3\x00\x00', b'#!SILK_V3\xff\xff',
                normalize_silk(valid) + b'x']:
        try:
            normalize_silk(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('bad packet accepted')
    checks.append('silk-framing-and-six-negative-cases')
    import xml.etree.ElementTree as ET
    sns = ET.fromstring('<TimelineObject><id>101</id><ContentObject><mediaList><media><id>201</id></media></mediaList></ContentObject></TimelineObject>')
    assert sns.findtext('ContentObject/mediaList/media/id') == '201'
    checks.append('sns-xml-path')
    db = sqlite3.connect(':memory:')
    db.executescript('CREATE TABLE Name2Id(user_name TEXT);'
                     'CREATE TABLE VoiceInfo(chat_name_id INTEGER, svr_id INTEGER, local_id INTEGER);'
                     "INSERT INTO Name2Id(rowid,user_name) VALUES(4,'abc'),(7,'other');"
                     'INSERT INTO VoiceInfo VALUES(4,9001,99),(7,9001,12);')
    rows = db.execute('SELECT v.local_id FROM VoiceInfo v JOIN Name2Id n ON n.rowid=v.chat_name_id WHERE n.user_name=? AND v.svr_id=?', ('abc',9001)).fetchall()
    assert rows == [(99,)]
    db.execute('INSERT INTO VoiceInfo VALUES(4,9001,100)')
    assert len(db.execute('SELECT local_id FROM VoiceInfo WHERE chat_name_id=4 AND svr_id=9001 LIMIT 2').fetchall()) == 2
    db.close()
    checks.append('voice-join-and-ambiguity')
    return checks


if __name__ == '__main__':
    result = {'markdown_files': check_tree(), 'synthetic_checks': synthetic_checks(),
              'limits': 'No real account data; no AES or WxIsaac64 execution in this script.'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
