"""Synthetic editor fixtures only; none of these sentences are ROM content."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import http.client
import json
from pathlib import Path
import threading
from urllib.parse import quote

import pytest

from fomt_text import ROM_SHA1
from localization_queue import DEFAULT_TRANSLATIONS, ROOT, digest
from translation_workbench import EditorError, Repository, make_server


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


@pytest.fixture
def repo(tmp_path):
    def original(identifier, context='item_description', text='Fixture{CR}{LF}Description.'):
        return {'id': identifier, 'context': context, 'original_english': text,
                'vietnamese_translation': '', 'translation_status': 'untranslated',
                'max_columns': 28, 'max_encoded_bytes': 90, 'control_codes': ['{CR}', '{LF}'],
                'speaker': None, 'rom_address': 'synthetic fixture, not a ROM address',
                'source': {'kind': 'fixture', 'reference': 'Synthetic unit fixture'}}
    rows = [original('item.fixture.000.description'), original('fixture.unknown', 'script_string_unclassified'),
            original('item.fixture.001.description'), original('item.fixture.002.description'),
            original('fixture.dialogue', 'intro_arrival_dialogue', 'Thomas{CR}{LF}Fixture.'),
            original('item.fixture.flower.name', 'item_name', 'Fixture Flower')]
    rows[4]['speaker'] = 'Thomas'
    write(tmp_path / 'localization/en/catalog.json', {'rom': {'sha1': ROM_SHA1}, 'records': rows})
    for path in DEFAULT_TRANSLATIONS:
        write(tmp_path / path.relative_to(ROOT), {'schema_version': 1, 'rom_sha1': ROM_SHA1, 'records': []})
    translated = {**rows[0], 'vietnamese_translation': 'Mẫu{CR}{LF}Mô tả.', 'translation_status': 'reviewed'}
    write(tmp_path / 'localization/vi/item_descriptions_tools.json',
          {'rom_sha1': ROM_SHA1, 'records': [translated]})
    write(tmp_path / 'localization/qa/records.json', {'records': [
        {'id': rows[0]['id'], 'source_sha256': digest(rows[0]['original_english']),
         'translation_sha256': digest(translated['vietnamese_translation']),
         'renderer_check': {'status': 'passed', 'target_sha256': '0' * 64, 'evidence': 'fixture'},
         'context_status': 'verified', 'context_evidence': 'Synthetic unit fixture'},
        {'id': rows[5]['id'], 'source_sha256': digest(rows[5]['original_english']),
         'blocked_reason': 'Unknown referent in synthetic fixture.', 'context_status': 'needs_context'}]})
    write(tmp_path / 'localization/glossary.json', {'rules': ['Fixture rule'],
          'terms': [{'english': 'Description', 'vietnamese': 'Mô tả', 'category': 'fixture'}],
          'proper_names': [{'english': 'Thomas', 'vietnamese': 'Thomas'}]})
    write(tmp_path / 'localization/character_profiles.json', {'profiles': [
        {'character': 'Thomas', 'self': 'bác', 'player': 'cháu', 'scope': 'synthetic fixture only',
         'source_ids': ['fixture.dialogue'], 'evidence': 'Synthetic unit fixture'}]})
    write(tmp_path / 'localization/qa/batches/fixture.json', {'record_ids': [rows[0]['id']]})
    return Repository(tmp_path)


def test_search_context_profiles_and_accent_folding(repo):
    assert repo.search({'q': 'mo ta'})['total'] == 1
    assert repo.search({'speaker': 'Thomas'})['total'] == 1
    assert repo.search({'batch': 'fixture'})['total'] == 1
    assert repo.search({'context': 'item_description', 'bucket': 'translate'})['total'] == 2
    assert repo.record('fixture.dialogue')['profiles'][0]['self'] == 'bác'
    assert repo.record('item.fixture.000.description')['profiles'] == []
    assert repo.glossary_search('mo ta')['terms'][0]['english'] == 'Description'
    with pytest.raises(EditorError):
        repo.search({'limit': '10000'})


def test_validation_uses_real_encoder_and_reports_independent_limits(repo):
    value = repo.validate('item.fixture.001.description', 'x' * 100)
    assert {e['code'] for e in value['errors']} == {'tokens', 'width', 'bytes'}
    value = repo.validate('item.fixture.001.description', 'Mẫu{CR}{LF}😀')
    assert any(e['code'] == 'encoding' for e in value['errors'])
    assert repo.validate('item.fixture.001.description', 'Mẫu{CR}{LF}Mô tả.')['normalized_text'].startswith('Mẫu')
    assert not repo.validate('item.fixture.001.description', 'Mẫu{LF}{CR}Mô tả.')['valid']
    assert any(e['code'] == 'empty' for e in repo.validate('item.fixture.001.description', '')['errors'])
    assert repo.validate('fixture.dialogue', 'Bác{CR}{LF}Chào.')['warnings']


def test_existing_save_keeps_source_backs_up_and_invalidates_qa(repo):
    identifier = 'item.fixture.000.description'
    path = repo.root / 'localization/vi/item_descriptions_tools.json'
    before = path.read_bytes()
    qa = repo.qa.read_bytes()
    source = deepcopy(repo.record(identifier)['source'])
    result = repo.save(identifier, 'Mẫu{CR}{LF}Đã sửa.', repo.record(identifier)['revision'])
    assert (repo.root / result['backup']).read_bytes() == before
    assert result['record']['source'] == source
    assert result['record']['translation_file'] == 'localization/vi/item_descriptions_tools.json'
    assert result['record']['translation_status'] == 'translated'
    assert result['record']['qa_stale'] and result['record']['renderer_check'] == 'stale'
    assert repo.qa.read_bytes() == qa


def test_new_translation_enters_existing_pipeline_file(repo):
    identifier = 'item.fixture.001.description'
    original = deepcopy(repo.snapshot()['originals'][identifier])
    result = repo.save(identifier, 'Mẫu{CR}{LF}Mới.', repo.record(identifier)['revision'])
    assert result['record']['translation_file'] == 'localization/vi/items.json'
    added = json.loads((repo.root / 'localization/vi/items.json').read_text())['records'][0]
    assert added == {**original, 'vietnamese_translation': 'Mẫu{CR}{LF}Mới.', 'translation_status': 'translated'}


def test_invalid_blocked_and_conflicting_edits_never_overwrite(repo):
    identifier = 'item.fixture.000.description'
    path = repo.root / repo.record(identifier)['translation_file']
    before = path.read_bytes()
    for identifier, text in [('item.fixture.000.description', 'Lost tokens.'),
                             ('fixture.unknown', 'Mẫu{CR}{LF}Không rõ.'),
                             ('item.fixture.flower.name', 'Hoa')]:
        with pytest.raises(EditorError) as error:
            repo.save(identifier, text, repo.record(identifier)['revision'])
        assert error.value.status == 422
    assert path.read_bytes() == before
    identifier = 'item.fixture.000.description'
    revision = repo.record(identifier)['revision']
    repo.save(identifier, 'Mẫu{CR}{LF}Mới.', revision)
    with pytest.raises(EditorError) as error:
        repo.save(identifier, 'Mẫu{CR}{LF}Cũ.', revision)
    assert error.value.status == 409
    assert repo.record(identifier)['vietnamese_translation'].endswith('Mới.')


def test_two_instances_merge_different_records_in_same_file(repo):
    other = Repository(repo.root)
    ids = ['item.fixture.001.description', 'item.fixture.002.description']
    revisions = [repo.record(i)['revision'] for i in ids]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(instance.save, identifier, 'Mẫu{CR}{LF}Mới.', revision)
                   for instance, identifier, revision in zip([repo, other], ids, revisions)]
        assert all(f.result()['changed'] for f in futures)
    assert {r['id'] for r in json.loads((repo.root / 'localization/vi/items.json').read_text())['records']} == set(ids)


def test_source_change_conflicts_even_when_english_is_identical(repo):
    identifier = 'item.fixture.001.description'
    revision = repo.record(identifier)['revision']
    catalog = json.loads(repo.catalog.read_text())
    catalog['records'][2]['source']['reference'] = 'Changed fixture provenance'
    write(repo.catalog, catalog)
    with pytest.raises(EditorError) as error:
        repo.save(identifier, 'Mẫu{CR}{LF}Mới.', revision)
    assert error.value.status == 409


def test_csv_is_filtered_and_spreadsheet_safe(repo):
    catalog = json.loads(repo.catalog.read_text())
    catalog['records'][2]['original_english'] = '=SYNTHETIC_FORMULA()'
    write(repo.catalog, catalog)
    content = repo.export_csv({'q': 'SYNTHETIC_FORMULA'})
    assert content.startswith(b'\xef\xbb\xbf')
    assert "'=SYNTHETIC_FORMULA()" in content.decode('utf-8-sig')
    assert content.decode('utf-8-sig').count('\r\n') == 2


def test_http_auth_origin_write_contract_and_static_allowlist(repo):
    server = make_server(repo, port=0, token='synthetic-test-session')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(path, body=None, token=True, extra=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
        headers = {'Authorization': 'Bearer synthetic-test-session'} if token else {}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        headers.update(extra or {})
        connection.request('POST' if body is not None else 'GET', path,
                           json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result
    try:
        assert request('/api/meta', token=False)[0] == 401
        assert request('/api/meta', extra={'Origin': 'https://untrusted.invalid'})[0] == 403
        assert request('/api/meta', extra={'Host': 'untrusted.invalid'})[0] == 403
        assert request('/localization/en/catalog.json')[0] == 404
        assert request('/../translation_workbench.py')[0] == 404
        assert request('/')[0] == 200
        status, body, headers = request('/api/meta')
        assert status == 200 and json.loads(body)['total'] == 6
        assert headers['Cache-Control'] == 'no-store'
        assert 'frame-ancestors' in headers['Content-Security-Policy']
        identifier = 'item.fixture.001.description'
        revision = repo.record(identifier)['revision']
        assert request('/api/save', {'id': identifier, 'text': 'Mẫu{CR}{LF}Mới.', 'revision': revision,
                                     'translation_status': 'reviewed'})[0] == 400
        assert request('/api/save', {'id': identifier, 'text': 'Broken', 'revision': revision})[0] == 422
        assert request('/api/save', {'id': identifier, 'text': 'Mẫu{CR}{LF}Mới.', 'revision': revision})[0] == 200
        assert request('/api/save', {'id': identifier, 'text': 'Mẫu{CR}{LF}Cũ.', 'revision': revision})[0] == 409
        assert request('/api/export.csv?q=' + quote('Mới'))[0] == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
