#!/usr/bin/env python3
"""Rebuild twice, verify the release IPS, and optionally replay golden UI scenes.

Never updates golden files or the release patch. Run from any directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

from fomt_text import FormatError, verified_rom
import ips

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'localization/platform_baseline.json'
OUT = ROOT / 'build/platform-check'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise FormatError(message)


def compare_images(reference, candidate, diff_path):
    """Compare decoded RGBA pixels, independent of PNG compression/metadata."""
    with Image.open(reference) as im:
        expected = im.convert('RGBA')
    with Image.open(candidate) as im:
        actual = im.convert('RGBA')
    require(actual.size == expected.size, f'image size changed: {candidate}')
    # RGB diff alone would miss an alpha-only regression.
    delta = ImageChops.difference(expected, actual)
    changed = sum(a != b for a, b in zip(expected.get_flattened_data(), actual.get_flattened_data()))
    if changed:
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        mask = Image.new('RGB', actual.size)
        mask.putdata([(255, 0, 255) if any(px) else (0, 0, 0)
                      for px in delta.get_flattened_data()])
        mask.save(diff_path)
    return {'changed_pixels': changed, 'size': list(actual.size)}


def check_locks(baseline):
    for row in baseline['locked_files']:
        require(digest((ROOT / row['path']).read_bytes()) == row['sha256'],
                f'platform source changed: {row["path"]}; review the baseline explicitly')
    for row in baseline['images']:
        path = ROOT / row['reference']
        require(digest(path.read_bytes()) == row['sha256'],
                f'golden reference changed: {row["reference"]}')
        with Image.open(path) as im:
            require(list(im.size) == [240, 160], f'golden is not native GBA size: {path}')


def command(name, args, env=None):
    print(f'Running {name}', flush=True)
    log = OUT / 'logs' / (name + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w') as stream:
        result = subprocess.run(args, cwd=ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT)
    require(result.returncode == 0, f'{name} failed; see {log.relative_to(ROOT)}')
    return str(log.relative_to(ROOT))


def run(base_path, backends):
    baseline = json.loads(BASELINE.read_text())
    require(baseline['schema_version'] == 1, 'unsupported platform baseline')
    base = verified_rom(base_path)
    require(not base_path.resolve().is_relative_to(OUT.resolve()),
            'base ROM must live outside build/platform-check')
    check_locks(baseline)
    release = json.loads((ROOT / 'patches/manifest.json').read_text())
    report = {'schema_version': 1, 'status': 'running',
              'baseline_sha256': digest(BASELINE.read_bytes()),
              'source_sha1': hashlib.sha1(base).hexdigest(),
              'visual_review': baseline['visual_review'],
              'limitations': baseline['limitations'], 'emulators': {}}
    # Always replace a previous success report before starting work.
    save_report(report)
    env = {**os.environ, 'FOMT_ROM': str(base_path)}
    junit = OUT / 'pytest.xml'
    report['pytest_log'] = command('pytest', [sys.executable, '-m', 'pytest', '-q',
                                            f'--junitxml={junit}'], env)
    suites = ET.parse(junit).getroot().iter('testsuite')
    totals = {key: 0 for key in ('tests', 'failures', 'errors', 'skipped')}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key, 0))
    report['pytest'] = {'passed': totals['tests'] - totals['failures'] - totals['errors'] - totals['skipped'],
                        'failed': totals['failures'] + totals['errors'], 'skipped': totals['skipped']}
    require(report['pytest']['passed'] > 0 and report['pytest']['skipped'] == 0,
            'platform gate requires the complete ROM-backed suite without skipped tests')
    builds = []
    for index in (1, 2):
        dest = OUT / f'build-{index}'
        command(f'build-{index}', [sys.executable, 'tools/text_inserter.py', str(base_path),
                '--output', str(dest / 'game.gba'), '--patch', str(dest / 'game.ips'),
                '--report', str(dest / 'insertion.json')])
        builds.append(((dest / 'game.gba').read_bytes(), (dest / 'game.ips').read_bytes()))
    require(builds[0] == builds[1], 'repeated builds differ')
    target, patch = builds[0]
    require(digest(target) == release['target_sha256'], 'build differs from release manifest')
    require(digest(patch) == release['patch_sha256'], 'built IPS differs from release manifest')
    shipped_patch = (ROOT / 'patches/fomt-vi-demo.ips').read_bytes()
    require(shipped_patch == patch, 'release IPS differs from reproducible build')
    require(ips.apply(base, shipped_patch) == target, 'release IPS round trip failed')
    report.update(target_sha256=digest(target), patch_sha256=digest(patch),
                  repeated_builds_identical=True, release_ips_round_trip=True,
                  locked_files_checked=len(baseline['locked_files']),
                  golden_references_checked=len(baseline['images']))
    rom = OUT / 'build-1/game.gba'
    for backend in backends:
        spec = baseline['emulators'][backend]
        library = ROOT / spec['library']
        require(library.is_file(), f'missing {library}; see docs/PLATFORM_BASELINE.md')
        fixture = ROOT / baseline['save_fixture']['path']
        require(digest(fixture.read_bytes()) == baseline['save_fixture']['sha256'],
                'day-2 SRAM fixture changed')
        result = {'library_sha256': digest(library.read_bytes()), 'suites': {}, 'images': []}
        for suite, script in [('full', 'emulator_smoke'), ('new-game', 'new_game_smoke'),
                              ('start', 'start_menu_smoke'), ('date', 'date_ui_smoke'),
                              ('items', 'item_batch_smoke'), ('item-audit', 'item_audit'),
                              ('item-ui', 'item_ui_smoke'), ('npc-daily', 'npc_daily_smoke'), ('object-labels', 'object_labels_smoke'), ('interaction-hints', 'interaction_hints_smoke')]:
            dest = OUT / backend / suite
            args = [sys.executable, f'tools/{script}.py', str(rom), '--library', str(library)]
            if suite != 'start':
                args += ['--base-rom', str(base_path)]
            if suite in ('start', 'date', 'item-ui', 'object-labels', 'interaction-hints'):
                args += ['--sram', str(fixture)]
            if suite == 'items':
                args += ['--output', str(dest / 'report.json')]
            else:
                args += ['--output-dir', str(dest)]
            command(f'{backend}-{suite}', args)
            data = json.loads((dest / 'report.json').read_text())
            require(data['target_sha256'] == report['target_sha256'], 'stale emulator report')
            require(data['status'].startswith('passed'), f'{suite} did not pass')
            result['suites'][suite] = {'report': str((dest / 'report.json').relative_to(ROOT)),
                                       'sha256': digest((dest / 'report.json').read_bytes())}
        for row in baseline['images']:
            comparison = compare_images(ROOT / row['reference'],
                    OUT / backend / row['suite'] / row['capture'],
                    OUT / backend / 'diff' / f'{row["suite"]}-{row["capture"]}')
            result['images'].append({'reference': row['reference'], **comparison})
        report['emulators'][backend] = result
        save_report(report)
        require(all(i['changed_pixels'] == 0 for i in result['images']),
                f'{backend}: golden pixels differ; inspect build/platform-check/{backend}/diff')
    report['status'] = 'passed'
    report['emulator_replay_run'] = bool(backends)
    save_report(report)
    return report


def save_report(report):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-rom', type=Path, required=True)
    parser.add_argument('--emulators', nargs='+', choices=['0.10.5', 'dev'], default=[])
    args = parser.parse_args()
    if args.base_rom.resolve().is_relative_to(OUT.resolve()):
        parser.error('base ROM must live outside build/platform-check')
    try:
        report = run(args.base_rom.resolve(), args.emulators)
    except (OSError, ValueError, KeyError) as exc:
        # A failed retry must not leave an earlier green report in place.
        save_report({'schema_version': 1, 'status': 'failed', 'error': str(exc)})
        parser.exit(1, f'error: {exc}\n')
    print(json.dumps({k: report[k] for k in ('status', 'target_sha256',
                     'golden_references_checked', 'emulator_replay_run')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
