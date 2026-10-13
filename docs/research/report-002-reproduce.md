# Report 002 — reproduction and evidence access

Classification: **Independent Technical Report — Not Peer Reviewed**. Study completed October 13, 2026; publication date is assigned only at release.

## Public materials and important limits

The same-site downloads provide the unchanged, output-free training and evaluation notebooks, their exact embedded source ZIPs, an allowlisted evidence summary, a retrospective decision record, and SHA-256 inventories. Website builds read these reviewed files only; they never read private run directories.

**Public downloads alone cannot reproduce the exact trained adapter or paired analysis.** The selected Aya text, review packets, original predictions, optimizer states and model weights are restricted. The 32 unreviewed instruction-following tasks are not published or scored. Public hashes identify retained evidence, but are not public access to it. No claim of external replication or peer review is made.

The pinned upstream Aya file is accessible separately under its declared Apache-2.0 terms, which do not establish rights to every contributed third-party work. An independently screened subset is a new dataset realization; it must not be represented as the exact 363-example run. Exact reproduction requires authorized access to the hash-matched private inputs and retained baseline predictions. Contact Makata about evidence availability; access is not promised.

## Immutable inputs

- Base and tokenizer: `Qwen/Qwen3-1.7B-Base`, `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`.
- Aya: `CohereLabs/aya_collection_language_split`, `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`, `filipino/train-00000-of-00001.parquet`; SHA-256 `8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc`.
- Selected training JSONL: `33a8edcaddee3c5b3fca12513b17ac906525b6d69745588b8a4c6cb848a071ac`.
- Final adapter (update 91): `f7605c629df52087d04da01fcf018368986570f64e3f864071eacb4a0ebdde2a`.
- FilBench: `7ad52795d7d218d4679f93a019b58dde4b749c5b`, `community_tasks/filbench_evals.py`, `filbench|belebele_fil_mcf|0|0`.
- Belebele: `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, `tgl_Latn`, all 900 test questions. CC BY-SA 4.0.

Full revisions, source/manifest/archive hashes, execution timestamps, environment and numerical aggregates are in `evidence.json`. `checksums.json` identifies every public download. Source ZIPs are extracted from historical notebook payloads, not regenerated from newer working code.

## Frozen environments and method

Training: Python 3.12.13, PyTorch 2.7.1+cu126, Transformers 4.53.3, Accelerate 1.8.1, PEFT 0.16.0, TRL 0.19.1, bitsandbytes 0.46.1. The source contains the transitive CUDA lock. QLoRA uses NF4 double quantization, FP16 computation, FP32 rank-16 adapters/AdamW states, alpha 32, dropout 0.05, Q/K/V/O and gate/up/down targets. One epoch, batch one, accumulation four, LR 2e-4, five warmup updates, clip 1.0, seed 1234, sequence limit 512, no truncation/packing. The final three-example window is normalized by three. Exactly 91 successful optimizer updates; save 50 and 91, select 91 in advance. AMP initial scale 1024 preserves the verified smoke fix.

Format `### Panuto:\n{prompt}\n\n### Sagot:\n{response}` plus EOS 151643; mask prompt/padding with -100, preserving response EOS by sequence length. There is no chat template or added vocabulary.

Evaluation preserves the original environment, adding only PEFT 0.16.0. Load the unquantized base in FP32 and attach the unmerged FP32 adapter; batch one, TF32 off, seed 1234, four CPU threads. Preserve official prompts, 1-based-to-0-based answer conversion, answer-label log likelihoods and accuracy. No training prefix, system prompt, chat template, truncation, filtering or quantization is added.

## Commands (conditional on authorized private inputs)

These document the completed run; do not execute another experiment merely to check the website. Run from the matching source snapshot root in its pinned environment. Output directories must be new.

```powershell
# Prepare the training upload from already verified, restricted Aya artifacts.
python research/qlora_full.py prepare --source research/runs/aya-filipino-v2 --packet research/runs/aya-training-approval-v2-final --output research/runs/qlora-full-inputs-v1
```

Open the frozen training notebook in a free Colab T4 session. Its explicit cells verify hardware/environment and hashes, accept the separately uploaded private bundle, train once, save both checkpoints, reload the final adapter in a fresh process, and archive evidence. The executed session used Colab's files pane when the notebook upload widget failed; it verified the identical ZIP hash before extraction. This transport fallback did not change the source, data or training configuration.

```powershell
python research/qlora_full.py import --archive "$env:USERPROFILE/Downloads/makata-v01-full-results.zip" --output research/runs/qlora-full-import-v1
python research/qlora_full.py verify --output research/runs/qlora-full-import-v1
python research/post_training.py prepare --training-run research/runs/qlora-full-import-v1 --baseline research/runs/colab-import-7df37d1937bf --output research/runs/post-training-inputs-v1
```

The frozen evaluation notebook accepts the private adapter upload, freezes the GPU/environment/configuration, verifies disabled-adapter equality with the base, and invokes the guarded 900-question evaluation once. It refuses automatic retries in the frozen output directory. The base predictions are retained from Report 001, not rerun.

```powershell
python research/post_training.py import --archive "$env:USERPROFILE/Downloads/makata-post-training-results.zip" --output research/runs/post-training-import-v1
python research/post_training.py verify --output research/runs/post-training-import-v1
python research/post_training.py compare --baseline research/runs/colab-import-7df37d1937bf --output research/runs/post-training-import-v1 --destination research/runs/paired-comparison-reproduction.json
python -X utf8 -m unittest discover -s research/tests -v
```

Verification checks safe archive inventories, hashes, configuration, finite values, checkpoint state/update accounting, and reload equality. Pairing requires identical full prompts, choices, gold indices, instructions and token sequences. The retained comparison must match 390 both-correct, 108 improved, 93 regressed and 309 both-wrong. Bootstrap 488 passage clusters with replacement for 10,000 paired replicates, seed 1234; keep all questions in sampled passages and divide by their sampled question count. Use linear 2.5/97.5 percentiles. Expected interval: −1.449315799689441 to +4.804469273743017 percentage points. This interval includes zero and is conditional on this benchmark and one training run.

No raw benchmark examples are distributed in these downloads. No command uploads results or model weights automatically. Do not use observed benchmark failures for iterative tuning.
