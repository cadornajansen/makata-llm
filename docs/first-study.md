# Makata first study: Tagalog reading comprehension

**Status: protocol and engineering preparation; no baseline results yet.**

## Question and purpose

How reliably do selected open-weight language models answer multiple-choice questions grounded in Tagalog passages? Makata will establish reproducible baselines before choosing a model and Filipino training data for GPU fine-tuning. Evaluation is evidence gathering toward that objective, not a replacement for model adaptation research.

The initial task is the `tgl_Latn` subset of [Belebele](https://huggingface.co/datasets/facebook/belebele), evaluated through [FilBench](https://aclanthology.org/2025.emnlp-main.127/). Its 900 test questions measure Tagalog reading comprehension using translated passages. They do not directly measure Taglish conversation, native Philippine cultural knowledge, open-ended generation, or all Filipino-language abilities.

## Models and computing

After the engineering pilot passes, select one general-purpose multilingual open-weight checkpoint and one Filipino- or Southeast Asian-focused checkpoint, if computing resources and license conditions permit. Consider existing regional research, including [AI Singapore SEA-LION](https://sea-lion.ai/). Record the exact checkpoint, license, language coverage, context capacity, inference memory, architecture support, and suitability for later fine-tuning. Neither Qwen nor a particular parameter count is a fixed requirement. A comparison between unrelated checkpoints is descriptive; it cannot isolate a causal effect of regional training.

The CPU pilot uses [SmolLM2-135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M), a primarily English-focused model, only to test the pipeline on 20 original synthetic Filipino questions. Its pilot accuracy is not a Filipino benchmark or a model-selection result. GPU access is pending; the personal budget is approximately ₱1,000/month, with US$80 in one-time AWS credits whose eligibility and expiry need checking. No cloud spending is required for this preparation.

## Fixed baseline protocol

- Use FilBench's official `community_tasks/filbench_evals.py` entry point and zero-shot selector `filbench|belebele_fil_mcf|0|0`.
- Preserve the official localized prompt, answer order, conversion of 1-based answer labels to 0-based indices, and likelihood-based multiple-choice accuracy. Do not parse freely generated answers or introduce a custom aggregate metric.
- Run the complete 900-question subset for a reported baseline, with no few-shot examples, additional system prompt, or chat template. Record model/tokenizer revisions, precision, context handling, dependencies, hardware, runtime, and per-example scoring details. Abort on overlength inputs rather than silently truncating them.
- Keep qualitative error review separate from accuracy. Potential review categories include explicit detail, inference, negation, reference resolution, distractor confusion, and ambiguous items; these are human annotations, not supplied benchmark labels.

| Artifact | Pinned revision |
| --- | --- |
| FilBench Lighteval fork | `7ad52795d7d218d4679f93a019b58dde4b749c5b` |
| Pilot model and tokenizer | `93efa2f097d58c2a74874c7e644dbc9b0cee75a2` |
| Belebele dataset | `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2` |

Belebele is external research released under **CC BY-SA 4.0**; preserve its attribution and applicable license conditions. The harness is external software under its own license. Makata claims neither authorship of these works nor institutional affiliation. [Belebele paper](https://aclanthology.org/2024.acl-long.44/), [pinned task definition](https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/filbench/belebele.py).

## Evaluation protection and next decision

The synthetic debugging questions are stored separately and never drawn from Belebele. During implementation, do not download benchmark examples or execute benchmark mode. Freeze the baseline protocol before accessing the test set. Mark failed or partial runs incomplete, and do not report them as full benchmark measurements.

Public benchmarks may already occur in model training data, so their availability does not establish absence of contamination. Do not repeatedly tune a model against observed Belebele failures. Before adaptation experiments, establish an additional independently authored, untouched Filipino evaluation set, separated from training data and development decisions. Creating that set is a later task.

Completion of this preparation means passing tests and a verified local CPU pilot. Next, select the two serious checkpoints and run their baselines when compute permits. Use the evidence, a separate development set, and dataset provenance review to justify a bounded Filipino fine-tuning experiment. Batayan/SEA-HELM may inform later evaluation, but no scores are combined with this task.
