import test from "node:test"
import { Buffer } from "node:buffer"
import { execFileSync } from "node:child_process"
import assert from "node:assert/strict"
import { readFile, writeFile, mkdtemp, readdir, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { fileURLToPath } from "node:url"
import {
  studies,
  findStudy,
  studyMaterialUrl,
} from "../../lib/research/studies.ts"
import { studySources } from "../../lib/research/study-sources.ts"
import { extractOutline } from "../../lib/research/outline.ts"
import {
  prepareStudyArtifacts,
  sha256,
  verifiedSourceBundle,
} from "../../scripts/prepare-study-artifacts.mjs"

const evidence = JSON.parse(
  await readFile(
    new URL(
      "../../content/research/studies/001-tagalog-comprehension.evidence.json",
      import.meta.url
    ),
    "utf8"
  )
)
const privateInformation =
  /colab\.research\.google\.com\/drive\/|[A-Z]:[\\/]Users[\\/]|colab-import-[a-f0-9]+|"(?:mc_answer1|flores_passage|correct_answer_num|access_token|api_key)"\s*:/i

test("study catalog preserves completion, review, publication, and source distinctions", () => {
  assert.ok(studies.length >= 1)
  assert.equal(new Set(studies.map(({ id }) => id)).size, studies.length)
  assert.equal(new Set(studies.map(({ slug }) => slug)).size, studies.length)
  assert.equal(findStudy("unknown-report"), undefined)
  for (const study of studies) {
    assert.equal(findStudy(study.slug), study)
    assert.ok(study.authors.length > 0)
    assert.ok(["planned", "in-progress", "completed"].includes(study.status))
    for (const id of study.sources)
      assert.ok(studySources[id], `Missing reference ${id}`)
    for (const source of Object.values(studySources))
      assert.equal(new URL(source.url).protocol, "https:")
    if (study.reviewStatus === "peer-reviewed") assert.ok(study.reviewEvidence)
  }
  const first = findStudy("001-tagalog-comprehension")
  assert.deepEqual(first.authors, ["Makata"])
  assert.equal(first.status, "completed")
  assert.equal(first.reviewStatus, "not-peer-reviewed")
  assert.equal(first.availability, "prepared-locally")
  assert.equal(first.publishedOn, undefined)
  assert.equal(first.completedOn, evidence.completed_on)
})

test("verified results, exact pins, chronology, and timing reconcile", () => {
  assert.deepEqual(
    evidence.models.map((model) => model.correct),
    [483, 222]
  )
  assert.deepEqual(
    evidence.models.map((model) => model.wall_seconds),
    [2100.078, 1141.737]
  )
  assert.deepEqual(
    evidence.models.map((model) => model.accuracy_standard_error),
    [0.01663103346925096, 0.014377023375409376]
  )
  assert.equal(evidence.protocol.task, "filbench|belebele_fil_mcf|0|0")
  assert.equal(
    evidence.protocol.custom_entry_point,
    "community_tasks/filbench_evals.py"
  )
  assert.equal(
    evidence.protocol.filbench_revision,
    "7ad52795d7d218d4679f93a019b58dde4b749c5b"
  )
  assert.equal(
    evidence.dataset.revision,
    "7899cdfa4e1e0d733fd77c848e2c273cb1d32be2"
  )
  assert.equal(evidence.dataset.subset, "tgl_Latn")
  assert.equal(evidence.dataset.split, "test")
  assert.equal(evidence.protocol.dtype, "float32")
  assert.equal(evidence.protocol.batch_size, 1)
  assert.equal(evidence.protocol.seed, 1234)
  for (const key of [
    "tf32",
    "quantization",
    "filtering",
    "chat_template",
    "uploads",
  ])
    assert.equal(evidence.protocol[key], false)
  assert.equal(evidence.protocol.system_prompt, null)
  assert.equal(evidence.protocol.truncation, "abort")
  assert.equal(evidence.verification.raw_results_public, false)
  assert.equal(evidence.freeze.benchmark_accessed_at_freeze, false)
  assert.deepEqual(
    evidence.models.map((model) => model.model_revision),
    [
      "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
      "75c2856ffc7e6a6e64127f40c5f54a953deb682e",
    ]
  )
  for (const model of evidence.models) {
    assert.equal(model.samples, 900)
    assert.equal(model.accuracy, model.correct / model.samples)
    assert.equal(model.model_revision, model.tokenizer_revision)
    assert.match(model.model_revision, /^[a-f0-9]{40}$/)
    assert.match(model.samples_sha256, /^[a-f0-9]{64}$/)
    assert.ok(model.inference_seconds < model.wall_seconds)
    assert.ok(model.maximum_input_tokens < model.context_tokens)
    assert.ok(
      Date.parse(evidence.freeze.created_at) < Date.parse(model.started_at)
    )
    assert.ok(
      Math.abs(
        (Date.parse(model.finished_at) - Date.parse(model.started_at)) / 1000 -
          model.wall_seconds
      ) < 0.002
    )
  }
  assert.equal(evidence.hardware.gpu, "Tesla T4")
  assert.doesNotMatch(JSON.stringify(evidence), privateInformation)
})

test("report sections and citations resolve without educational placeholder anchors", async () => {
  const body = await readFile(
    new URL(
      "../../content/research/studies/001-tagalog-comprehension.mdx",
      import.meta.url
    ),
    "utf8"
  )
  const outline = extractOutline(body)
  const ids = new Set(outline.map(({ id }) => id))
  for (const id of [
    "abstract",
    "research-motivation",
    "model-selection-methodology",
    "evaluation-methodology",
    "verified-results",
    "interpretation",
    "limitations",
    "research-decisions",
    "reproducibility",
    "conclusion-and-next-steps",
    "references",
    "suggested-citation",
    "related-learning",
  ])
    assert.ok(ids.has(id), id)
  assert.equal(ids.size, outline.length)
  assert.doesNotMatch(body, /^# |\bTODO\b|\[PLACEHOLDER\]/m)
  assert.doesNotMatch(body, privateInformation)
  for (const [, fragment] of body.matchAll(/\]\(#([^)]+)\)/g)) {
    assert.ok(
      ids.has(fragment) ||
        (fragment.startsWith("ref-") &&
          studies[0].sources.includes(fragment.slice(4))),
      fragment
    )
  }
  const toc = await readFile(
    new URL("../../components/research/navigation.tsx", import.meta.url),
    "utf8"
  )
  assert.match(toc, /supplementalLinks = \[\s*\{ id: "sources"/)
  assert.match(toc, /id: "related-reading"/)
  const page = await readFile(
    new URL("../../app/research/studies/[slug]/page.tsx", import.meta.url),
    "utf8"
  )
  assert.match(page, /supplementalLinks=\{\[\]\}/)
  assert.match(page, /dynamicParams = false/)
  assert.doesNotMatch(page, /research\/runs|ScholarlyArticle/)
})

test("public downloads match the frozen source and exclude private evidence", async () => {
  const directory = await mkdtemp(join(tmpdir(), "makata-publications-"))
  try {
    const checksums = await prepareStudyArtifacts(directory)
    const expectedFiles = [
      ...studies[0].materials.map(({ file }) => file),
      ...studies[0].decisions.map(({ file }) => file),
    ].sort()
    assert.deepEqual((await readdir(directory)).sort(), expectedFiles)
    for (const name of expectedFiles.filter(
      (name) => name !== "checksums.json"
    )) {
      const bytes = await readFile(join(directory, name))
      assert.equal(sha256(bytes), checksums[name], name)
      assert.equal(
        studyMaterialUrl(studies[0].slug, name),
        `/research-materials/001-tagalog-comprehension/${name}`
      )
      if (!name.endsWith(".zip"))
        assert.doesNotMatch(bytes.toString("utf8"), privateInformation)
    }
    assert.equal(
      checksums["makata-baselines.ipynb"],
      "794b3e1783f663517ebed076dcd6b692e46a2110448d001b6979e4ce10589865"
    )
    assert.equal(
      checksums["source-snapshot.zip"],
      "ac9949705cd1f5f5e6e9e266afb8b6f840c46ae7fab584ba6d8f34d236e05fde"
    )
    const notebook = await readFile(join(directory, "makata-baselines.ipynb"))
    assert.throws(
      () =>
        verifiedSourceBundle(
          Buffer.concat([notebook, Buffer.from(" ")]),
          evidence
        ),
      /checksum mismatch/
    )
    assert.throws(
      () =>
        verifiedSourceBundle(notebook, {
          artifacts: {
            ...evidence.artifacts,
            source_bundle_sha256: "0".repeat(64),
          },
        }),
      /bundle checksum mismatch/
    )
    for (const decision of studies[0].decisions) {
      const body = await readFile(join(directory, decision.file), "utf8")
      assert.match(body, /retrospective documentation/i)
      assert.match(body, /revisit|reconsider/i)
      assert.match(body, /Supporting evidence/)
      assert.match(
        body,
        /not public preregistration|not a formal public preregistration|not an externally registered|not proof/i
      )
    }
    await writeFile(join(directory, "unreviewed.json"), "{}")
    await assert.rejects(
      () => prepareStudyArtifacts(directory),
      /Unreviewed files/
    )
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
})

test("Git normalization preserves the executed source bytes across checkouts", async () => {
  const root = fileURLToPath(new URL("../../../../", import.meta.url))
  const notebook = JSON.parse(
    await readFile(join(root, "research/colab/makata-baselines.ipynb"), "utf8")
  )
  for (const name of [
    "research/colab/makata-baselines.ipynb",
    ...Object.keys(notebook.metadata.makata.files_sha256),
  ]) {
    const raw = execFileSync("git", ["hash-object", "--no-filters", name], {
      cwd: root,
      encoding: "utf8",
    }).trim()
    const filtered = execFileSync(
      "git",
      ["hash-object", `--path=${name}`, name],
      { cwd: root, encoding: "utf8" }
    ).trim()
    assert.equal(filtered, raw, `Git would normalize frozen bytes: ${name}`)
  }
})
