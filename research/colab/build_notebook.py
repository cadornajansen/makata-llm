"""Bundle only reviewed research source into a self-contained Colab notebook."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "research/evaluate.py", "research/protocol.py", "research/preflight.py",
    "research/baseline-plan.json", "research/requirements.txt", "research/requirements-colab.txt",
    "research/fixtures/development.json", "research/tests/test_evaluation.py",
    "research/tests/test_colab.py", "research/colab/run.py",
)


def cell(kind: str, source: str) -> dict[str, object]:
    value: dict[str, object] = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    return value


def build() -> Path:
    files = {name: (ROOT / name).read_bytes() for name in FILES}
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    files["bundle-manifest.json"] = json.dumps({
        "files_sha256": hashes,
        "git_reference": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "notice": "Includes the current local research changes; hashes identify the exact bundled source.",
    }, sort_keys=True, indent=2).encode()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    payload = stream.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    bootstrap = f'''import base64, hashlib, io, json, os, pathlib, subprocess, sys, uuid, zipfile

# This allowlisted snapshot includes unpushed fixes, not your entire repository.
PAYLOAD = {base64.b64encode(payload).decode()!r}
BUNDLE_SHA256 = {digest!r}
data = base64.b64decode(PAYLOAD)
assert hashlib.sha256(data).hexdigest() == BUNDLE_SHA256
ROOT = pathlib.Path('/content') / ('makata-' + BUNDLE_SHA256[:12])
ROOT.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    manifest = json.loads(archive.read('bundle-manifest.json'))
    assert set(archive.namelist()) == set(manifest['files_sha256']) | {{'bundle-manifest.json'}}
    for name, expected in manifest['files_sha256'].items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT.resolve())
        content = archive.read(name)
        assert hashlib.sha256(content).hexdigest() == expected
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == content, 'Existing source differs; start a fresh runtime.'
        else:
            target.write_bytes(content)
(ROOT / 'bundle-manifest.json').write_text(json.dumps(manifest, indent=2))
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
SESSION = ROOT / 'research/runs' / ('colab-' + uuid.uuid4().hex[:12])
SESSION.mkdir(parents=True)
subprocess.run(['nvidia-smi'], check=True)
print('Source verified:', BUNDLE_SHA256)
print('Result session:', SESSION)
'''
    setup = '''# Research packages stay separate from Colab's changing preinstalled environment.
subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'uv==0.11.28'], check=True)
UV = [sys.executable, '-m', 'uv']
ENV = ROOT / 'research/.venv'
PY = ENV / 'bin/python'
if not PY.exists():
    subprocess.run(UV + ['venv', '--python', '3.12.13', str(ENV)], check=True)
UPSTREAM = ROOT / 'research/.cache/filbench-lighteval'
if not UPSTREAM.exists():
    UPSTREAM.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'clone', 'https://github.com/filbench/lighteval.git', str(UPSTREAM)], check=True)
subprocess.run(['git', '-C', str(UPSTREAM), 'checkout', '7ad52795d7d218d4679f93a019b58dde4b749c5b'], check=True)
subprocess.run(UV + ['pip', 'sync', '--python', str(PY), '--torch-backend', 'cu126', 'requirements-colab.txt'],
               cwd=ROOT / 'research', check=True)
subprocess.run(UV + ['pip', 'check', '--python', str(PY)], check=True)
'''
    helpers = '''import shutil

def archive_results():
    # Includes manifests/logs/results, never model weights, caches, or environments.
    destination = '/content/makata-results-' + SESSION.name
    shutil.make_archive(destination, 'zip', root_dir=SESSION)
    return destination + '.zip'

def stage(command, candidate=0):
    log = SESSION / (command + '-' + str(candidate) + '.log')
    try:
        with log.open('w') as output:
            result = subprocess.run([str(PY), str(ROOT / 'research/colab/run.py'), command,
                                     '--session', str(SESSION), '--candidate', str(candidate)],
                                    cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=14400)
        print(log.read_text()[-6000:])
        result.check_returncode()
    finally:
        print('Local runtime archive:', archive_results())

def download_results():
    from google.colab import files
    files.download(archive_results())
'''
    cells = [
        cell("markdown", """# Makata: verified Tagalog comprehension baselines on free Colab

Use **Runtime → Change runtime type → T4 GPU** (or another available free NVIDIA GPU).
Use only the free tier. No AWS, API credits, paid subscriptions, Drive mount, or public uploads are used.
GPU allocation and session lifetime are not guaranteed. Run cells in order and remain present.

This notebook embeds the current research source, including unpushed fixes. It preserves the exact
FilBench/model/tokenizer/dataset pins, zero-shot prompts, **float32** scoring, batch one and no truncation.
CUDA replaces CPU explicitly; TF32 and quantization are disabled. It freezes a separate GPU execution
profile before candidate weights or benchmark examples load. All results remain private to this runtime
until **you download them**. A terminated runtime can lose undownloaded artifacts; incomplete runs do not count.

First validate the environment and both candidates on 20 **synthetic development questions**.
Only the later baseline cells access the full 900-question held-out dataset. Do not tune against those results.
"""),
        cell("markdown", "## 1. Verify and unpack the reviewed source; check GPU assignment"), cell("code", bootstrap),
        cell("markdown", "## 2. Install the isolated pinned Linux/CUDA environment\nDownloads several GB of dependencies. The notebook kernel is not the research interpreter."), cell("code", setup),
        cell("markdown", "## 3. Run offline protocol tests; freeze the GPU execution profile"),
        cell("code", "subprocess.run([str(PY), '-m', 'unittest', 'discover', '-s', 'research/tests', '-v'], cwd=ROOT, check=True)\n" + helpers + "\nstage('freeze')\n"),
        cell("markdown", "## 4. Verify Qwen and Sailor2 on development data only\nDownloads each pinned checkpoint. Candidate runs execute in separate processes to release GPU memory."),
        cell("code", "stage('smoke', 0)\nstage('smoke', 1)\ndownload_results()\n"),
        cell("markdown", "## 5. Qwen: full 900-question baseline\nProceed only if both smoke checks succeeded. A four-hour timeout applies. No partial subset or CPU fallback is allowed."),
        cell("code", "stage('evaluate', 0)\ndownload_results()\n"),
        cell("markdown", "## 6. Sailor2: full 900-question baseline\nKeep the first downloaded archive before starting this run."),
        cell("code", "stage('evaluate', 1)\ndownload_results()\n"),
        cell("markdown", "## 7. Confirm evidence and retain the final archive\nA successful milestone requires two verified 900-question runs, not the synthetic pilot scores."),
        cell("code", """for index in (0, 1):
    marker = json.loads((SESSION / ('baseline-' + str(index) + '.json')).read_text())
    directory = pathlib.Path(marker['directory'])
    saved = json.loads((directory / 'manifest.json').read_text())
    metrics = json.loads((directory / 'metrics.json').read_text())
    assert saved['status'] == 'complete' and saved['sample_count'] == 900
    print(saved['configuration']['model'], metrics['official_task_metrics'])
download_results()
print('Download finished? Then use Runtime → Disconnect and delete runtime to release the GPU.')
"""),
    ]
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "accelerator": "GPU", "colab": {"name": "Makata — Tagalog comprehension baselines.ipynb"},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "makata": {"bundle_sha256": digest, "files_sha256": hashes},
    }, "cells": cells}
    for index, value in enumerate(cells):
        value["id"] = f"makata-{index:02d}"
    output = Path(__file__).with_name("makata-baselines.ipynb")
    output.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(build())
