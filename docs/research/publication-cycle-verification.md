# Research cycle publication verification

Recorded October 13, 2026. This describes local release preparation, not peer review or proof of a deployed website.

## Evidence and claims

The retained baseline archives, completed training checkpoints, and post-training archive were reverified locally without inference. Report 001/002 summaries reconcile to retained metrics, manifests, revisions and hashes. Website builds read committed summaries and frozen output-free notebooks, never private run directories.

Qwen3-1.7B-Base: 483/900 (53.67%); Sailor2-1B: 222/900 (24.67%). Makata-v0.1 checkpoint 91: 498/900 (55.33%). The observed +1.67 percentage points has a paired 95% passage-bootstrap interval of −1.45 to +4.80 points, with 108 improvements and 93 regressions. **A performance gain is not statistically established.** Both reports are independent technical reports, not peer reviewed.

Completion and publication metadata are distinct; no web publication date was invented. Data-rights and human-review limitations remain: 283/363 training records lacked individual content review; the 32 agent-authored tasks remain unreviewed and unscored; weights remain private. Evidence hashes do not provide public access or establish external replication.

## Commands and results

Executed from the repository root:

```powershell
pnpm lint
pnpm typecheck
pnpm --filter web test:research
pnpm build
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py verify --output research/runs/qlora-full-import-v1
research/.venv/Scripts/python.exe -X utf8 research/post_training.py verify --output research/runs/post-training-import-v1
pnpm --filter web start --port 3003
```

- Lint and typechecking passed. Website tests: **30/30**. Research tests: **114/114**. Production build: **31 static pages**.
- Training and post-training artifact verification passed. Both baseline sessions were rechecked through the existing `research.colab.import_results.verify_session` verifier.
- All 17 primary study-reference URLs returned HTTP 200. Accessibility does not imply endorsement.
- Archive and both reports checked at 320, 393, 768, 1024 and 1440 px; no horizontal page overflow. Desktop TOC and mobile rail navigate to section anchors. The results table scrolls by keyboard. The educational drawer opens by keyboard and restores focus after closing.
- Report 002 retains 62 paragraphs and five tables with JavaScript disabled. Reduced-motion emulation was checked and temporary overrides reset. No captured browser warnings or errors during checked report interactions.
- HTTP checks: homepage, learning index, mathematics article, archive and both reports return 200; canonical origins and fragment links match. Two unknown slugs return 404. All 16 download responses match local checksums; both report social images and sitemap work.
- `https://makata.jansencadorna.com` resolved and returned HTTPS 200. This does not establish that the new reports are deployed. No deployment, training or GPU experiment was launched.
- Downloads are deterministic and checksum-verified. Tests decode embedded source ZIPs to check for forbidden private payloads. Historical synthetic engineering fixtures are explicitly identified; unreviewed evaluation tasks are excluded.
- Raw data, adapters/checkpoints, per-question benchmark records, account/session information and caches remain outside the Git inventory. Generated downloads remain ignored and are rebuilt from an explicit allowlist.

Local receipts and the desktop screenshot are retained under ignored `research/.cache/`; private experiment evidence remains under ignored `research/runs/`.

## Scope and file inventory

This delivery includes previously uncommitted Milestones 2–4 source and Report 001 infrastructure, alongside Report 002 and current-state integration. Including historical source makes reproduction coherent; those experiments were not rerun. Frozen notebooks and research source were preserved byte-for-byte. Git preserves historical CRLF bytes of `research/requirements.txt`; dependency versions were not changed for publication. No files were deleted or dependencies added.

Every created or modified file relative to the previous commit is listed below; generated private artifacts are excluded.


- `.gitattributes`
- `.gitignore`
- `README.md`
- `apps/web/app/page.tsx`
- `apps/web/app/research/layout.tsx`
- `apps/web/app/research/page.tsx`
- `apps/web/app/research/studies/[slug]/opengraph-image.tsx`
- `apps/web/app/research/studies/[slug]/page.tsx`
- `apps/web/app/research/studies/opengraph-image.tsx`
- `apps/web/app/research/studies/page.tsx`
- `apps/web/app/sitemap.ts`
- `apps/web/components/research/navigation.tsx`
- `apps/web/components/research/report-001-evidence.tsx`
- `apps/web/components/research/report-002-evidence.tsx`
- `apps/web/components/research/social-image.tsx`
- `apps/web/components/research/study-elements.tsx`
- `apps/web/content/research/evaluation.mdx`
- `apps/web/content/research/studies/001-tagalog-comprehension.evidence.json`
- `apps/web/content/research/studies/001-tagalog-comprehension.mdx`
- `apps/web/content/research/studies/002-aya-qlora-evaluation.evidence.json`
- `apps/web/content/research/studies/002-aya-qlora-evaluation.mdx`
- `apps/web/lib/research/metadata.ts`
- `apps/web/lib/research/studies.ts`
- `apps/web/lib/research/study-content.ts`
- `apps/web/lib/research/study-sources.ts`
- `apps/web/lib/site.ts`
- `apps/web/package.json`
- `apps/web/scripts/prepare-study-artifacts.mjs`
- `apps/web/tests/research/publication-cycle.test.mjs`
- `apps/web/tests/research/studies.test.mjs`
- `docs/first-study.md`
- `docs/milestone-2-baselines.md`
- `docs/milestone-3-data-audit.md`
- `docs/milestone-3-data-refinement.md`
- `docs/milestone-3-qlora-full.md`
- `docs/milestone-3-qlora-smoke.md`
- `docs/milestone-3-quarantine-review.md`
- `docs/milestone-3-training-readiness.md`
- `docs/milestone-4-post-training.md`
- `docs/project-vision.md`
- `docs/research-directions.md`
- `docs/research-roadmap.md`
- `docs/research/decisions/0001-tagalog-reading-comprehension.md`
- `docs/research/decisions/0002-baseline-model-selection.md`
- `docs/research/decisions/0003-evaluation-protocol.md`
- `docs/research/decisions/0004-exploratory-aya-adaptation.md`
- `docs/research/decisions/README.md`
- `docs/research/publication-cycle-verification.md`
- `docs/research/publications.md`
- `docs/research/report-001-implementation.md`
- `docs/research/report-001-reproduce.md`
- `docs/research/report-002-reproduce.md`
- `research/README.md`
- `research/aya-training-proposal.json`
- `research/baseline-plan.json`
- `research/colab/README.md`
- `research/colab/build_notebook.py`
- `research/colab/build_post_training_notebook.py`
- `research/colab/build_qlora_full_notebook.py`
- `research/colab/build_qlora_notebook.py`
- `research/colab/import_results.py`
- `research/colab/makata-baselines.ipynb`
- `research/colab/makata-post-training.ipynb`
- `research/colab/makata-qlora-full.ipynb`
- `research/colab/makata-qlora-smoke.ipynb`
- `research/colab/run.py`
- `research/evaluate.py`
- `research/post-training-plan.json`
- `research/post_training.py`
- `research/preflight.py`
- `research/prepare_dataset.py`
- `research/prepare_training_readiness.py`
- `research/protocol.py`
- `research/qlora-full-authorization.json`
- `research/qlora-smoke-plan.json`
- `research/qlora_full.py`
- `research/qlora_full_runtime.py`
- `research/qlora_smoke.py`
- `research/qlora_training.py`
- `research/requirements-colab.txt`
- `research/requirements-post-training-colab.txt`
- `research/requirements-qlora-colab.in`
- `research/requirements-qlora-colab.txt`
- `research/requirements.txt`
- `research/tests/test_colab.py`
- `research/tests/test_colab_import.py`
- `research/tests/test_dataset_preparation.py`
- `research/tests/test_evaluation.py`
- `research/tests/test_post_training.py`
- `research/tests/test_qlora_full.py`
- `research/tests/test_qlora_smoke.py`
- `research/tests/test_training_readiness.py`
- `turbo.json`

## Remaining release checks

Push the reviewed commit to the existing remote under the user's authorization. Deployment remains separate. After the production rollout, verify both reports, downloads, sitemap and canonical metadata at `https://makata.jansencadorna.com`, then assign a truthful publication date and availability state. Do not release weights or dataset text before rights and release-readiness review. Exact adaptation reproduction remains conditional on authorized private inputs; the baseline notebook is independently executable subject to compute and source access.
