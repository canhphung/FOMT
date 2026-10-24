#!/usr/bin/env python3
"""Local English–Vietnamese translation editor; no ROM or external API required.

The extracted catalog supplies immutable source fields. Saving edits the seven
existing translation files, never QA approvals, font assets or the ROM.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import unicodedata
from urllib.parse import parse_qs, unquote, urlsplit

from fomt_text import FormatError, ROM_SHA1, check_translation, encode, tokens
from localization_queue import DEFAULT_TRANSLATIONS, FIELDS, ROOT, index_records, queue

ASSETS = Path(__file__).resolve().parent / 'workbench'


class EditorError(ValueError):
    def __init__(self, status, message, **details):
        super().__init__(message)
        self.status, self.details = status, details


def folded(value):
    value = unicodedata.normalize('NFD', str(value or '').casefold().replace('đ', 'd'))
    return ''.join(c for c in value if not unicodedata.combining(c))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Repository:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.catalog = self.root / 'localization/en/catalog.json'
        self.paths = [self.root / p.relative_to(ROOT) for p in DEFAULT_TRANSLATIONS]
        self.qa = self.root / 'localization/qa/records.json'
        self.glossary = self.root / 'localization/glossary.json'
        self.profiles = self.root / 'localization/character_profiles.json'
        self.batches = sorted((self.root / 'localization/qa/batches').glob('*.json'))
        self.local = self.root / 'local-data/workbench'
        self.lock = threading.RLock()
        self.cache_key = self.cache = None

    def snapshot(self, force=False):
        with self.lock:
            paths = [self.catalog, *self.paths, self.qa, self.glossary, self.profiles, *self.batches]
            key = tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
            if not force and key == self.cache_key:
                return self.cache
            raw = {p: p.read_bytes() for p in paths}
            data = {p: json.loads(content) for p, content in raw.items()}
            catalog = data[self.catalog]
            if catalog.get('rom', {}).get('sha1') != ROM_SHA1:
                raise FormatError('Catalog must be extracted from the supported USA rev 0 ROM.')
            owners, translations = {}, []
            for path in self.paths:
                if data[path].get('rom_sha1') != ROM_SHA1:
                    raise FormatError(f'Translation file targets a different ROM: {path.name}')
                for row in data[path]['records']:
                    if row['id'] in owners:
                        raise FormatError('duplicate translation ID: ' + row['id'])
                    owners[row['id']] = path
                    translations.append(row)
            rows = queue(catalog, translations, data[self.qa])
            originals = index_records(catalog['records'], 'catalog')
            vi = index_records(translations, 'translation')
            manual = index_records(data[self.qa]['records'], 'QA')
            for row in rows:
                identifier = row['id']
                row['revision'] = sha(json.dumps([originals[identifier], vi.get(identifier),
                    manual.get(identifier)], ensure_ascii=False, sort_keys=True).encode())
                row['_search'] = folded(' '.join(str(row.get(k) or '') for k in
                    ('id', 'original_english', 'vietnamese_translation', 'context', 'speaker', 'source_reference')))
            batches = {}
            for path in self.batches:
                batch = data[path]
                ids = batch['record_ids']
                if len(ids) != len(set(ids)) or set(ids) - originals.keys():
                    raise FormatError('Invalid batch: ' + path.name)
                batches[path.stem] = batch
            snapshot = {'rows': rows, 'index': index_records(rows, 'queue'), 'originals': originals,
                        'vi': vi, 'manual': manual, 'owners': owners, 'data': data, 'raw': raw,
                        'glossary': data[self.glossary], 'profiles': data[self.profiles]['profiles'],
                        'batches': batches}
            self.cache_key, self.cache = key, snapshot
            return snapshot

    def meta(self):
        s = self.snapshot()
        return {'total': len(s['rows']), 'summary': {b: sum(r['bucket'] == b for r in s['rows'])
                    for b in ('translate', 'qa', 'blocked', 'done')},
                'drafts': len(s['vi']), 'contexts': sorted({r['context'] for r in s['rows']}),
                'speakers': sorted({r['speaker'] for r in s['rows'] if r['speaker']}),
                'batches': [{'id': key, 'count': len(value['record_ids'])} for key, value in s['batches'].items()],
                'glossary_terms': len(s['glossary']['terms']),
                'profiles': s['profiles'], 'glossary_rules': s['glossary']['rules']}

    def search(self, params, paginate=True):
        s = self.snapshot()
        query = folded(params.get('q', ''))
        batch = params.get('batch', '')
        if batch and batch not in s['batches']:
            raise EditorError(400, 'Lô dịch không tồn tại.')
        batch_ids = set(s['batches'][batch]['record_ids']) if batch else None
        rows = [r for r in s['rows'] if (not query or query in r['_search'])
                and all(not params.get(k) or r[k] == params[k] for k in ('bucket', 'context', 'speaker'))
                and (params.get('issues') != '1' or r['validation_errors'])
                and (batch_ids is None or r['id'] in batch_ids)]
        total = len(rows)
        if paginate:
            try:
                offset, limit = max(0, int(params.get('offset', 0))), int(params.get('limit', 50))
            except ValueError:
                raise EditorError(400, 'Trang không hợp lệ.')
            if not 1 <= limit <= 100:
                raise EditorError(400, 'Mỗi trang cần từ 1 đến 100 bản ghi.')
            rows = rows[offset:offset + limit]
        return {'total': total, 'records': [{k: v for k, v in r.items() if not k.startswith('_')} for r in rows]}

    def record(self, identifier, snapshot=None):
        s = snapshot or self.snapshot()
        if identifier not in s['index']:
            raise EditorError(404, 'Không tìm thấy ID nguồn.')
        row = {k: v for k, v in s['index'][identifier].items() if not k.startswith('_')}
        original = s['originals'][identifier]
        row.update(max_columns=original['max_columns'], max_encoded_bytes=original.get('max_encoded_bytes'),
                   translation_file=str(s['owners'].get(identifier, self.destination(identifier)).relative_to(self.root)),
                   editable=(row['context_status'] == 'verified' and not s['manual'].get(identifier, {}).get('blocked_reason')),
                   profiles=[p for p in s['profiles'] if identifier in p['source_ids']])
        return row

    def destination(self, identifier):
        # Existing files are already consumed by the locked insertion pipeline.
        return self.root / ('localization/vi/items.json' if identifier.startswith('item.')
                            else 'localization/vi/pilot.json')

    def validate(self, identifier, text, snapshot=None):
        if not isinstance(text, str) or len(text) > 32768:
            raise EditorError(400, 'Bản dịch cần là chuỗi, tối đa 32768 ký tự.')
        s = snapshot or self.snapshot()
        row = self.record(identifier, s)
        original = s['originals'][identifier]
        text = unicodedata.normalize('NFC', text)
        errors, warnings = [], []
        expected, actual = tokens(original['original_english']), tokens(text)
        def error(code, message):
            errors.append({'code': code, 'message': message})
        if not row['editable']:
            error('context', row['blocked_reason'] or 'Cần xác minh ngữ cảnh trước khi dịch.')
        if not text.strip():
            error('empty', 'Bản dịch đang trống.')
        from fomt_text import matching_tokens
        if not matching_tokens(original['original_english'],text,
                padding_reflow=original.get('source',{}).get('sign_context',{}).get('padding_reflow',False),
                    drop_apostrophe=original.get('source',{}).get('popuri_context',{}).get('drop_apostrophe',False)):
            error('tokens', 'Thiếu, thừa hoặc đổi thứ tự control code / placeholder.')
        metrics = {'max_columns': row['max_columns'], 'maximum_tiles': None, 'encoded_bytes': None,
                   'max_encoded_bytes': row['max_encoded_bytes'], 'dynamic_variable_reserve': False}
        try:
            payload = encode(text, True)
            metrics['encoded_bytes'] = len(payload)
            measured = check_translation(text, text, 1 << 30)
            metrics.update({k: measured[k] for k in ('maximum_tiles', 'dynamic_variable_reserve')})
            if measured['maximum_tiles'] > row['max_columns']:
                error('width', f'Dòng dài nhất {measured["maximum_tiles"]} ô; giới hạn {row["max_columns"]} ô.')
            if row['max_encoded_bytes'] is not None and len(payload) > row['max_encoded_bytes']:
                error('bytes', f'{len(payload)} byte; giới hạn {row["max_encoded_bytes"]} byte.')
        except FormatError as exc:
            error('encoding', str(exc))
        suggested = []
        for kind, entries in [('term', s['glossary']['terms']), ('proper_name', s['glossary']['proper_names'])]:
            for term in entries:
                if re.search(r'(?<!\w)' + re.escape(term['english']) + r'(?!\w)', original['original_english'], re.I):
                    suggested.append({**term, 'kind': kind})
                    if kind == 'proper_name' and term['vietnamese'] not in text:
                        warnings.append('Kiểm tra giữ nguyên tên riêng: ' + term['english'])
        return {'valid': not errors, 'errors': errors, 'warnings': warnings, 'metrics': metrics,
                'expected_tokens': expected, 'actual_tokens': actual, 'suggestions': suggested,
                'normalized_text': text}

    def save(self, identifier, text, revision):
        self.local.mkdir(parents=True, exist_ok=True)
        with self.lock, (self.local / 'write.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            s = self.snapshot(force=True)
            row = self.record(identifier, s)
            if revision != row['revision']:
                raise EditorError(409, 'Bản ghi đã đổi ở nơi khác. Tải lại trước khi lưu; bản đang nhập vẫn được giữ.')
            validation = self.validate(identifier, text, s)
            if not validation['valid']:
                raise EditorError(422, 'Chưa thể lưu: hãy sửa các lỗi.', validation=validation)
            text = validation['normalized_text']
            if text == row['vietnamese_translation'] and identifier in s['vi']:
                return {'changed': False, 'record': row, 'validation': validation}
            path = s['owners'].get(identifier, self.destination(identifier))
            document = deepcopy(s['data'][path])
            translated = deepcopy(s['vi'].get(identifier, s['originals'][identifier]))
            translated.update(vietnamese_translation=text, translation_status='translated')
            existing = next((i for i, r in enumerate(document['records']) if r['id'] == identifier), None)
            if existing is None:
                document['records'].append(translated)
            else:
                document['records'][existing] = translated
            before = s['raw'][path]
            backup = self.local / 'backups' / (path.stem + '-' + sha(before) + '.json')
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                with backup.open('xb') as stream:
                    stream.write(before)
            # Detect edits from an external editor before publishing. Other app
            # instances serialize via flock; unrelated records merge on reload.
            if path.read_bytes() != before:
                raise EditorError(409, 'File dịch vừa thay đổi. Tải lại rồi lưu lại.')
            payload = (json.dumps(document, ensure_ascii=False, indent=2) + '\n').encode()
            handle, temporary = tempfile.mkstemp(prefix='.workbench-', suffix='.tmp', dir=path.parent)
            try:
                with os.fdopen(handle, 'wb') as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            self.cache_key = None
            return {'changed': True, 'record': self.record(identifier), 'validation': validation,
                    'backup': str(backup.relative_to(self.root))}

    def glossary_search(self, query):
        glossary = self.snapshot()['glossary']
        terms = [{**t, 'kind': kind} for kind, key in [('term', 'terms'), ('proper_name', 'proper_names')]
                 for t in glossary[key]]
        found = [t for t in terms if folded(query) in folded(' '.join(str(v) for v in t.values()))]
        return {'total': len(found), 'terms': found[:100]}

    def export_csv(self, params):
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction='ignore')
        writer.writeheader()
        for row in self.search(params, paginate=False)['records']:
            row['control_codes'] = ' '.join(row['control_codes'])
            writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r'))
                             else v for k, v in row.items()})
        return ('\ufeff' + stream.getvalue()).encode('utf-8')


def make_server(repository, port=8765, token=None):
    token = token or secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Neither search text nor credentials belong in request logs.

        def reply(self, status, data, content_type='application/json; charset=utf-8'):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            if content_type.startswith('text/csv'):
                self.send_header('Content-Disposition', 'attachment; filename="fomt-translations.csv"')
            self.end_headers()
            self.wfile.write(data)

        def dispatch(self, post=False):
            try:
                allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
                if self.headers.get('Host') not in allowed:
                    raise EditorError(403, 'Host không hợp lệ; chỉ dùng localhost.')
                route = urlsplit(self.path)
                path = route.path
                if path.startswith('/api/'):
                    if not secrets.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                        raise EditorError(401, 'Mở đường dẫn có mã phiên do terminal cung cấp.')
                    if self.headers.get('Origin') and self.headers['Origin'] not in {'http://' + h for h in allowed}:
                        raise EditorError(403, 'Origin không hợp lệ.')
                params = {k: v[0] for k, v in parse_qs(route.query).items()}
                if post:
                    if path not in ('/api/validate', '/api/save'):
                        raise EditorError(404, 'Không có thao tác này.')
                    if self.headers.get_content_type() != 'application/json':
                        raise EditorError(415, 'Cần JSON.')
                    try:
                        size = int(self.headers.get('Content-Length', '0'))
                    except ValueError:
                        raise EditorError(400, 'Content-Length không hợp lệ.')
                    if not 0 < size <= 262144:
                        raise EditorError(413, 'Yêu cầu quá lớn hoặc trống.')
                    body = json.loads(self.rfile.read(size))
                    expected = {'id', 'text', 'revision'} if path == '/api/save' else {'id', 'text'}
                    if not isinstance(body, dict) or set(body) != expected or not isinstance(body['id'], str):
                        raise EditorError(400, 'Các trường yêu cầu không hợp lệ.')
                    value = repository.save(body['id'], body['text'], body['revision']) if path == '/api/save' else repository.validate(body['id'], body['text'])
                    self.reply(200, value)
                elif path == '/api/meta':
                    self.reply(200, repository.meta())
                elif path == '/api/records':
                    self.reply(200, repository.search(params))
                elif path.startswith('/api/records/'):
                    self.reply(200, repository.record(unquote(path[len('/api/records/'):])) )
                elif path == '/api/glossary':
                    self.reply(200, repository.glossary_search(params.get('q', '')))
                elif path == '/api/export.csv':
                    self.reply(200, repository.export_csv(params), 'text/csv; charset=utf-8')
                elif path in ('/', '/app.js', '/style.css'):
                    asset, mime = {'/': ('index.html', 'text/html; charset=utf-8'),
                                   '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                                   '/style.css': ('style.css', 'text/css; charset=utf-8')}[path]
                    self.reply(200, (ASSETS / asset).read_bytes(), mime)
                else:
                    raise EditorError(404, 'Không tìm thấy trang.')
            except EditorError as exc:
                self.reply(exc.status, {'error': str(exc), **exc.details})
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.reply(400, {'error': 'Không đọc được dữ liệu: ' + str(exc)})

        def do_GET(self):
            self.dispatch()

        def do_POST(self):
            self.dispatch(post=True)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.session_token = token
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--project-root', type=Path, default=ROOT, help='checkout or disposable data copy')
    args = parser.parse_args()
    try:
        repository = Repository(args.project_root)
        meta = repository.meta()
        server = make_server(repository, args.port)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'error: {exc}\nExtract localization/en/catalog.json first; see README_VI.md.\n')
    print(f'FOMT: {meta["total"]} source records; {meta["drafts"]} drafts. Ctrl+C to stop.', flush=True)
    print(f'http://127.0.0.1:{server.server_port}/#token={server.session_token}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
