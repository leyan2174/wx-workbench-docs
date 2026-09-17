"""Synthetic WAL vectors: checksum/commit selection, HMAC and application order.

No account input. Payloads are artificial authenticated ciphertext-shaped bytes;
AES decryption is intentionally NOT exercised here. See check_crypto.ps1 for AES.
"""
import hashlib
import hmac
import json
import struct

PAGE = 4096
FRAME = 24 + PAGE
SALT = bytes(range(16))
KEY = bytes(range(32))  # synthetic derived-key input, not a captured key
MAC_KEY = hashlib.pbkdf2_hmac('sha512', KEY, bytes(b ^ 0x3a for b in SALT), 2, 32)
GENERATION = bytes.fromhex('1122334455667788')


def checksum(data, little, state=(0, 0)):
    assert len(data) % 8 == 0
    a, b = state
    for x, y in struct.iter_unpack('<II' if little else '>II', data):
        a = (a + x + b) & 0xffffffff
        b = (b + y + a) & 0xffffffff
    return a, b


def page(number, label):
    # Full WAL ciphertext layout, INCLUDING actual page number 1.
    body_iv = bytes([label]) * 4016 + bytes(range(16, 32))
    tag = hmac.digest(MAC_KEY, body_iv + struct.pack('<I', number), 'sha512')
    return body_iv + tag


def make_wal(spec, little=True, invalid_auth_at=None):
    header = struct.pack('>IIII', 0x377f0682 if little else 0x377f0683,
                         3007000, PAGE, 0) + GENERATION
    state = checksum(header, little)
    result = bytearray(header + struct.pack('>II', *state))
    for index, (number, commit_pages, label) in enumerate(spec):
        payload = page(number, label)
        if index == invalid_auth_at:
            payload = payload[:-1] + bytes([payload[-1] ^ 1])
        prefix = struct.pack('>II', number, commit_pages)
        state = checksum(payload, little, checksum(prefix, little, state))
        result.extend(prefix + GENERATION + struct.pack('>II', *state) + payload)
    return bytes(result)


def selected(data):
    if len(data) < 32:
        raise ValueError('header truncated')
    magic, version, size = struct.unpack_from('>III', data)
    if magic not in (0x377f0682, 0x377f0683) or version != 3007000 or size != PAGE:
        raise ValueError('unsupported header')
    little = magic == 0x377f0682
    state = checksum(data[:24], little)
    if state != struct.unpack_from('>II', data, 24):
        raise ValueError('header checksum')
    frames, last = [], None
    for pos in range(32, len(data) - FRAME + 1, FRAME):
        frame = data[pos:pos + FRAME]
        number, count = struct.unpack_from('>II', frame)
        if number == 0 or frame[8:16] != data[16:24]:
            break
        next_state = checksum(frame[24:], little, checksum(frame[:8], little, state))
        if next_state != struct.unpack_from('>II', frame, 16):
            break
        if number > 1000000 or count > 1000000:
            raise ValueError('resource limit')
        state = next_state
        frames.append((number, count, frame[24:]))
        if count:
            last = len(frames), count
    if last is None:
        return [], None
    return frames[:last[0]], last[1]


def authenticate(frames):
    for number, _, payload in frames:
        expected = hmac.digest(MAC_KEY, payload[:4032] + struct.pack('<I', number), 'sha512')
        if not hmac.compare_digest(expected, payload[4032:]):
            raise ValueError('page HMAC')


def apply_labels(old, frames, final_count):
    # A label represents one already decrypted 4096-byte page. This stage tests
    # ordering and truncation only; it does not pretend to decrypt ciphertext.
    authenticate(frames)  # all selected frames before any output mutation
    result = list(old)
    for number, count, payload in frames:
        result.extend([0] * max(0, number - len(result)))
        result[number - 1] = payload[0]
        if count:
            result = result[:count] + [0] * max(0, count - len(result))
    if final_count is not None:
        result = result[:final_count] + [0] * max(0, final_count - len(result))
    return result


def rejected(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('invalid input accepted')


def run():
    checks = []
    vectors = []
    def vector(name, spec, expected, little=True):
        data = make_wal(spec, little)
        frames, count = selected(data)
        authenticate(frames)
        actual = (len(frames), count)
        assert actual == expected, (name, actual)
        vectors.append({'name': name, 'frames': spec, 'checksum_little_endian': little,
                        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                        'selected_frames': expected[0], 'final_pages': expected[1]})
        checks.append(name)
        return data
    # Primitive arithmetic anchor independent of the WAL builder.
    assert checksum(bytes.fromhex('01000000020000000300000004000000'), True) == (7, 14)
    assert checksum(bytes.fromhex('00000001000000020000000300000004'), False) == (7, 14)
    checks.append('checksum-arithmetic-and-byte-order')
    vector('no-commit', [(1, 0, 10)], (0, None))
    base = vector('uncommitted-tail', [(1, 2, 10), (2, 0, 20)], (1, 2))
    vector('big-endian-checksum', [(1, 1, 10)], (1, 1), False)
    overwrite = vector('same-page-last-write', [(1, 1, 10), (1, 1, 20)], (2, 1))
    assert apply_labels([9], *selected(overwrite)) == [20]
    shrink = vector('shrink-then-grow', [(1, 1, 10), (3, 3, 30)], (2, 3))
    assert apply_labels([7, 8, 9], *selected(shrink)) == [10, 0, 30]
    committed_prefix = make_wal([(1, 1, 10)])
    assert selected(committed_prefix + b'partial-frame')[1] == 1
    checks.append('partial-tail-ignored')
    three = make_wal([(1, 1, 10), (2, 0, 20), (3, 3, 30)])
    corrupt = bytearray(three)
    corrupt[32 + FRAME + 24] ^= 1
    assert (len(selected(corrupt)[0]), selected(corrupt)[1]) == (1, 1)
    checks.append('bad-frame-stops-before-later-commit')
    stale = bytearray(three)
    stale[32 + FRAME + 8] ^= 1
    assert len(selected(stale)[0]) == 1
    checks.append('generation-mismatch-stops')
    bad_header = bytearray(base)
    bad_header[24] ^= 1
    rejected(lambda: selected(bad_header))
    checks.append('header-checksum-rejected')
    rejected(lambda: selected(base[:31]))
    checks.append('truncated-header-rejected')
    # Recompute a valid rolling chain around a bad page HMAC: checksum is NOT MAC.
    bad_mac = make_wal([(1, 0, 10), (1, 1, 20)], invalid_auth_at=0)
    selected_bad, count = selected(bad_mac)
    old = [99]
    rejected(lambda: apply_labels(old, selected_bad, count))
    assert old == [99]
    checks.append('overwritten-bad-HMAC-still-rejected-output-preserved')
    wrong_number = [(2, 1, page(1, 10))]
    rejected(lambda: authenticate(wrong_number))
    checks.append('HMAC-binds-little-endian-real-page-number')
    wrong_salt_key = hashlib.pbkdf2_hmac('sha512', KEY, GENERATION * 2, 2, 32)
    assert not hmac.compare_digest(page(1, 10)[4032:],
                                  hmac.digest(wrong_salt_key, page(1, 10)[:4032] + b'\x01\0\0\0', 'sha512'))
    checks.append('WAL-generation-not-authentication-salt')
    rejected(lambda: selected(make_wal([(1000001, 1, 10)])))
    checks.append('valid-checksum-over-limit-rejected')
    return {'checks': checks, 'vectors': vectors,
            'limits': 'Synthetic structure/authentication/application tests; not AES end-to-end, production-code execution, or real WeChat evidence.'}


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-vectors', type=Path)
    args = parser.parse_args()
    report = run()
    if args.write_vectors:
        args.write_vectors.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': len(report['checks']), 'vectors': len(report['vectors']),
                      'limits': report['limits']}, ensure_ascii=False))
