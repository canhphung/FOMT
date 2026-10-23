"""The baseline gate must detect pixel changes, including alpha-only changes."""
from PIL import Image
import pytest

from fomt_text import FormatError
import platform_check as gate


def test_rgba_comparison_detects_alpha_and_writes_diff(tmp_path):
    before, after, diff = [tmp_path / name for name in ('before.png', 'after.png', 'diff.png')]
    image = Image.new('RGBA', (240, 160), (10, 20, 30, 255))
    image.save(before, compress_level=0)
    image.save(after, compress_level=9)
    assert gate.compare_images(before, after, diff)['changed_pixels'] == 0
    assert not diff.exists()
    image.putpixel((7, 3), (10, 20, 30, 254))
    image.save(after)
    assert gate.compare_images(before, after, diff)['changed_pixels'] == 1
    assert Image.open(diff).getpixel((7, 3)) == (255, 0, 255)


def test_wrong_framebuffer_size_is_rejected(tmp_path):
    a, b = tmp_path / 'a.png', tmp_path / 'b.png'
    Image.new('RGB', (240, 160)).save(a)
    Image.new('RGB', (241, 160)).save(b)
    with pytest.raises(FormatError, match='size changed'):
        gate.compare_images(a, b, tmp_path / 'diff.png')


def test_source_and_reference_locks_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, 'ROOT', tmp_path)
    source = tmp_path / 'source.py'
    source.write_bytes(b'original')
    reference = tmp_path / 'reference.png'
    Image.new('RGB', (240, 160)).save(reference)
    baseline = {'locked_files': [{'path': source.name, 'sha256': gate.digest(source.read_bytes())}],
                'images': [{'reference': reference.name, 'sha256': gate.digest(reference.read_bytes())}]}
    gate.check_locks(baseline)
    source.write_bytes(b'changed')
    with pytest.raises(FormatError, match='platform source changed'):
        gate.check_locks(baseline)
    source.write_bytes(b'original')
    Image.new('RGB', (240, 160), 'red').save(reference)
    with pytest.raises(FormatError, match='golden reference changed'):
        gate.check_locks(baseline)


def test_failed_retry_cannot_leave_green_report(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, 'OUT', tmp_path / 'out')
    gate.save_report({'status': 'passed'})
    def fail(*args):
        raise FormatError('broken build')
    monkeypatch.setattr(gate, 'run', fail)
    monkeypatch.setattr('sys.argv', ['platform_check.py', '--base-rom', str(tmp_path / 'input.gba')])
    with pytest.raises(SystemExit) as error:
        gate.main()
    assert error.value.code == 1
    assert '"status": "failed"' in (gate.OUT / 'report.json').read_text()
