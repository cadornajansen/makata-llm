# Free Colab execution for Milestone 2

Verified on 2026-10-12: both full 900-question baselines completed on a free T4, and the downloaded archive passed independent local verification. See the [Milestone 2 report](../../docs/milestone-2-baselines.md) for scores, exact evidence hashes, runtime and limitations. No AWS credits were consumed.

Open [`makata-baselines.ipynb`](makata-baselines.ipynb) through **Colab → Upload notebook**. The notebook contains an allowlisted, checksummed snapshot of the current local research code, so the unpushed Milestone 2 fixes are included. It does not depend on the older GitHub checkout. No model weights, benchmark examples, environments, credentials, or local run artifacts are embedded.

Colab is the first choice for this release because it offers a direct notebook upload and a free interactive GPU option. [Colab's official FAQ](https://research.google.com/colaboratory/faq.html) states that GPU types/availability vary and free sessions can run at most 12 hours, subject to usage limits. Kaggle also offers [free notebook GPUs](https://www.kaggle.com/docs/notebooks), but that account's verification/quota and internet availability have not been established here. Neither service promises a free GPU on demand. AWS credits are not consumed.

## Run the notebook

1. Choose **Runtime → Change runtime type → T4 GPU**, or another available free NVIDIA GPU. Do not upgrade or buy compute units.
2. Run sections 1–3. The notebook verifies its embedded source, installs isolated Python **3.12.13**, clones the exact FilBench fork, installs the Linux CUDA lock and runs the protocol tests. The notebook kernel's Python version is independent of the research interpreter.
3. Section 3 freezes `execution-profile.json` before candidate weights or benchmark examples are loaded. It requires one visible CUDA GPU with at least 12 GiB free VRAM, 8 GiB free host RAM and 25 GiB free disk as conservative planning screens. An unavailable GPU causes a failure, never CPU fallback.
4. Run section 4. Both selected candidates must pass the **20-question original synthetic development pilot** on CUDA. These are engineering measurements, not benchmark scores. Preserve the downloaded archive.
5. Run section 5 for Qwen, then section 6 for Sailor2. Each scores all **900** held-out Tagalog questions with the unchanged official protocol. Download the archive after each model. Do not tune models or prompts against those results.
6. Run section 7 to display complete results and download the final archive. Check that browser downloads actually finished before releasing the runtime.

The notebook explicitly uses **CUDA float32**, batch one, four CPU threads, and disables TF32/quantization. Thus the CPU study's precision stays unchanged; only execution hardware changes. The original `baseline-plan.json` is retained. A separate GPU execution profile records that amendment, source hashes, GPU/driver information and resource checks. Each run embeds this profile and its hash in its manifest. Scores are not claimed to be bit-identical across CPU/GPU hardware.

No chat template, system prompt, task/model/tokenizer/dataset pin, answer indexing or scoring function changes. `low_cpu_mem_usage` streams model loading to reduce host-memory peaks; it does not quantize weights. The evaluator checks actual input lengths against native context capacity, checks a GPU allocation allowance, and saves synchronized inference timing and peak GPU allocation/reservation. An out-of-memory failure remains incomplete.

## Session limits and saved evidence

Each candidate smoke run executes in a fresh subprocess, releasing its CUDA allocation on exit. A conservative runtime screen extrapolates measured synthetic inference time to 900 questions assuming a 2,048-token average input and adds ten minutes. This is a rough estimate, not a benchmark input cap or runtime promise. A projected run over four hours stops before test-set access. Each subprocess also has a four-hour timeout. Timeout or provider termination does not yield a valid result; no partial-subset scoring or resume mechanism is introduced.

The session lives under `/content/makata-<bundle-hash>/research/runs/colab-<session-id>/`. It contains the frozen GPU profile, logs, smoke references, baseline references and each run's existing four artifacts. A complete baseline must have 900 unique examples, four finite answer likelihoods per example, matching pins/source hashes, zero truncations/few-shot examples, and official aggregate accuracy matching saved predictions. Rerunning a baseline cell in the same session reuses an already verified complete run instead of evaluating it again.

After each stage, an archive is refreshed in `/content/makata-results-colab-<session-id>.zip`. Download cells use Colab's standard file-download helper; archives contain results/logs only. There is no Hugging Face upload, public Kaggle publication, paid API call, or Google Drive mount. **Runtime storage is temporary.** A hard termination can lose results that have not been downloaded; notebook output is not a substitute for the JSON/JSONL evidence. Keep the notebook itself with the downloaded archives to retain its exact bundled source.

After downloading, import and independently verify the archive on the CPU laptop:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/colab/import_results.py "PATH_TO_DOWNLOADED_ARCHIVE.zip"
```

Replace `PATH_TO_DOWNLOADED_ARCHIVE.zip` with the downloaded filename. `-X utf8` makes Windows read the saved UTF-8 passages correctly; the importer rejects Windows invocations without it before extracting files. This affects archive reading only, not inference or scoring. The importer checks archive paths/file types, extracts into an ignored unique `research/runs/colab-import-*` directory, verifies both 900-question runs, frozen profiles, source/sample hashes, revisions, finite likelihoods and official metrics, then writes `verification.json`. It preserves original remote path fields. Exit 0 requires both complete baselines; exit 2 means incomplete evidence. Source mismatches fail instead of silently accepting a different checkout. Keep the exact notebook snapshot alongside its archive for reproduction.

The repository's Milestone 2 report must then be updated using actual full-run evidence. This setup by itself does not complete the milestone.

## Rebuild and test locally

After editing any bundled research source, regenerate the notebook and re-upload it. The snapshot will have a different checksum; do not alter source inside an already frozen study session.

```powershell
research/.venv/Scripts/python.exe research/colab/build_notebook.py
research/.venv/Scripts/python.exe -m unittest discover -s research/tests -v
```

`requirements-colab.txt` was resolved for Linux x86_64/Python 3.12 from the CPU lock with only `torch==2.7.1+cpu` replaced by `torch==2.7.1+cu126`, plus the resolved Linux/CUDA dependencies. Install using `uv==0.11.28` and `uv pip sync --torch-backend cu126`. [PyTorch's official installation archive](https://pytorch.org/get-started/previous-versions/) documents the 2.7.1 CUDA 12.6 wheel source. The Windows CPU environment remains unchanged.

Packaging tests compile every code cell, verify embedded source against local hashes, and check that caches/runs are absent. The exported runtime skips the one packaging test because it receives source rather than a second copy of the notebook; all protocol/runtime safeguard tests still run. Passing local tests cannot establish CUDA driver compatibility or benchmark completion; the notebook's actual GPU checks and result verification are required.

## First QLoRA smoke test (separate workflow)

Use [makata-qlora-smoke.ipynb](makata-qlora-smoke.ipynb) for the authorized 20-update engineering test, not the baseline notebook. The [procedure and evidence](../../docs/milestone-3-qlora-smoke.md) explain preparation, loss masking, hardware checks, and result verification. Rebuild only this new notebook with `research/.venv/Scripts/python.exe -X utf8 research/colab/build_qlora_notebook.py`.

Select a free T4 and upload the private input ZIP when asked. The notebook embeds no Aya records and mounts no Drive. It uses its own Python 3.12.13/CUDA environment and performs training and reload in separate processes. Download the result ZIP before disconnecting; import it with `research/.venv/Scripts/python.exe -X utf8 research/qlora_smoke.py import --archive PATH_TO_ZIP --output research/runs/qlora-smoke-import-v1`. Existing output directories are refused. A failed or partial run is incomplete; do not report it as successful training.


## Bounded Makata-v0.1 full QLoRA run

Open `makata-qlora-full.ipynb`, a separate snapshot from the historical smoke notebook. Use only a free single T4. Run cells in order: preflight, private-input upload, offline tests/tiny CPU integration, one-epoch training/fresh reload, and result download. Stop if payment or unavailable free compute blocks execution.

Use only the ZIP produced by `qlora_full.py prepare`; no benchmark or agent-authored evaluation items belong in this workflow. The 66 validation records are unvalidated Aya diagnostics, not an independent test. Save both 50/91 checkpoints. Keep failed attempts separately and download their evidence too. Import the result archive locally with `qlora_full.py import` before disconnecting. A complete run requires 91 actual optimizer updates, all 363 examples exactly once, finite losses/gradients, matching checkpoint states and a fresh-process final-adapter reload. Do not rerun to select favorable losses.

See [the full-run report](../../docs/milestone-3-qlora-full.md) for execution evidence and limitations.

The first full run and independent local import are complete. Both checkpoints are retained in ignored `research/runs/qlora-full-import-v1/`; do not rerun the notebook merely to inspect them. The report includes a read-only local verification command, actual runtime/memory and the final reload proof. Post-training evaluation is documented separately below; no public model release has occurred.

## Checkpoint91 post-training benchmark

Use the separate [makata-post-training.ipynb](makata-post-training.ipynb) for Milestone4. It preserves the original evaluation environment plus pinned PEFT, uses unquantized FP32 inference, and checks disabled-adapter/base equivalence before accessing the900-question benchmark. Upload only `research/runs/post-training-inputs-v1/private-adapter.zip` through Files → Upload to session storage. Do not upload training examples or the32 unvalidated evaluation tasks.

Run setup, upload/check/freeze, then the single start cell. Rerun only the read-only monitor cell while waiting (approximately35–60 minutes on a free T4). An attempt marker prevents duplicate benchmark execution; failed runs remain incomplete. After process exit, run verify/archive/download, then import and compare locally as documented in the [Milestone4 report](../../docs/milestone-4-post-training.md). Do not release temporary runtime storage before local verification. No paid tier, model publication, training or failure-driven tuning is authorized.

### Verified post-training outcome

The authorized checkpoint 91 evaluation completed once on a free T4 and was downloaded and verified locally: 498/900, compared with the retained base's 483/900. The paired passage-bootstrap interval for the +1.67-point change spans −1.45 to +4.80 points. This does not establish a reliable capability improvement. See [the Milestone 4 report](../../docs/milestone-4-post-training.md) for methodology, evidence hashes, runtime, memory and limitations. Retained results are in ignored `research/runs/post-training-import-v1/`; use the local verifier, not another GPU run. No model release or further training is authorized by this workflow.
