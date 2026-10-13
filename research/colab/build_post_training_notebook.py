"""Package the unchanged baseline evaluator and isolated checkpoint91 extension."""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FILES = ("evaluate.py", "protocol.py", "preflight.py", "baseline-plan.json", "requirements.txt",
         "requirements-colab.txt", "colab/run.py", "fixtures/development.json", "post_training.py",
         "post-training-plan.json", "requirements-post-training-colab.txt", "tests/test_post_training.py")


def build() -> Path:
    contents = {"research/" + name: (ROOT / "research" / name).read_bytes() for name in FILES}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    contents["source-manifest.json"] = (json.dumps(hashes, sort_keys=True) + "\n").encode()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    payload = stream.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    input_digest = hashlib.sha256((ROOT / "research/runs/post-training-inputs-v1/private-adapter.zip").read_bytes()).hexdigest()
    bootstrap = f'''import base64, hashlib, io, json, os, pathlib, subprocess, sys, zipfile
data = base64.b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(data).hexdigest() == {digest!r}
ROOT = pathlib.Path('/content/makata-post-{digest[:12]}')
ROOT.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    hashes = json.loads(archive.read('source-manifest.json'))
    assert set(archive.namelist()) == set(hashes) | {{'source-manifest.json'}}
    for name, expected in hashes.items():
        content = archive.read(name)
        assert hashlib.sha256(content).hexdigest() == expected
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == content
        else:
            target.write_bytes(content)
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
subprocess.run(['nvidia-smi'], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'uv==0.11.28'], check=True)
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
subprocess.run(UV + ['pip', 'sync', '--python', str(PY), '--torch-backend', 'cu126', 'requirements-post-training-colab.txt'], cwd=ROOT / 'research', check=True)
subprocess.run(UV + ['pip', 'check', '--python', str(PY)], check=True)
SESSION = ROOT / 'research/runs/post-training'
INPUTS = ROOT / 'research/runs/adapter-inputs'
RESULT_ZIP = ROOT / 'makata-post-training-results.zip'
def run(command, *args):
    subprocess.run([str(PY), '-X', 'utf8', str(ROOT / 'research/post_training.py'), command, *map(str, args)], cwd=ROOT, check=True)
print('Frozen source SHA256:', {digest!r})
'''
    upload = f'''# Upload private-adapter.zip with Colab's Files pane -> Upload to session storage.
UPLOAD = pathlib.Path('/content/private-adapter.zip')
assert UPLOAD.is_file(), 'Upload the adapter bundle through the Files pane first.'
assert hashlib.sha256(UPLOAD.read_bytes()).hexdigest() == {input_digest!r}
run('unpack', '--archive', UPLOAD, '--output', INPUTS)
subprocess.run([str(PY), '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'research/tests', '-p', 'test_post_training.py', '-v'], cwd=ROOT, check=True)
run('integration', '--output', ROOT / 'research/runs/tiny-integration')
run('freeze', '--inputs', INPUTS, '--output', SESSION)
print('Ready: exact adapter91; float32; batch1; no benchmark accessed.')
'''
    execute = '''# This starts exactly one guarded subprocess. Do not rerun this cell.
assert not (SESSION / 'attempt.json').exists(), 'An evaluation was already attempted.'
assert 'PROCESS' not in globals(), 'Evaluation process already created.'
LOG = (SESSION / 'evaluation.log').open('w')
PROCESS = subprocess.Popen([str(PY), '-X', 'utf8', str(ROOT / 'research/post_training.py'), 'evaluate', '--inputs', str(INPUTS), '--output', str(SESSION)], cwd=ROOT, stdout=LOG, stderr=subprocess.STDOUT)
print('Evaluation PID:', PROCESS.pid)
print('One full900-question run started. Monitor with the next cell; never train or tune here.')
'''
    monitor = '''code = PROCESS.poll()
print('Running' if code is None else 'Process exit: ' + str(code))
print((SESSION / 'evaluation.log').read_text(errors='replace')[-4500:])
'''
    finish = '''assert PROCESS.poll() is not None, 'Still running; use the monitor cell.'
LOG.close()
try:
    assert PROCESS.returncode == 0, 'Incomplete run; preserve evidence, do not automatically retry.'
    run('verify', '--output', SESSION)
finally:
    if not RESULT_ZIP.exists():
        run('archive', '--output', SESSION, '--archive', RESULT_ZIP)
print('Result archive:', RESULT_ZIP)
'''
    download = '''from google.colab import files
assert RESULT_ZIP.exists()
files.download(str(RESULT_ZIP))
print('Retain the runtime until local import and paired comparison pass.')
'''
    sections = [
        ("markdown", "# Makata Milestone4: checkpoint91 post-training evaluation\n\nOne complete900-question FilBench Belebele evaluation. Unchanged FP32 base plus frozen LoRA; no quantization, training, prompt changes or checkpoint selection. Free T4 only; stop at any payment requirement. The32 instruction-following tasks remain separate and unscored.\n"),
        ("markdown", "## 1. Verify source and install the pinned evaluation environment\nSelect a free T4 first. No benchmark data loads in this section.\n"), ("code", bootstrap),
        ("markdown", "## 2. Upload adapter, run offline checks and freeze\nUse Files → Upload to session storage for private-adapter.zip. No training data or retained benchmark records are uploaded.\n"), ("code", upload),
        ("markdown", "## 3. Start the single authorized benchmark run\nExpect roughly35–60 minutes on T4. The first synthetic-logit check proves disabled-adapter/base equivalence before test-set access.\n"), ("code", execute),
        ("markdown", "## 4. Monitor safely\nThis cell only reads process status/logs and may be rerun.\n"), ("code", monitor),
        ("markdown", "## 5. Verify and archive\nRun only after the process exits. Failed attempts remain incomplete.\n"), ("code", finish),
        ("markdown", "## 6. Download evidence\nImport locally, then compare against the retained base predictions. Never publish the adapter or raw benchmark examples.\n"), ("code", download)]
    cells = []
    for index, (kind, content) in enumerate(sections):
        cell = {"cell_type": kind, "id": f"post-{index:02d}", "metadata": {}, "source": content.splitlines(keepends=True)}
        if kind == "code":
            compile(content, f"post-cell-{index}", "exec")
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    notebook = {"nbformat": 4, "nbformat_minor": 5, "cells": cells,
                "metadata": {"kernelspec": {"display_name": "Python3", "language": "python", "name": "python3"},
                             "accelerator": "GPU", "makata": {"source_sha256": digest, "files_sha256": hashes}}}
    path = Path(__file__).with_name("makata-post-training.ipynb")
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(build())
