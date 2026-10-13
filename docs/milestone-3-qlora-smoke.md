# First QLoRA engineering smoke test

This is a bounded pipeline check, not evidence of improved Tagalog comprehension. Makata-v0.1 is not complete. The existing two-model baseline, Aya exports, audit records, and evaluation notebook remain unchanged.

## Frozen inputs

The [selection ledger and configuration](../research/qlora-smoke-plan.json) authorize only Qwen/Qwen3-1.7B-Base, model and tokenizer revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`, and these 16 Aya training IDs:

`127, 132, 149, 181, 188, 312, 372, 564, 652, 680, 686, 820, 916, 961, 1102, 1199`.

They belong to 16 distinct training groups. Each selected record has a content-matched prior agent acceptance observation, no substantive quality flag, and no held or quarantined group member. Selection covers short arithmetic, simple context questions, language exercises, and basic programming syntax. Text is unchanged. This is **provisional engineering data, not native-speaker or legal clearance**; the wider Aya v2 dataset remains uncleared.

Preparation verifies the exact Aya v2 manifest, training export, disposition ledger, both review-decision files, source revision and attribution notice. It reads no validation/quarantine text or benchmark records. The previous dataset screening receipt is preserved through the manifest hash; this task does not repeat benchmark screening.

- Aya revision: `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`.
- Raw Parquet SHA-256: `8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc`.
- Aya v2 manifest SHA-256: `e1bcfee1b264aa527b3d53ad940e2410ff59f28a5bbb190cc491e8d40bf49cc2`.
- Aya v2 training SHA-256: `7468b67418756b738bc2bf4d5455316d87e116db242852738029f5dff4833ef2`.
- Initial private bundle SHA-256: `2b1a43c2161f253b9ea99cfcad94a71435d92971ba6b695f3e7e094373bf67c5`.

The bundle contains only `subset.jsonl`, `subset-manifest.json`, and `NOTICE.md`. Dataset text and adapters stay in ignored local run directories and the private Colab runtime. Aya's publisher declares Apache-2.0; this does not clear every possible third-party contribution. No dataset/model publication is authorized.

## Formatting and training contract

```text
### Panuto:
{original prompt}

### Sagot:
{original response}
```

Prefix and response are encoded separately, verified by exact decoding, and followed by EOS ID 151643. No chat template, tools, thinking instructions, added vocabulary, packing, or truncation is used. Instructions and padding have label `-100`, which PyTorch's cross-entropy ignores. Response tokens and the actual EOS remain supervised. Padding shares the EOS ID, so the collator pads by sequence length, never by matching token IDs. Causal loss predicts each supervised token from preceding tokens; it shifts logits and labels by one position.

The real pinned tokenizer check passed for all 16 records: **47–261 total tokens**, below the 512-token cap; 8–163 supervised tokens per example. Automatic roundtrip checks cannot verify the truth or linguistic quality of those answers.

| Setting | Frozen value |
| --- | --- |
| Base storage | 4-bit NF4 with double quantization |
| Quantized matmul compute | FP16; BF16 and TF32 disabled |
| Trainable parameters / optimizer state | FP32 LoRA / FP32 AdamW |
| LoRA | r=16, alpha=32, dropout=0.05, no bias |
| Targets | q/k/v/o attention and gate/up/down MLP projections |
| Updates | Exactly 20 successful optimizer calls |
| Batch | One example, accumulation four (effective batch four) |
| Learning rate | 2e-4; two warmup steps, then constant |
| Gradient clipping / weight decay | 1.0 / 0 |
| AMP loss scaler | Initial scale 1024; growth factor 2, backoff 0.5, growth interval 2000 |
| Seed | 1234 |
| Memory controls | Gradient checkpointing; cache disabled; no packing |

An initial warmup step has learning rate zero under the pinned Transformers scheduler; it is still a completed optimizer call. Logs report the rate actually used. Loss is the mean of the four microbatch response losses for that update, not a comprehension score. Five passes through this tiny subset are an implementation check, not a generalization test.

The runner stops on nonfinite loss/gradients/weights, skipped AMP optimizer updates, OOM, changed inputs, excessive length, or interruption. A run starts `incomplete`, becomes `pending_reload` after training, and becomes `complete` only after a fresh interpreter reloads the adapter. Reload uses the same frozen base and preparation dtypes, checks adapter tensor hashes, finite full-vocabulary next-token probe logits, matching argmax, and `atol=rtol=0.001`. Hashes are consistency checks, not independent replication.

## Isolated environment and reproduction

Python 3.12.13; PyTorch 2.7.1+cu126; Transformers 4.53.3; Accelerate 1.8.1; TRL 0.19.1; PEFT 0.16.0; bitsandbytes 0.46.1. The [CUDA lock](../research/requirements-qlora-colab.txt) pins all resolved dependencies. PyArrow 20.0.0 and xxhash 3.5.0 avoid compatibility failures with NumPy 1.26.4 and datasets 3.6.0. The evaluation environment and its locks are not reused for training or modified.

From the repository root, use fresh output directory names:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_smoke.py prepare --source research/runs/aya-filipino-v2 --output research/runs/qlora-smoke-inputs-v2
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/colab/build_qlora_notebook.py
```

Open `research/colab/makata-qlora-smoke.ipynb` in Colab and select **T4 GPU, free standard runtime**. Run cells in order. Upload the generated `private-inputs.zip` when prompted. The notebook contains only allowlisted source, not Aya text. It installs a separate Python environment, verifies resources before downloading model weights, checks tokenization, runs offline tests and a tiny random-model integration check, then trains and reloads in separate subprocesses. Download the result archive before disconnecting.

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_smoke.py import --archive PATH_TO_DOWNLOADED_ZIP --output research/runs/qlora-smoke-import-v1
```

No automatic resume is supported: existing output directories are rejected. Failed archives retain `incomplete` status and are not accepted as successful smoke tests. A hard runtime termination may prevent writing the latest error; the previously written incomplete/pending manifest still cannot pass verification. Save evidence before requesting another allocation.

Local CPU integration (does not test NF4 kernels):

```powershell
uv venv --python 3.12.13 research/.cache/qlora-cpu-venv
uv pip install --python research/.cache/qlora-cpu-venv/Scripts/python.exe --torch-backend cpu -r research/requirements-qlora-colab.in
uv pip check --python research/.cache/qlora-cpu-venv/Scripts/python.exe
research/.cache/qlora-cpu-venv/Scripts/python.exe -X utf8 research/qlora_smoke.py integration --output research/runs/qlora-integration-v2
research/.cache/qlora-cpu-venv/Scripts/python.exe -X utf8 research/qlora_smoke.py tokenize --inputs research/runs/qlora-smoke-inputs-v2 --output research/runs/qlora-tokenization-v1
```

## Verification evidence

- The existing 64 tests plus 15 smoke-test tests pass: **79 tests in 20.029 seconds**, recorded in ignored `research/runs/qlora-tests-final.txt`.
- The isolated CPU environment passes `uv pip check`.
- Tiny random Qwen3 + real TRL/PEFT completed two optimizer calls, changed only adapters, matched manual causal cross-entropy, preserved frozen base tensors, and reloaded matching adapter outputs. Receipt: `research/runs/qlora-integration-final/integration-check.json` (final source).
- The first CPU integration attempt exposed an incompatible PyArrow 26 resolution; the separate training lock was corrected to 20.0.0. No GPU run was attempted with that broken environment.
- Pinned tokenizer receipt: `research/runs/qlora-tokenization-v1/tokenizer-check.json`.
- Notebook generation is deterministic; all code cells compile and contain no saved output. Private bundle/cache paths are ignored by Git.

The first actual T4 attempt completed 19 optimizer updates, then GradScaler skipped update 20. The guard correctly rejected it. Its archive SHA-256 is `1b9a309525b62ad7e984116ee251e52846b53fa073e4c0545feeac91ecd63f8e`; raw archive and exact first-attempt source are retained in ignored `research/runs/qlora-failed-attempt-source/`, with extracted incomplete evidence in `research/runs/qlora-smoke-failed-v1/`. It is not a successful smoke test.

The explicit engineering amendment (`makata-qlora-smoke-v2`) reduces the initial FP16 loss scale from the default 65536 to 1024. Loss scaling multiplies loss before backpropagation to protect small FP16 gradients and unscales gradients before optimization; it does not change the learning rate or intended objective. An excessive scale can overflow. All checkpoint, record, optimizer, and LoRA choices remain unchanged; the repeat starts from the original base, without resuming the failed adapter. The new input-bundle hash is `d2eab1821917bd8682e6493de149cfe0bae0f8beb73b0bc322aa53b450ebb89e`.

The amended run **completed and passed local archive verification** on October 13, 2026 (Asia/Manila). Its manifest starts at `2026-10-12T16:08:21.722078+00:00` and finishes at `2026-10-12T16:09:38.245191+00:00` (UTC). This is retained local evidence, not independent replication.

| Measurement | Verified result |
| --- | --- |
| GPU | One Tesla T4, 15,637,086,208 bytes physical VRAM |
| Successful optimizer calls | 20, four microbatches each |
| Trainable LoRA parameters | 17,432,576 |
| Synchronized training duration | 57.935 seconds |
| Fresh-process reload duration | 5.180 seconds |
| Run start through reload completion | 76.523 seconds; excludes environment setup, pilots, and downloads |
| Peak PyTorch allocated GPU memory | 3,430,426,112 bytes (3.195 GiB) |
| Peak PyTorch reserved GPU memory | 3,735,027,712 bytes (3.479 GiB) |
| First / final update response loss | 1.186264 / 0.112067 |
| Mean of 20 update losses | 0.656920 |
| Final AMP scale | 1024 |
| Adapter tensor equality after reload | Exact |
| Probe logits | Finite, identical argmax, maximum absolute difference 0 |

All 20 updates recorded finite loss and gradients. No OOM occurred. PyTorch memory counters exclude CUDA driver/context overhead and are not total device usage. The examples span only 47–261 tokens; these measurements do not establish peak memory for 512-token examples or the full dataset. Loss decreased on repeatedly seen training examples; there is no held-out quality measurement here.

Verified local evidence: `research/runs/qlora-smoke-import-v2/` contains the complete manifest, 20-row training log, tokenizer receipt, adapter-only safetensors, probe reference, and reload verification. The archived copy is `research/runs/qlora-smoke-inputs-v2/results.zip`, SHA-256 `49b069759d4dc0333ee12f431a0a78219f3a54415543cff4a99ab56ec4f17b9b`. The plan SHA-256 is `4241ccf9a3c3a8b3ec217a5c7d95085efe4ba85ce6ce65e6a1323c036ffc71f0`; the manifest records all source and environment hashes. These private files remain ignored by Git.

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_smoke.py verify --output research/runs/qlora-smoke-import-v2
```

The Colab embedded file-picker timed out, so the same private ZIP was uploaded through Files → Upload to session storage; the notebook supports this fallback. Source was transferred through the generated notebook, with the previous immutable model cache reused for the second run. The probe autocast context is explicit in both training and reload. Transport corrections did not change the selected text or model checkpoint. No paid services, benchmark records, full training, or publication were used.

## Before a full Aya-only experiment

Full training requires final dataset clearance, an explicitly frozen configuration informed by the full approved training-set token lengths, an independently authored untouched evaluation set, and user approval. Smoke-test loss cannot establish Tagalog reading-comprehension improvement; Aya instruction following is not a passage-grounded comprehension training set. A successful smoke test establishes only that this software/hardware configuration can update and reload adapters on the inspected short examples.

One conservative candidate for that later, separately approved experiment is the same frozen base, NF4/double quantization, FP16 with initial scale 1024, FP32 LoRA r=16/alpha=32/dropout=0.05, the same seven target projections, batch one with accumulation four, AdamW at 2e-4, clipping 1.0, gradient checkpointing, no packing, and **one epoch** with 5% warmup followed by constant learning rate. Retain a 512-token ceiling only if the cleared-data token-length audit supports it; do not silently truncate longer records. Keep batch one despite the observed headroom until maximum-length examples are measured. This is a proposed configuration, not a frozen full-training plan or permission to run it.

## Implementation references

- [QLoRA paper](https://arxiv.org/abs/2305.14314): external method, not Makata work.
- [TRL 0.19.1 SFT trainer](https://github.com/huggingface/trl/blob/v0.19.1/trl/trainer/sft_trainer.py): custom collator and skipped preparation.
- [PEFT 0.16.0 k-bit preparation](https://github.com/huggingface/peft/blob/v0.16.0/src/peft/utils/other.py): frozen base and preparation dtypes.
- [PyTorch 2.7.1 installation archive](https://pytorch.org/get-started/previous-versions/): CUDA 12.6 wheels.
- [Pinned model card](https://huggingface.co/Qwen/Qwen3-1.7B-Base/tree/ea980cb0a6c2ae4b936e82123acc929f1cec04c1).
- [Pinned Aya source](https://huggingface.co/datasets/CohereLabs/aya_collection_language_split/tree/a3af2fde4b4cb5b2775830b11244a1a20b5f004f).
