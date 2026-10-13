"""Create an output-free notebook from an explicit, training-only source allowlist."""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "research/qlora_smoke.py", "research/qlora_training.py", "research/qlora-smoke-plan.json",
    "research/requirements-qlora-colab.in", "research/requirements-qlora-colab.txt",
    "research/tests/test_qlora_smoke.py",
)


def cell(kind: str, text: str) -> dict[str, object]:
    item: dict[str, object] = {"cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        item.update(execution_count=None, outputs=[])
    return item


def build() -> Path:
    payload = io.BytesIO()
    contents = {name: (ROOT / name).read_bytes() for name in FILES}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in contents.items()}
    contents["source-manifest.json"] = (json.dumps({"sha256": hashes}, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, value)
    encoded = base64.b64encode(payload.getvalue()).decode()
    digest = hashlib.sha256(payload.getvalue()).hexdigest()
    bootstrap = f'''import base64, hashlib, io, json, os, pathlib, subprocess, sys, uuid, zipfile

# Select Runtime > Change runtime type > T4 GPU. Use the free standard runtime.
gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], text=True)
assert len(gpu.strip().splitlines()) == 1 and 'T4' in gpu, 'One free T4 required. No CPU/paid fallback.'
print(gpu)
payload = base64.b64decode({encoded!r})
assert hashlib.sha256(payload).hexdigest() == {digest!r}
ROOT = pathlib.Path('/content') / ('makata-qlora-' + {digest[:12]!r})
ROOT.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    receipts = json.loads(archive.read('source-manifest.json'))['sha256']
    assert set(archive.namelist()) == set(receipts) | {{'source-manifest.json'}}
    for name, expected in receipts.items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT.resolve())
        data = archive.read(name)
        assert hashlib.sha256(data).hexdigest() == expected
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
os.environ.update({{'HF_HUB_DISABLE_TELEMETRY':'1', 'WANDB_DISABLED':'true', 'TOKENIZERS_PARALLELISM':'false'}})
os.environ['HF_HOME'] = str(ROOT / 'research/.cache/huggingface')
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'uv==0.11.28'], check=True)
ENV = ROOT / 'research/.cache/qlora-venv'
if not ENV.exists():
    subprocess.run(['uv', 'venv', '--python', '3.12.13', str(ENV)], check=True)
PYTHON = ENV / 'bin/python'
subprocess.run(['uv', 'pip', 'sync', '--python', str(PYTHON), '--torch-backend', 'cu126',
                str(ROOT / 'research/requirements-qlora-colab.txt')], check=True)
subprocess.run(['uv', 'pip', 'check', '--python', str(PYTHON)], check=True)
SESSION = ROOT / 'research/runs' / ('smoke-' + uuid.uuid4().hex[:12])
SESSION.mkdir(parents=True)
CLI = ROOT / 'research/qlora_smoke.py'
def run(*arguments):
    command = [str(PYTHON), '-X', 'utf8', str(CLI), *map(str, arguments)]
    with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
        for line in process.stdout:
            print(line, end='', flush=True)
        if process.wait():
            raise subprocess.CalledProcessError(process.returncode, command)
run('preflight', '--output', SESSION / 'preflight')
print('Isolated environment and T4 verified. Source snapshot:', {digest!r})
'''
    upload = '''from google.colab import files
UPLOAD = SESSION / 'private-inputs.zip'
sidebar_upload = pathlib.Path('/content/private-inputs.zip')
if sidebar_upload.exists():
    # Optional fallback: Files > Upload to session storage (no Drive mount).
    UPLOAD.write_bytes(sidebar_upload.read_bytes())
else:
    uploaded = files.upload()  # Select only the prepared private-inputs.zip.
    assert len(uploaded) == 1, 'Upload exactly one private input bundle.'
    UPLOAD.write_bytes(next(iter(uploaded.values())))
    del uploaded
INPUTS = SESSION / 'inputs'
run('unpack', '--archive', UPLOAD, '--output', INPUTS)
run('tokenize', '--inputs', INPUTS, '--output', SESSION / 'tokenization')
print('Exactly 16 frozen training records verified; no validation or benchmark data loaded.')
'''
    checks = '''subprocess.run([str(PYTHON), '-X', 'utf8', '-m', 'unittest', 'discover',
                '-s', 'research/tests', '-p', 'test_qlora_smoke.py', '-v'], cwd=ROOT, check=True)
run('integration', '--output', SESSION / 'cpu-integration')
'''
    training = '''RUN = SESSION / 'gpu-run'
RESULT_ZIP = SESSION / 'qlora-smoke-results.zip'
try:
    # Each command starts a new interpreter. Training exits before adapter reload.
    run('train', '--inputs', INPUTS, '--output', RUN)
    run('reload', '--output', RUN)
    run('verify', '--output', RUN)
finally:
    # Failures keep their incomplete manifest. An interrupted cell can use the next cell.
    if (RUN / 'run-manifest.json').exists() and not RESULT_ZIP.exists():
        run('archive', '--output', RUN, '--archive', RESULT_ZIP)
'''
    download = '''from google.colab import files
if not RESULT_ZIP.exists() and (RUN / 'run-manifest.json').exists():
    run('archive', '--output', RUN, '--archive', RESULT_ZIP)
print(json.loads((RUN / 'run-manifest.json').read_text())['status'])
files.download(str(RESULT_ZIP))
# Download before disconnecting. No Drive mount, hub upload, or paid service is used.
'''
    notebook = {"nbformat": 4, "nbformat_minor": 5,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                             "accelerator": "GPU", "colab": {"name": "Makata — 20-update QLoRA smoke test.ipynb", "provenance": []}},
                "cells": [
                    cell("markdown", "# Makata: first QLoRA engineering smoke test\n\nExactly 20 optimizer updates on 16 provisional Aya training examples. This does not establish improved comprehension, native-speaker review, legal clearance, or completion of Makata-v0.1.\n\nUse **free T4 / standard RAM**. Stop if Colab asks for payment or cannot allocate a T4. Run cells in order. The notebook embeds source only; upload the private input ZIP separately. No evaluation data is needed.\n"),
                    cell("markdown", "## 1. Check hardware and install the separate pinned environment\nMay take several minutes. Setup time is excluded from training measurements.\n"),
                    cell("code", bootstrap),
                    cell("markdown", "## 2. Upload and verify the private inputs\nChoose the ZIP produced by `qlora_smoke.py prepare`. The source text remains unchanged.\n"),
                    cell("code", upload),
                    cell("markdown", "## 3. Test masking, data guards, and the training-library integration\nThe tiny CPU model checks code paths; it is not a GPU quantization test.\n"),
                    cell("code", checks),
                    cell("markdown", "## 4. Train, save, and reload in a fresh process\nOnly a finite 20-update run with matching reloaded adapter tensors and probe logits receives `complete` status. Do not repeatedly rerun to cherry-pick losses.\n"),
                    cell("code", training),
                    cell("markdown", "## 5. Download local evidence\nKeep results private. Back on your computer, import the ZIP with `qlora_smoke.py import --archive ... --output ...`. A partial run remains incomplete.\n"),
                    cell("code", download),
                ]}
    for index, item in enumerate(notebook["cells"]):
        item["id"] = f"qlora-{index:02d}"
        if item["cell_type"] == "code":
            compile("".join(item["source"]), f"cell-{index}", "exec")
    path = ROOT / "research/colab/makata-qlora-smoke.ipynb"
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(build())
