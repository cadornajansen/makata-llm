"""Build a separate output-free notebook; never regenerate the historical smoke notebook."""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "research/qlora_full.py", "research/qlora_full_runtime.py", "research/qlora-full-authorization.json",
    "research/aya-training-proposal.json", "research/qlora_smoke.py", "research/qlora_training.py",
    "research/qlora-smoke-plan.json", "research/requirements-qlora-colab.txt",
    "research/tests/test_qlora_full.py",
)


def build() -> Path:
    contents = {name: (ROOT / name).read_bytes() for name in FILES}
    contents["source-manifest.json"] = (json.dumps({"sha256": {
        name: hashlib.sha256(value).hexdigest() for name, value in contents.items()}}, sort_keys=True) + "\n").encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, value)
    digest = hashlib.sha256(buffer.getvalue()).hexdigest()
    encoded = base64.b64encode(buffer.getvalue()).decode()
    original = json.loads((ROOT / "research/colab/makata-qlora-smoke.ipynb").read_text(encoding="utf-8"))
    bootstrap = "".join(original["cells"][2]["source"])
    bootstrap = re.sub(r"base64.b64decode\('[^']+'\)", f"base64.b64decode('{encoded}')", bootstrap)
    bootstrap = re.sub(r"hexdigest\(\) == '[0-9a-f]+'", f"hexdigest() == '{digest}'", bootstrap)
    bootstrap = re.sub(r"'makata-qlora-' \+ '[0-9a-f]+'", f"'makata-full-' + '{digest[:12]}'", bootstrap)
    bootstrap = re.sub(r"Source snapshot:', '[0-9a-f]+'", f"Source snapshot:', '{digest}'", bootstrap)
    bootstrap = bootstrap.replace("('smoke-' + uuid", "('full-' + uuid")
    bootstrap = bootstrap.replace("research/qlora_smoke.py", "research/qlora_full.py")
    upload = '''from google.colab import files
uploaded = files.upload()  # Only private-full-inputs.zip, never the evaluation packet.
assert len(uploaded) == 1
UPLOAD = SESSION / 'private-full-inputs.zip'
UPLOAD.write_bytes(next(iter(uploaded.values())))
del uploaded
INPUTS = SESSION / 'inputs'
run('unpack', '--archive', UPLOAD, '--output', INPUTS)
run('tokenize', '--inputs', INPUTS, '--output', SESSION / 'tokenization')
print('363 training records and66 provisional validation diagnostics only. No evaluation tasks.')
'''
    checks = '''subprocess.run([str(PYTHON), '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'research/tests',
                '-p', 'test_qlora_full.py', '-v'], cwd=ROOT, check=True)
run('integration', '--output', SESSION / 'cpu-integration')
'''
    training = '''RUN = SESSION / 'gpu-run'
RESULT_ZIP = SESSION / 'makata-v01-full-results.zip'
try:
    run('train', '--inputs', INPUTS, '--output', RUN)
    run('reload', '--output', RUN)  # Fresh interpreter; selects final91 only.
    run('verify', '--output', RUN)
finally:
    if (RUN / 'run-manifest.json').exists() and not RESULT_ZIP.exists():
        run('archive', '--output', RUN, '--archive', RESULT_ZIP)
'''
    download = '''from google.colab import files
if not RESULT_ZIP.exists() and (RUN / 'run-manifest.json').exists():
    run('archive', '--output', RUN, '--archive', RESULT_ZIP)
print('Archive bytes:', RESULT_ZIP.stat().st_size)
print(json.loads((RUN / 'run-manifest.json').read_text())['status'])
files.download(str(RESULT_ZIP))
# Keep the runtime until local import independently verifies both checkpoints and final reload.
'''
    sections = [
        ("markdown", "# Makata-v0.1: authorized internal Aya-only experiment\n\n363 provisional training records; one epoch,91 optimizer updates; checkpoints50/91. Free T4 only. 283 records lack individual content review. No native-speaker/legal clearance or validated capability claim. The66 validation records are provisional diagnostics only. No benchmark or32-item evaluation tasks are uploaded.\n"),
        ("markdown", "## 1. Pinned source, environment and free-T4 preflight\nSetup is excluded from training timing. Stop on payment or unavailable free T4.\n"),
        ("code", bootstrap),
        ("markdown", "## 2. Upload the private full-run inputs\nChoose only the bundle produced by qlora_full.py prepare.\n"),
        ("code", upload),
        ("markdown", "## 3. Offline safeguards and tiny CPU integration\nVerifies the final three-example gradient accumulation and checkpoint/reload APIs.\n"),
        ("code", checks),
        ("markdown", "## 4. One epoch, checkpoints and fresh-process final reload\nNo automatic resume, benchmark access or best-checkpoint selection. Failures retain incomplete evidence.\n"),
        ("code", training),
        ("markdown", "## 5. Download and locally verify before disconnecting\nUse qlora_full.py import on the laptop. Never publish the archive or adapter.\n"),
        ("code", download),
    ]
    cells = []
    for index, (kind, text) in enumerate(sections):
        item = {"cell_type": kind, "id": f"full-{index:02d}", "metadata": {}, "source": text.splitlines(keepends=True)}
        if kind == "code":
            compile(text, f"full-cell-{index}", "exec")
            item.update(execution_count=None, outputs=[])
        cells.append(item)
    notebook = {"nbformat": 4, "nbformat_minor": 5, "cells": cells,
                "metadata": {"kernelspec": {"display_name": "Python3", "language": "python", "name": "python3"},
                             "accelerator": "GPU", "colab": {"name": "Makata-v0.1 — internal full QLoRA.ipynb", "provenance": []}}}
    path = ROOT / "research/colab/makata-qlora-full.ipynb"
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(build())
