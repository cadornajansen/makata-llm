# Authoring Makata research reports

Research Studies contains original experimental reports. The eight Research & Learning articles explain external methods. Keep their catalogs and claims separate.

## Add a report

1. Add metadata to `apps/web/lib/research/studies.ts`, an MDX body under `apps/web/content/research/studies/`, and its explicit import in the server-only `study-content.ts` loader. Use the next report number and a stable descriptive slug. Existing routes generate the archive and report pages from this catalog.
2. Record authors accurately. Treat experiment status, review status, and public availability as separate fields. A completed experiment need not be peer reviewed or published. Do not assign `publishedOn` until actual release; then update availability and include an accurate date. Peer-review status requires verifiable review evidence.
3. Write an abstract, motivation, model/data selection, exact methodology, measurements, interpretation, limitations, decisions, reproduction instructions, references, and future work. Use plain `##`/`###` headings so the extracted TOC matches rendered anchors. Link citations beside claims to stable reference IDs. Add primary-source entries to `study-sources.ts`.
4. Reconcile measurements with full saved artifacts before creating an explicitly allowlisted public evidence JSON. Record exact revisions, software, hardware, timing definitions, completeness, and verification method. Never import ignored run directories into website code. Use one verified numeric source for tables, charts, and downloaded aggregates.
5. Add relevant numbered decision records. Distinguish contemporaneous records from retrospective documentation. Do not infer alternatives or preregistration from a narrative written after execution.
6. Register only reviewed public materials in `scripts/prepare-study-artifacts.mjs`. Extend its explicit allowlist for a future report. Frozen notebooks must have no outputs and match recorded checksums. Preserve historical source snapshots; do not regenerate them from newer code and keep the old identifier.

The publication preparation script uses only Node and reviewed source documents. It runs before web dev/build and writes ignored `public/research-materials/` assets. Turbo tracks the external document/notebook inputs and caches generated downloads with the build. Builds do not read raw runs, download models, or execute Python. Source documents remain authoritative; generated copies should not be edited.

## Report 001 materials and access

The [reproduction instructions](report-001-reproduce.md) describe the exact source-bundled notebook. The [decision records](decisions/README.md) were written retrospectively. The public evidence JSON contains aggregates and provenance; raw per-example predictions, full original manifests/logs, and private session details remain locally retained and ignored. Hashes identify those records but do not make them publicly auditable.

The notebook's `git_reference` identifies the earlier starting checkout; its embedded file hashes identify the actual executed source with local changes. Do not describe the starting commit alone as a complete executed source release. Same-site notebook/source downloads make the exact workflow available without relying on unpushed GitHub files.

Explicit Git attributes preserve the recorded notebook/dependency-lock bytes and the LF endings of other bundled source. Automatic Windows/Linux newline conversion would otherwise change the frozen hashes. Do not normalize the historical snapshot during release.

The previously committed CPU lock has LF endings, while the executed snapshot used its Windows CRLF working copy. When staging the reviewed release, explicitly stage that lock with `git add --renormalize research/requirements.txt` after the new attributes are in effect, then verify its SHA-256 against the frozen source manifest. This records historical bytes without changing dependency versions. The exact downloadable source ZIP already preserves them and does not depend on this Git staging step.

No project-wide license has been assigned. Do not imply that public availability grants unrestricted reuse. Credit external software, models, and datasets and preserve their applicable terms; review licensing explicitly before any broader release.

## Verify and release

Run `pnpm lint`, `pnpm typecheck`, `pnpm --filter web test:research`, and `pnpm build`, then `pnpm --filter web start`. Verify new routes, references, hashes/downloads, canonicals, sitemap, unknown-slug 404s, keyboard navigation, mobile rail, narrow layouts, and JavaScript-disabled reading. Run the existing Python tests and revalidate retained evidence without inference. Do not rerun benchmarks as a website check.

Review the intended Git changes and confirm no private artifacts or session links are included. Confirm that `makata.jansencadorna.com` is configured and reachable before public release. Committing, pushing, and deploying are separate actions. Set actual publication metadata when releasing; do not present the local preparation date as publication.

## Corrections

Preserve the report number/permalink. Add a dated correction explaining what changed, why, and which evidence supports it. Preserve prior measurements and provenance in version history. Reconcile any corrected score with original artifacts, and update the shared evidence summary, tables, prose, and download checksums together. A new experiment with changed methods belongs in a new report or clearly labeled version, not an undisclosed overwrite.

## Report 002 and subsequent cycle reports

The [reproduction guide](report-002-reproduce.md) distinguishes public frozen source from restricted data/weights. Its allowlisted evidence JSON is the numerical source for tables and charts. Preserve the passage-cluster bootstrap method, seed, sample count, negative interval endpoint and regressions beside the point estimate. Do not convert an uncertain difference into an improvement claim.

Training and evaluation notebooks have different historical bootstrap formats; preparation extracts their payloads and verifies immutable SHA-256s rather than rebuilding them. Keep all research snapshot bytes unchanged across checkouts. Source snapshots may include configuration metadata and synthetic engineering fixtures, but must contain no raw training records, benchmark records, unreviewed evaluation tasks, weights, credentials or private session URLs. Audit decoded ZIP entries as well as visible notebook text.

Exact reproduction remains conditional on authorized private inputs. Never imply that hashes make private evidence independently accessible. The recorded experiment completion dates are not publication dates. Both reports remain prepared locally until the approved release; assign publication metadata only then. See [publication verification](publication-cycle-verification.md) for checks and the reviewed file inventory.
