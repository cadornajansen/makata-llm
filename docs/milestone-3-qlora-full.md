# Milestone 3: bounded Aya-only QLoRA experiment

## Scope and status

This is the first authorized full **exploratory internal** Makata-v0.1 adapter experiment, not a validated capability result or a public model release. GPU training, fresh-process reload, download and independent local artifact verification passed. The predetermined final adapter is retained locally at `research/runs/qlora-full-import-v1/checkpoint-91/`.

The user approved the existing 363-record proposal on October 13, 2026. `research/qlora-full-authorization.json` records that bounded authorization separately; the original proposal, including its historical approval status, remains unchanged. No AWS, paid services, benchmark evaluation, public upload, or website work is authorized.

## Frozen inputs and method

- Base/tokenizer: `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`.
- Aya revision: `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`; original source SHA-256 `8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc`.
- Frozen proposal SHA-256: `9ab753aa10954de2832187df4486b95507dd33e4446cb9b6402c9ad9588e6ac8`.
- Selected training file SHA-256: `33a8edcaddee3c5b3fca12513b17ac906525b6d69745588b8a4c6cb848a071ac`.
- Provisional validation file SHA-256: `a4b41287eee61c509f06ca5069338605233aeef90a684d19d1706fee89140705`.
- Private upload ZIP SHA-256: `e06c8f10c662d9616b4fa073657fe734d87deb0d7fa310e15f362050571134a2`.

There are 363 training examples from 363 distinct prompt groups. Of these, 80 have individual agent observations (43 current and 37 prior); **283 have screening evidence only and no individual content review**. Known defects, explicit holds, and unresolved flagged third-party material remain excluded. Existing review evidence is not native-speaker validation or legal clearance. The declared Apache-2.0 source license does not establish rights to every contributed third-party passage. No text was rewritten for this run.

The separate 66 validation records are provisional Aya diagnostics with disjoint prompt groups. Their mean per-example response-token cross-entropy is measured before and after training; it is neither an independently validated evaluation nor a checkpoint-selection criterion. The 32 agent-authored evaluation tasks were not uploaded or scored. No Belebele, Kalahi, other benchmark examples, or evaluation failure cases are loaded by this executor. Previous screening receipts are preserved rather than reopening benchmark examples.

| Setting | Frozen value |
|---|---|
| Hardware | Free Colab, one NVIDIA T4 |
| Base storage/computation | 4-bit NF4, double quantization; FP16 computation |
| Trainable parameters | FP32 LoRA, rank 16, alpha 32, dropout 0.05, no bias |
| Targets | Q/K/V/O attention and gate/up/down MLP projections |
| Epochs and updates | One epoch, 363 examples, 91 successful optimizer updates |
| Batch/accumulation | One example; 90 windows of four and one final window of three |
| Optimizer | AdamW, FP32 moments, weight decay zero, clipping norm 1.0 |
| Schedule | Learning rate 2e-4, five warmup updates, constant thereafter |
| Loss scaling | Verified smoke initial scale 1024; fail on nonfinite gradients or skipped updates |
| Checkpoints | Updates 50 and 91; predetermined final checkpoint 91 |
| Sequence handling | Limit 512, no truncation, packing, chat template, or added vocabulary |
| Other controls | Seed/data seed 1234, gradient checkpointing, cache and TF32 disabled |

Completion formatting is `### Panuto:\n{prompt}\n\n### Sagot:\n{response}`, followed by the pinned EOS. Prompt and padding labels are masked with `-100`; response and EOS labels remain supervised. EOS and padding share ID 151643, so masking follows sequence length/attention masks rather than token identity.

The full executor uses an explicit PyTorch AMP loop with the unchanged smoke tokenizer, collator, quantized-base loader, and adapter helpers. Each accumulation window averages gradients over its **actual** example count, including three in the final window. An optimizer post-hook counts executed updates, rather than assuming every requested FP16 update succeeded. An independent seeded CPU generator shuffles the epoch exactly once. Checkpoints retain adapter-only safetensors plus optimizer, scheduler, scaler, random-number-generator state and data position. The historical smoke runner and notebook are not regenerated or modified.

## Verification and reproduction

The complete existing Python suite passed **105 tests**. Nine new offline tests cover scope, accounting, remainder normalization, adapter-only parameters, checkpoint integrity, archive safety, incomplete runs, and benchmark isolation. A separate installed-library tiny random Qwen3 CPU integration completed two windows (four and three examples), preserved the base weights, saved optimizer state, and reloaded equal adapter tensors/logits. These checks are engineering evidence, not a GPU run.

The separate Colab environment preserves Python 3.12.13; PyTorch 2.7.1 CUDA 12.6; Transformers 4.53.3; Accelerate 1.8.1; TRL 0.19.1; PEFT 0.16.0; bitsandbytes 0.46.1 and the existing transitive lock. Hardware and environment are checked before model download. Failures remain incomplete and are archived separately; no automatic resume or loss-based retries are performed.

Commands executed locally:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py prepare --source research/runs/aya-filipino-v2 --packet research/runs/aya-training-approval-v2-final --output research/runs/qlora-full-inputs-v1
research/.cache/qlora-cpu-venv/Scripts/python.exe -X utf8 research/qlora_full.py integration --output research/runs/qlora-full-integration-v1
research/.venv/Scripts/python.exe -X utf8 research/colab/build_qlora_full_notebook.py
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py import --archive "$env:USERPROFILE/Downloads/makata-v01-full-results.zip" --output research/runs/qlora-full-import-v1
```

The output-free `research/colab/makata-qlora-full.ipynb` embeds an explicitly allowlisted, hashed source snapshot. Upload `research/runs/qlora-full-inputs-v1/private-full-inputs.zip` separately. Its cells run safeguards, training, a fresh-interpreter final reload, verification, and an allowlisted result archive. Local import must verify both checkpoints, file hashes, actual update/example accounting, finite values, frozen configuration and reload proof before disconnecting Colab. Do not rerun training merely to reproduce verification.

Execution setup: Colab initially rejected a second GPU session. The already verified historical smoke session was terminated after its completed and failed artifacts were confirmed locally. The new session reports one Tesla T4 (15,637,086,208 bytes VRAM), CUDA 12.6, and the exact pinned environment. Source snapshot SHA-256 is `9e968f19abfb6fa25224e6969042bb87a126d0e7935d882841ee1a47cd1f7bd4`. The notebook's iframe upload did not expose a usable file chooser, so that setup cell was canceled before training and the identical ZIP uploaded through Colab's session-files pane. The replacement upload cell verifies the exact ZIP hash above before unpacking. This changes file transport only; the embedded executor, configuration and data are unchanged. No failed GPU training attempt is implied by this setup error.

Private inputs, checkpoints, logs, probes, manifests and result archives remain local and ignored. Historical completed and failed smoke artifacts remain in their original separate directories. No data or model artifact is published by this workflow.

## Observed GPU execution

| Measurement | Recorded value |
|---|---:|
| Actual optimizer updates | 91 |
| Examples consumed | 363, exactly once |
| First update loss | 2.1746431291103363 |
| Final update loss | 1.3594228426615398 |
| Mean of all 363 example losses during the epoch | 1.6835284903440266 |
| Training runtime | 257.665785127 seconds (4 min 17.67 s) |
| Peak allocated GPU memory | 3,731,268,608 bytes |
| Peak reserved GPU memory | 4,034,920,448 bytes |
| Trainable LoRA parameters | 17,432,576 |
| Final loss scale | 1024 |
| Fresh-process reload | Passed, equal adapter tensors |
| Maximum absolute probe-logit difference | 0.0 |
| Reload runtime | 5.219216250000045 seconds |

The training timer synchronizes CUDA and includes checkpoint saves. It excludes environment setup, model download/loading, pre/post validation diagnostics and fresh-process reload. Memory peaks are recorded over the loaded model's training/diagnostic process, rather than measuring optimizer updates in isolation. The first warmup optimizer call uses learning rate zero, followed by 4e-5, 8e-5, 1.2e-4, 1.6e-4 and then 2e-4; all 91 optimizer calls executed without AMP skips. All forward losses and unscaled gradients were finite. The final three-example window was included and averaged over three. No OOM or failed GPU training attempt occurred.

The final checkpoint is update 91 as predetermined. A separate interpreter (training PID 1925, reload PID 3355) loaded the same frozen quantized base and final adapter. Adapter tensor hashes matched exactly; finite FP16 probe logits matched with maximum absolute difference zero and unchanged top token. Declared comparison tolerances were absolute/relative 0.001. This is a reload-integrity check using a training-only probe, not generative evaluation.

The 66 provisional validation records had mean per-example response-token cross-entropy 2.0317009606144647 before and 1.7707118744199926 after training. Each diagnostic pass took approximately 11.09 seconds, excluded from the training timer. These records are not independently validated; the diagnostic was not used to select checkpoints.

## Independent local artifact verification

The downloaded ZIP contains 18 allowlisted files, is 386,252,957 bytes, and has SHA-256 `a7fd387a692a8a19cd8b3f1f74078a8f4d921f66376284fef5a5750c4aaa2b44`, matching the GPU-side archive receipt. A second copy is retained at `research/runs/qlora-full-execution-record-v1/makata-v01-full-results.zip`; the original download is preserved.

Local import safely extracted the archive into `research/runs/qlora-full-import-v1/` and verified every archived file hash, frozen source/configuration, adapter tensor digest and finite tensor value. Both checkpoint optimizer states contain FP32 finite moments with the expected update counters, matching scheduler/data positions and the complete 363-item epoch permutation. An additional independent log check confirmed 91 logs, 363 distinct example IDs, finite individual/aggregate losses, finite gradient norms/scales, and agreement between logged loss and the actual accumulation-window mean. All preserved smoke source and retained smoke evidence still match their frozen hashes.

| Checkpoint | Examples consumed | Adapter safetensors SHA-256 |
|---|---:|---|
| 50 | 200 | `7990dee87b8baebbe2cfb438dc54715651a6dda310c18fa47936ff016494211d` |
| 91, selected final | 363 | `f7605c629df52087d04da01fcf018368986570f64e3f864071eacb4a0ebdde2a` |

The local verification receipt is `research/runs/qlora-full-import-v1/local-verification.json`, recorded at `2026-10-12T17:56:33.756873+00:00` (October 13 in the Philippines). The runtime's UTC training interval was `2026-10-12T17:41:36.995233+00:00` through `2026-10-12T17:46:06.581895+00:00`; the synchronized training timer above is the precise measured duration. GPU-side reload finished at `2026-10-12T17:46:22.633037+00:00`. These are retained runtime timestamps, not invented publication dates.

Recheck the retained artifacts without inference, training, downloading weights or accessing benchmark records:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py verify --output research/runs/qlora-full-import-v1
```

All private input/output paths remain ignored by Git. Existing failed and completed smoke attempts remain separate and unchanged. There was no failed full GPU training attempt. The setup transport fallback described above is the only execution adjustment; no frozen training setting changed. Colab offers only **Disconnect and delete runtime**, which deletes temporary session files. That final UI deletion is left to the user after local verification; the saved notebook remains available and no computation is running.

## Interpretation boundary

First and last training losses describe different minibatches, not a controlled before/after capability measurement. Lower loss, including lower provisional Aya validation loss, cannot establish improved Filipino understanding. Milestone 4, independent review of the evaluation tasks, and any public release require separate approval.

## Files in this implementation

Created:

- `research/qlora-full-authorization.json`: separate bounded execution authorization.
- `research/qlora_full.py`: frozen input preparation, CLI, checkpoint verification and private result import.
- `research/qlora_full_runtime.py`: explicit AMP epoch, checkpoint state and fresh-process reload.
- `research/tests/test_qlora_full.py`: nine offline safeguards and accounting tests.
- `research/colab/build_qlora_full_notebook.py`: deterministic allowlisted notebook packaging.
- `research/colab/makata-qlora-full.ipynb`: output-free full-run notebook.
- `docs/milestone-3-qlora-full.md`: this procedure and evidence report.

Modified: `research/README.md` and `research/colab/README.md`, adding full-run commands and evidence links. No files were deleted. All unrelated working-tree changes, frozen smoke files, proposal, dependency locks, evaluation infrastructure and previous research artifacts were preserved.

## Publication follow-up

Milestone 4 has since completed; see [the post-training evaluation](milestone-4-post-training.md) and Research Report 002. The observed increase is not statistically established; model weights remain restricted. The approval boundaries above document the historical training scope.
