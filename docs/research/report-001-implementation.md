# Report 001 publication implementation and verification

Prepared locally on October 12, 2026. This is a delivery record for the website implementation, not a new experiment, publication date, or peer-review record.

## Delivered routes and content

- `/research/studies`: publication-style archive, currently containing only Report 001.
- `/research/studies/001-tagalog-comprehension`: complete technical report, static results comparison, methodology, limitations, citations, decisions, and reproduction materials.
- Corresponding index/report Open Graph images and sitemap entries.
- Eight same-site materials under `/research-materials/001-tagalog-comprehension/`: notebook, exact embedded ZIP, aggregate evidence JSON, reproduction instructions, three decision records, and checksums.

The author is Makata. Completion, review, and publication availability are distinct. The experiment completed October 12, 2026; public availability is prepared locally, no publication date is assigned, and the classification is Independent Technical Report — Not Peer Reviewed.

## Evidence reconciliation

Read-only local verification recomputed both complete runs from saved scores: Qwen3-1.7B-Base 483/900, accuracy 0.5366666666666666; Sailor2-1B 222/900, accuracy 0.24666666666666667. Exact official standard errors, float32/T4 execution conditions, frozen revisions, timing, and evidence hashes are in the public summary. No inference or benchmark download was performed for this website work.

Raw per-example records remain ignored and local. Public hashes identify retained evidence without providing independent access to its contents. Local verification is not independent external replication. Qualitative-review records remain empty. The source cards, papers, dataset card and official FilBench entry/task were checked during planning; Sailor2's pinned card was accessible through raw HTTP, while its standalone LICENSE returned 404. The report attributes licensing to that card accordingly.

## Architecture and data flow

1. The typed study catalog supplies archive entries, article headers, static routes, and metadata.
2. An explicit server-only loader imports the registered local MDX body and extracts its section outline.
3. A curated evidence JSON supplies result tables, chart labels, revision listings, provenance, and the downloadable summary. Neither loader nor website build reads private run directories.
4. Shared MDX/shadcn components render semantic content. The existing TOC/mobile rail handles navigation; studies pass an empty supplemental-link list while learning articles keep their defaults.
5. Before dev/build, an allowlisted Node script verifies the historical notebook, extracts the exact original source ZIP, and copies reviewed materials into an ignored public download directory. Unexpected files in that directory cause a failure. Turbo tracks source-document inputs and includes generated downloads in its build cache.

No packages, CSS files, database, CMS, or charting library were added. Explicit Git attributes preserve frozen file bytes across Windows/Linux checkouts.

## Files created

| File | Purpose |
| --- | --- |
| `.gitattributes` | Preserve historical notebook/lock bytes and LF source hashes |
| `apps/web/app/research/studies/page.tsx` | Study archive |
| `apps/web/app/research/studies/[slug]/page.tsx` | Reusable statically generated report route |
| `apps/web/app/research/studies/opengraph-image.tsx` | Archive social image |
| `apps/web/app/research/studies/[slug]/opengraph-image.tsx` | Report social image |
| `apps/web/components/research/study-elements.tsx` | Metadata, results, decisions, materials, and references |
| `apps/web/components/research/report-001-evidence.tsx` | Report 001 result/revision/provenance bindings |
| `apps/web/content/research/studies/001-tagalog-comprehension.mdx` | Full scientific report |
| `apps/web/content/research/studies/001-tagalog-comprehension.evidence.json` | Allowlisted verified public measurements and provenance |
| `apps/web/lib/research/studies.ts` | Typed study catalog and labels |
| `apps/web/lib/research/study-content.ts` | Server-only import registry and outline loader |
| `apps/web/lib/research/study-sources.ts` | Primary-source citation catalog |
| `apps/web/scripts/prepare-study-artifacts.mjs` | Dependency-free public-material preparation |
| `apps/web/tests/research/studies.test.mjs` | Publication content, provenance, packaging, and Git-normalization checks |
| `docs/research/decisions/README.md` | Decision-record index and conventions |
| `docs/research/decisions/0001-tagalog-reading-comprehension.md` | Retrospective scope decision |
| `docs/research/decisions/0002-baseline-model-selection.md` | Retrospective selection decision |
| `docs/research/decisions/0003-evaluation-protocol.md` | Retrospective protocol and hardware-amendment decision |
| `docs/research/report-001-reproduce.md` | Downloaded reproduction instructions |
| `docs/research/publications.md` | Future authoring, release, licensing, and corrections guidance |
| `docs/research/report-001-implementation.md` | This delivery record and complete file inventory |

## Files modified in this pass

| File | Purpose |
| --- | --- |
| `.gitignore` | Ignore generated publication downloads |
| `README.md` | Research-state consistency, report/documentation links, canonical domain |
| `apps/web/app/research/layout.tsx` | Studies navigation and accurate shared footer |
| `apps/web/app/research/page.tsx` | Original-research entry point |
| `apps/web/app/sitemap.ts` | Studies index/report URLs |
| `apps/web/components/research/navigation.tsx` | Configurable TOC supplemental links, preserving learning defaults |
| `apps/web/components/research/social-image.tsx` | Optional study-specific labels/footer |
| `apps/web/lib/research/metadata.ts` | Correct website/article type for archive metadata |
| `apps/web/lib/site.ts` | Canonical `https://makata.jansencadorna.com` origin |
| `apps/web/package.json` | Prepare downloads before dev/build |
| `turbo.json` | Include external publication inputs and generated downloads in build caching |
| `docs/milestone-2-baselines.md` | Sanitize private session URL/account observations and personal paths in the existing local report |
| `research/colab/README.md` | Replace a personal download path with a portable placeholder |

No files were deleted. Existing homepage, vision/roadmap, evaluator/protocol/test changes and other pending research files were preserved. The milestone report and Colab README already existed locally but were uncommitted; they were updated rather than recreated. Generated materials and browser evidence remain ignored.

## Verification

```powershell
pnpm lint
pnpm typecheck
pnpm --filter web test:research
pnpm build
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
pnpm --filter web start --port 3002
```

- Lint passes with zero warnings; TypeScript passes.
- Website research suite: 27 passing tests, including the existing eight-article coverage and numerical checks.
- Python suite: 27 passing tests; no benchmark execution.
- Production build succeeds; both study pages and social images are statically generated.
- Browser checks at 320, 393, 768, 1024, and 1440px: both new pages render without horizontal document overflow.
- Mobile rail keyboard navigation, nested scrolling, smooth desktop anchors, skip link, reduced motion, and JavaScript-disabled reading pass.
- All eight learning routes and the homepage return 200; unknown study slug returns 404.
- Report section/citation anchors resolve; KaTeX compiles without errors.
- Sitemap contains 12 canonical page URLs. Both study social images return PNGs; all eight downloads return successfully and agree with published SHA-256 checksums.
- Browser checks report no uncaught page errors. Screenshots and check logs are retained under ignored `research/.cache/publications-verification/`.
- Git clean-filter checks preserve all 11 frozen notebook/source file byte sequences.

## Remaining release steps and limitations

1. Review the intended changes, including pre-existing uncommitted research code required by the broader repository release. The old committed CPU lock has LF endings while the executed copy has CRLF; explicitly stage it with `git add --renormalize research/requirements.txt` under the new attributes and verify the frozen hash when preparing that release. Dependency versions are unchanged, and the public source ZIP already has the exact executed bytes. Do not include ignored raw runs, caches, environments, or private session data.
2. Confirm the chosen production domain. `makata.jansencadorna.com` did not resolve from this environment during planning; canonical configuration is prepared but DNS/deployment access remains unverified.
3. Review reuse/licensing terms. The project has no project-wide license, and public source availability does not itself grant unrestricted reuse. External model/data/software terms remain applicable.
4. When actually releasing, assign the real publication date and availability in study metadata, commit the reviewed source, and push/deploy only with authorization. Verify production downloads, canonicals, social previews, sitemap, and references afterward.

The original per-example predictions are not publicly distributed, so direct third-party audit of those predictions remains limited. Reproduction uses the exact publicly served frozen code and pinned artifacts. Formal peer review and independent external replication have not occurred. No cloud session, training, benchmark rerun, push, or deployment was performed in this pass.

## Subsequent publication cycle

Report 002 and the complete-cycle release checks supersede the current-status claims in this historical implementation log. See [publication-cycle verification](publication-cycle-verification.md). The canonical origin remains `https://makata.jansencadorna.com`; no domain migration is intended.
