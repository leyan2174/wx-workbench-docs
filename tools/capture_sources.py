"""Capture metadata of explicitly reviewed source files, never account data."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

FILES = '''THIRD_PARTY_NOTICES.md
src/config.rs
src/crypto/mod.rs
src/crypto/auth.rs
src/crypto/wal.rs
src/scanner/windows/account.rs
src/attachment/decoder/mod.rs
src/attachment/decoder/v2.rs
src/attachment/decoder/v1_xor.rs
src/adapters/wechat/contacts/mod.rs
src/adapters/wechat/messages/sessions.rs
src/adapters/wechat/messages/read/mod.rs
src/adapters/wechat/messages/summary.rs
src/adapters/wechat/messages/export_content.rs
src/adapters/wechat/media/resource.rs
src/adapters/wechat/media/strict_image.rs
src/adapters/wechat/media/legacy_dat.rs
src/adapters/wechat/media/directory_layout.rs
src/adapters/wechat/media/voice.rs
src/adapters/wechat/media/sns_keystream.rs
src/adapters/wechat/media/SNS_KEYSTREAM.md
src/adapters/wechat/emoticons/remote_format.rs
src/adapters/wechat/moments.rs
src/adapters/wechat/moments/legacy.rs
src/adapters/wechat/moments/decode.rs
src/adapters/wechat/moments/query_xml.rs
src/infrastructure/audio/mod.rs
src/application/database_decryption.rs
src/application/emoticons/download.rs
src/application/moments/album_images.rs
src/application/moments/export.rs
src/application/mod.rs
src/infrastructure/mod.rs
src/scanner/mod.rs
src/cli/mod.rs
src/daemon/operations/init.rs
src/daemon/worker_keys.rs
src/daemon/operation_worker.rs
src/service/worker_keys.rs
src/service/operation_requests/key_provider.rs
src/adapters/wechat/media/assets/README.md
'''.splitlines()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_root', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--publication-commit', help='Explicit immutable Private source baseline; may differ from checkout HEAD.')
    args = parser.parse_args()
    root = args.source_root.resolve()
    output = Path(__file__).resolve().parents[1] / 'evidence/source-manifest.json'
    rows = []
    for name in FILES:
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError('unsafe source')
        data = p.read_bytes()
        rows.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    if args.check:
        old = {r['path']: r['sha256'] for r in json.loads(output.read_text(encoding='utf-8'))['files']}
        changed = [r['path'] for r in rows if old.get(r['path']) != r['sha256']]
        print(json.dumps({'changed': changed}, ensure_ascii=False))
        raise SystemExit(bool(changed))
    head = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip()
    publication = None
    if args.publication_commit:
        publication = subprocess.check_output(['git','-C',str(root),'rev-parse','--verify',args.publication_commit+'^{commit}'], text=True).strip()
    comparison_commit = publication or head
    baseline = json.loads((output.parent / 'source-manifest-2026-09-16.json').read_text(encoding='utf-8'))
    previous = {row['path']: row['sha256'] for row in baseline['files']}
    for row in rows:
        committed = subprocess.check_output(['git','-C',str(root),'show',comparison_commit+':'+row['path']])
        current = (root / row['path']).read_bytes()
        row['git_blob_sha256'] = hashlib.sha256(committed).hexdigest()
        row['byte_exact_commit_match'] = row['git_blob_sha256'] == row['sha256']
        row['matches_observed_commit'] = committed.replace(b'\r\n', b'\n') == current.replace(b'\r\n', b'\n')
        if publication:
            if not row['matches_observed_commit']:
                raise ValueError('source differs from mapped commit: '+row['path'])
            row['source_link'] = 'https://github.com/leyan2174/wx-workbench/blob/'+publication+'/'+row['path']
        row['review_method'] = ('prior-relevant-sections-plus-unchanged-hash' if previous.get(row['path']) == row['sha256'] else 'current-relevant-sections-or-diff')
    manifest = {'schema': 2, 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_repository': 'https://github.com/leyan2174/wx-workbench',
                'observed_head': comparison_commit, 'checkout_head_at_capture': head,
                'status': 'private-source-mapped' if publication else 'reviewed-subset-not-publication-freeze',
                'publication_candidate_commit': publication,
                'visibility_target': 'private',
                'source_links_verified_remotely': False,
                'commit_comparison': 'Text comparison normalizes CRLF to LF; raw working-tree and Git blob hashes are both retained.',
                'historical_manifest': 'source-manifest-2026-09-16.json',
                'review_scope': 'Relevant symbols and diffs, or previous reading with unchanged hashes; not a full audit or production test run.', 'files': rows}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'files': len(rows), 'status': manifest['status']}))
