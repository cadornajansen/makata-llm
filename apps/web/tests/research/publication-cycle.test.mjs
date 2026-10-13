import test from "node:test"
import assert from "node:assert/strict"
import { Buffer } from "node:buffer"
import { inflateRawSync } from "node:zlib"
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"
import { studies, findStudy } from "../../lib/research/studies.ts"
import { studySources } from "../../lib/research/study-sources.ts"
import { extractOutline } from "../../lib/research/outline.ts"
import { site } from "../../lib/site.ts"
import {
  prepareCycleArtifacts,
  sha256,
  verifiedCycleSourceBundle,
} from "../../scripts/prepare-study-artifacts.mjs"

const slug = "002-aya-qlora-evaluation"
const study = findStudy(slug)
const read = (path) => readFile(new URL(path, import.meta.url), "utf8")
const evidence = JSON.parse(
  await read(`../../content/research/studies/${slug}.evidence.json`)
)
const privateInformation =
  /colab\.research\.google\.com\/drive\/|[A-Z]:[\\/]Users[\\/]|"(?:mc_answer1|flores_passage|correct_answer_num|access_token|api_key)"\s*:/i

// Read the local-file entries of the frozen Python-generated ZIPs, including payload text.
function snapshotEntries(bytes) {
  const entries = new Map()
  let offset = 0
  while (bytes.readUInt32LE(offset) === 0x04034b50) {
    const flags = bytes.readUInt16LE(offset + 6)
    assert.equal(flags & 8, 0, "Unexpected streaming ZIP")
    const method = bytes.readUInt16LE(offset + 8)
    const size = bytes.readUInt32LE(offset + 18)
    const nameLength = bytes.readUInt16LE(offset + 26)
    const extraLength = bytes.readUInt16LE(offset + 28)
    const start = offset + 30
    const name = bytes.subarray(start, start + nameLength).toString("utf8")
    const data = bytes.subarray(
      start + nameLength + extraLength,
      start + nameLength + extraLength + size
    )
    assert.ok(method === 0 || method === 8)
    entries.set(name, method === 8 ? inflateRawSync(data) : data)
    offset = start + nameLength + extraLength + size
  }
  return entries
}

test("cycle metadata, complete counts, paired differences and uncertainty agree", () => {
  assert.equal(site.url, "https://makata.jansencadorna.com")
  assert.equal(studies.length, 2)
  assert.equal(study.completedOn, evidence.completed_on)
  assert.equal(study.reviewStatus, "not-peer-reviewed")
  assert.equal(study.availability, "prepared-locally")
  assert.equal(study.publishedOn, undefined)
  assert.deepEqual(
    evidence.models.map((result) => result.correct),
    [483, 498]
  )
  for (const model of evidence.models) {
    assert.equal(model.samples, 900)
    assert.equal(model.accuracy, model.correct / 900)
  }
  const { paired, aya, training } = evidence
  assert.deepEqual(paired.paired_counts, {
    both_correct: 390,
    improved: 108,
    regressed: 93,
    both_wrong: 309,
  })
  assert.equal(
    Object.values(paired.paired_counts).reduce((sum, count) => sum + count, 0),
    900
  )
  assert.ok(
    Math.abs(paired.difference_percentage_points - (108 - 93) / 9) < 1e-12
  )
  assert.deepEqual(
    paired.uncertainty.difference_interval_percentage_points,
    [-1.449315799689441, 4.804469273743017]
  )
  assert.equal(paired.uncertainty.seed, 1234)
  assert.equal(paired.uncertainty.replicates, 10000)
  assert.equal(paired.passage_clusters, 488)
  for (const version of [aya.v1, aya.v2])
    assert.equal(
      version.train +
        version.validation +
        version.quarantine +
        version.exclusions,
      version.original
    )
  assert.equal(
    aya.individual_agent_observations + aya.screening_only,
    aya.selected_training
  )
  assert.equal(aya.screening_only, 283)
  assert.equal(aya.v1.train, 437)
  assert.equal(aya.v1.validation, 49)
  assert.equal(aya.independent_human_review, false)
  assert.equal(aya.legal_clearance, false)
  assert.equal(training.metrics.optimizer_updates, Math.ceil(363 / 4))
  assert.equal(training.final_checkpoint, 91)
  assert.deepEqual(training.checkpoint_updates, [50, 91])
  assert.equal(training.reload.fresh_process, true)
  assert.equal(training.reload.tensor_equality, true)
  assert.equal(evidence.protocol.dtype, "float32")
  assert.equal(evidence.protocol.quantization, false)
  assert.equal(evidence.evaluation.base_rerun, false)
  for (const revision of [
    evidence.model.revision,
    evidence.model.tokenizer_revision,
    aya.revision,
    evidence.protocol.filbench_revision,
    evidence.benchmark.revision,
  ])
    assert.match(revision, /^[a-f0-9]{40}$/)
  assert.doesNotMatch(JSON.stringify(evidence), privateInformation)
  for (const flag of Object.values(evidence.release)) assert.equal(flag, false)
})

test("report section anchors, references and public release distinctions are complete", async () => {
  const body = await read(`../../content/research/studies/${slug}.mdx`)
  const outline = extractOutline(body)
  const ids = new Set(outline.map(({ id }) => id))
  assert.equal(ids.size, outline.length)
  for (const id of [
    "abstract",
    "dataset-provenance-and-preparation",
    "frozen-training-method",
    "training-and-checkpoint-verification",
    "post-training-evaluation-methodology",
    "verified-results-and-uncertainty",
    "interpretation-and-limitations",
    "research-decisions",
    "reproducibility-and-evidence-access",
    "references",
    "suggested-citation",
  ])
    assert.ok(ids.has(id), id)
  for (const [, id] of body.matchAll(/\]\(#([^)]+)\)/g))
    assert.ok(
      ids.has(id) ||
        (id.startsWith("ref-") && study.sources.includes(id.slice(4))),
      id
    )
  for (const id of study.sources) assert.ok(studySources[id])
  assert.match(body, /Improvement is not statistically established/)
  assert.match(body, /not public preregistration/)
  assert.match(body, /283/)
  assert.doesNotMatch(body, privateInformation)
  const page = await read("../../app/research/studies/[slug]/page.tsx")
  assert.match(page, /dynamicParams = false/)
  assert.match(page, /"@type": "Article"/)
  assert.match(page, /study.publishedOn \? \{ datePublished/)
  assert.doesNotMatch(page, /no Makata model has been trained|ScholarlyArticle/)
})

test("cycle downloads are deterministic, frozen and contain no private data payloads", async () => {
  const directory = await mkdtemp(join(tmpdir(), "makata-cycle-"))
  try {
    const hashes = await prepareCycleArtifacts(directory)
    assert.deepEqual(
      (await readdir(directory)).sort(),
      [
        ...study.materials.map(({ file }) => file),
        ...study.decisions.map(({ file }) => file),
      ].sort()
    )
    assert.deepEqual(await prepareCycleArtifacts(directory), hashes)
    for (const [name, expected] of Object.entries(hashes)) {
      const bytes = await readFile(join(directory, name))
      assert.equal(sha256(bytes), expected)
      if (!name.endsWith(".zip"))
        assert.doesNotMatch(bytes.toString("utf8"), privateInformation)
      else {
        const entries = snapshotEntries(bytes)
        const receipt = JSON.parse(
          entries.get("source-manifest.json").toString("utf8")
        )
        const manifest = receipt.sha256 ?? receipt
        assert.equal(entries.size, Object.keys(manifest).length + 1)
        for (const [path, content] of entries) {
          assert.ok(
            path === "source-manifest.json" ||
              /^research\/(?:[\w.-]+|tests\/[\w.-]+|colab\/run.py|fixtures\/development.json)$/.test(
                path
              ),
            path
          )
          assert.doesNotMatch(
            path,
            /runs\/|adapter|validation|evaluation-tasks|\.safetensors|\.parquet/
          )
          assert.doesNotMatch(
            content.toString("utf8"),
            /colab\.research\.google\.com\/drive\/|[A-Z]:[\\/]Users[\\/]|"(?:access_token|api_key)"\s*:/i,
            path
          )
          if (path === "research/fixtures/development.json") {
            const fixture = JSON.parse(content.toString("utf8"))
            assert.equal(
              fixture.provenance,
              "makata-original-synthetic-development"
            )
            assert.equal(fixture.examples.length, 20)
            assert.equal(
              sha256(content),
              "cf22ec6cc0043a53cc6564f05ab959c24874437cff6e353af6f32ebf09b1e24b"
            )
          } else if (path.endsWith(".json")) {
            assert.doesNotMatch(
              content.toString("utf8"),
              privateInformation,
              path
            )
          }
          if (path !== "source-manifest.json")
            assert.equal(sha256(content), manifest[path])
          if (path.endsWith("aya-training-proposal.json")) {
            const proposal = JSON.parse(content.toString("utf8"))
            for (const record of proposal.selection) {
              assert.equal(record.prompt, undefined)
              assert.equal(record.response, undefined)
              assert.equal(record.inputs, undefined)
              assert.equal(record.targets, undefined)
            }
          }
        }
      }
    }
    for (const [type, name] of [
      ["training", "makata-qlora-full.ipynb"],
      ["evaluation", "makata-post-training.ipynb"],
    ]) {
      const notebook = await readFile(join(directory, name))
      assert.throws(
        () =>
          verifiedCycleSourceBundle(
            Buffer.concat([notebook, Buffer.from(" ")]),
            evidence.artifacts[type]
          ),
        /checksum mismatch/
      )
      assert.throws(
        () =>
          verifiedCycleSourceBundle(notebook, {
            ...evidence.artifacts[type],
            source_bundle_sha256: "0".repeat(64),
          }),
        /bundle checksum mismatch/
      )
    }
    const decision = await readFile(
      join(directory, study.decisions[0].file),
      "utf8"
    )
    assert.match(decision, /Retrospective documentation/)
    assert.match(decision, /not satisfied/)
    assert.match(decision, /Supporting evidence/)
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
})
