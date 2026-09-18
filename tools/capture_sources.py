"""Capture selected source blobs from an explicit immutable Git commit.

Never read source working-tree files or account data. Hash capture is not a full
source audit; chapter text states which relevant symbols were reviewed.
"""
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
src/cli/chats.rs
src/cli/voices.rs
src/service/chat_plan.rs
src/service/task_artifacts.rs
src/service/plan.rs
src/service/operation_requests/plan.rs
src/daemon/operations/plan_tasks.rs
src/daemon/tasks/plan_artifacts.rs
src/daemon/tasks/artifacts.rs
src/daemon/tasks/artifact_file.rs
src/daemon/tasks/process.rs
src/windows_process/managed.rs
src/windows_process/managed/native.rs
src/windows_process/README.md
src/business/VOICE_EXPORT.md
src/daemon/operations/voices.rs
src/adapters/wechat/media/voice_export.rs
src/mcp/PROTOCOL.md
docs/task-artifacts.md
src/service/voice_export.rs
src/business/voice_export.rs
src/daemon/tasks/voice_artifacts.rs
src/cli/mcp_tasks.rs
src/cli/web_native.rs
src/service/web.rs
src/web/voices.rs
src/web/artifacts.rs
src/service/image_import.rs
src/daemon/operations/image_import.rs
src/daemon/operations/export_sns/source.rs
src/application/image_publication.rs
src/attachment/local_files.rs
src/infrastructure/output_tree/mod.rs
src/application/moments/cache.rs
src/adapters/wechat/moments/cache.rs
'''.splitlines()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_root', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--publication-commit', required=True,
                        help='Explicit immutable Private source baseline, read directly from Git objects.')
    args = parser.parse_args()
    root = args.source_root.resolve()
    output = Path(__file__).resolve().parents[1] / 'evidence/source-manifest.json'
    publication = subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', '--verify', args.publication_commit+'^{commit}'],
        text=True).strip()
    if len(publication) != 40 or any(c not in '0123456789abcdef' for c in publication):
        raise ValueError('expected full SHA-1 commit')
    baseline = json.loads((output.parent / 'source-manifest-2026-09-17.json').read_text(encoding='utf-8'))
    previous = {row['path']: row['git_blob_sha256'] for row in baseline['files']}
    rows = []
    for name in sorted(FILES):
        data = subprocess.check_output(['git', '-C', str(root), 'show', publication+':'+name])
        digest = hashlib.sha256(data).hexdigest()
        rows.append({
            'path': name, 'sha256': digest, 'git_blob_sha256': digest, 'bytes': len(data),
            'source_link': 'https://github.com/leyan2174/wx-workbench/blob/'+publication+'/'+name,
            'unchanged_from_previous_git_blob': previous.get(name) == digest,
            'review_method': ('prior-relevant-reading-plus-unchanged-git-blob'
                              if previous.get(name) == digest else
                              'fixed-commit-blob-capture; chapter text defines relevant-symbol review scope'),
        })
    if args.check:
        old_manifest = json.loads(output.read_text(encoding='utf-8'))
        old = {r['path']: r for r in old_manifest['files']}
        new = {r['path']: r for r in rows}
        changed = sorted(name for name in old.keys() | new.keys() if old.get(name) != new.get(name))
        commit_match = old_manifest['publication_candidate_commit'] == publication
        print(json.dumps({'changed': changed, 'commit_match': commit_match}, ensure_ascii=False))
        raise SystemExit(bool(changed) or not commit_match)
    manifest = {'schema': 3, 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_repository': 'https://github.com/leyan2174/wx-workbench',
                'observed_head': publication,
                'status': 'private-fixed-commit-candidate',
                'publication_candidate_commit': publication,
                'visibility_target': 'private',
                'source_links_verified_remotely': False,
                'source_mode': 'git-objects-only; working tree and checkout HEAD excluded',
                'commit_comparison': 'SHA-256 and byte counts are exact Git blob bytes; no newline normalization.',
                'historical_manifests': ['source-manifest-2026-09-16.json', 'source-manifest-2026-09-17.json'],
                'previous_source_commit': baseline['publication_candidate_commit'],
                'review_scope': 'Selected immutable blobs; relevant CLI, plan, artifact, process, raw-voice selection and group registration, Web/MCP authorization, and initialization symbols reviewed. Hash capture alone is not a full file audit or production test run.',
                'files': rows}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'files': len(rows), 'status': manifest['status']}))
