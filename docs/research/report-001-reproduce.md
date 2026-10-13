# Reproduce Makata Research Report 001

This independent technical report measures Tagalog reading comprehension on translated passages. It has not undergone formal peer review. Study completion: October 12, 2026. Public materials do not establish independent replication.

## Obtain the executed source

Download `makata-baselines.ipynb`, `source-snapshot.zip`, `evidence.json`, and `checksums.json` from the report's reproduction section. The notebook has no saved outputs or private session links. Its embedded source is the executed snapshot, including the then-local changes; the earlier GitHub reference commit alone does not contain that workflow.

Verify a download in PowerShell with `Get-FileHash ./makata-baselines.ipynb -Algorithm SHA256`, or on Linux with `sha256sum makata-baselines.ipynb`. Compare to `checksums.json` and the notebook hash in `evidence.json`. The ZIP hash is the recorded source-bundle hash. It contains source, dependency locks, tests, and synthetic development fixtures; it contains no weights or benchmark examples. The source manifest identifies every bundled file.

## Execute in a new environment

Use Colab's notebook upload to open the downloaded notebook. Choose a free NVIDIA GPU runtime; allocation is not guaranteed. The historical runs used one Tesla T4. No account-specific saved Colab link is required. Do not enable paid upgrades automatically.

1. Run notebook sections 1–2 to verify/unpack source and install the isolated Python 3.12.13 / torch 2.7.1+cu126 environment from its Linux/CUDA lock. These operations download dependencies and later model weights.
2. Run section 3 to execute offline protocol tests and freeze a new execution profile. It requires CUDA, conservative available-memory/disk checks, float32, TF32 disabled, batch one, and no quantization. A different device must pass those checks; there is no CPU fallback.
3. Run section 4: both candidates must pass the 20-question original synthetic development pilot. These questions are not Belebele, and their accuracy is not a research baseline.
4. Only then run sections 5 and 6. Each evaluates all 900 `tgl_Latn` test questions under `filbench|belebele_fil_mcf|0|0`. Download the result archive after each run and again after section 7.
5. Retain the notebook, frozen profile, logs, per-example JSONL, official metrics, and manifests. Runtime storage is temporary. Incomplete or interrupted runs are not full benchmark results.

The notebook invokes these research commands sequentially through its isolated interpreter, with a new frozen session directory and candidate indices 0 (Qwen) and 1 (Sailor2):

```bash
python research/colab/run.py freeze --session SESSION
python research/colab/run.py smoke --session SESSION --candidate 0
python research/colab/run.py smoke --session SESSION --candidate 1
python research/colab/run.py evaluate --session SESSION --candidate 0
python research/colab/run.py evaluate --session SESSION --candidate 1
```

`SESSION` is the new directory created by the notebook, not a path from Makata's original account. Use the notebook to select its interpreter and set up the pinned fork rather than invoking these commands in an arbitrary preinstalled environment. The `freeze`, `smoke`, and `evaluate` subcommands are workflow guards; the underlying evaluator still uses the official FilBench entry point and scoring functions.

## Check results

The notebook and bundled `research/colab/run.py` verifier require complete manifests, matching candidate/configuration/source hashes, all 900 unique examples, four finite likelihoods per example, zero few-shot demonstrations, and no truncation. Recompute the maximum-likelihood choice for every question, compare it with the zero-based gold label, and reconcile mean correctness with the official `acc` metric. Check both runs; console output alone is insufficient.

The original local import additionally verified archive extraction safety, shared execution-profile hashes, and full evidence consistency on a separate CPU machine. This was a verification step within Makata, not an external replication. The retained raw records are not part of the public download set. Their hashes identify those records but cannot substitute for access to them. A reader can rerun the supplied code, but cannot independently audit the original per-example predictions from this aggregate-only release.

Full model/tokenizer/data/fork revisions, software versions, source hashes, original timestamps and exact aggregates are in `evidence.json`. Different GPU allocations or software changes may affect numerical reproducibility; do not promise bit-identical results across hardware. Report changed conditions explicitly.

## Protect subsequent research

Do not tune prompts, models, or hyperparameters repeatedly against observed test failures. Future adaptation requires separate development data and an independently authored, untouched Filipino evaluation set. No training or new data collection is performed by this notebook. The public report is a descriptive comparison of two external checkpoints on one task.
