import { createHash } from "node:crypto"
import { Buffer } from "node:buffer"
import process from "node:process"
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises"
import { resolve, dirname } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "../../..")
const slug = "001-tagalog-comprehension"
const evidencePath = `apps/web/content/research/studies/${slug}.evidence.json`

/** @param {Buffer | string} bytes @returns {string} */
export function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex")
}

/**
 * @param {Buffer} bytes
 * @param {{artifacts: {notebook_sha256: string, source_bundle_sha256: string}}} evidence
 * @returns {Buffer}
 */
export function verifiedSourceBundle(bytes, evidence) {
  if (sha256(bytes) !== evidence.artifacts.notebook_sha256)
    throw new Error(
      "Frozen notebook checksum mismatch; do not rebuild the historical snapshot."
    )
  const notebook = JSON.parse(bytes.toString("utf8"))
  if (
    notebook.cells.some(
      (cell) => cell.outputs?.length || cell.execution_count != null
    )
  )
    throw new Error("Public notebook must be output-free.")
  const bootstrap = notebook.cells
    .map((cell) => cell.source.join(""))
    .join("\n")
  const payload = bootstrap.match(/^PAYLOAD = '([A-Za-z0-9+/=]+)'$/m)?.[1]
  if (!payload)
    throw new Error("Frozen notebook has no recognized source payload.")
  const source = Buffer.from(payload, "base64")
  if (
    sha256(source) !== evidence.artifacts.source_bundle_sha256 ||
    notebook.metadata.makata.bundle_sha256 !==
      evidence.artifacts.source_bundle_sha256
  )
    throw new Error("Frozen source bundle checksum mismatch.")
  return source
}

/** @param {string} [destination] @returns {Promise<Record<string, string>>} */
export async function prepareStudyArtifacts(
  destination = resolve(repository, "apps/web/public/research-materials", slug)
) {
  // Only these reviewed files can become downloads. Never traverse research/runs.
  const allowlist = {
    "evidence.json": evidencePath,
    "makata-baselines.ipynb": "research/colab/makata-baselines.ipynb",
    "reproduce.md": "docs/research/report-001-reproduce.md",
    "0001-tagalog-reading-comprehension.md":
      "docs/research/decisions/0001-tagalog-reading-comprehension.md",
    "0002-baseline-model-selection.md":
      "docs/research/decisions/0002-baseline-model-selection.md",
    "0003-evaluation-protocol.md":
      "docs/research/decisions/0003-evaluation-protocol.md",
  }
  const files = new Map(
    await Promise.all(
      Object.entries(allowlist).map(async ([name, path]) => [
        name,
        await readFile(resolve(repository, path)),
      ])
    )
  )
  const evidence = JSON.parse(files.get("evidence.json").toString("utf8"))
  files.set(
    "source-snapshot.zip",
    verifiedSourceBundle(files.get("makata-baselines.ipynb"), evidence)
  )
  return writePublicMaterials(files, destination)
}

/** @param {Map<string, Buffer>} files @param {string} destination */
async function writePublicMaterials(files, destination) {
  for (const [name, bytes] of files) {
    if (name.endsWith(".zip")) continue
    if (
      /colab\.research\.google\.com\/drive\/|[A-Z]:[\\/]Users[\\/]|["'](?:access_token|api_key|password)["']\s*:/i.test(
        bytes.toString("utf8")
      )
    )
      throw new Error(`Private information found in public material: ${name}`)
  }
  const checksums = Object.fromEntries(
    [...files].map(([name, bytes]) => [name, sha256(bytes)])
  )
  files.set(
    "checksums.json",
    Buffer.from(
      JSON.stringify({ algorithm: "SHA-256", files: checksums }, null, 2) + "\n"
    )
  )
  await mkdir(destination, { recursive: true })
  const unexpected = (await readdir(destination)).filter(
    (name) => !files.has(name)
  )
  if (unexpected.length)
    throw new Error(
      `Unreviewed files in publication download directory: ${unexpected.join(", ")}`
    )
  for (const [name, bytes] of files)
    await writeFile(resolve(destination, name), bytes)
  return checksums
}

/** @param {Buffer} bytes @param {{notebook_sha256: string, source_bundle_sha256: string}} hashes */
export function verifiedCycleSourceBundle(bytes, hashes) {
  if (sha256(bytes) !== hashes.notebook_sha256)
    throw new Error(
      "Frozen notebook checksum mismatch; do not regenerate historical notebooks."
    )
  const notebook = JSON.parse(bytes.toString("utf8"))
  if (
    notebook.cells.some(
      (cell) => cell.outputs?.length || cell.execution_count != null
    )
  )
    throw new Error("Public notebook must be output-free.")
  const source = notebook.cells.map((cell) => cell.source.join("")).join("\n")
  // Preserve the two historical bootstrap formats without rebuilding either ZIP.
  const payload = source.match(
    /(?:PAYLOAD = |base64\.b64decode\()'([A-Za-z0-9+/=]+)'/
  )?.[1]
  if (!payload) throw new Error("Missing frozen source payload.")
  const bundle = Buffer.from(payload, "base64")
  if (sha256(bundle) !== hashes.source_bundle_sha256)
    throw new Error("Frozen source bundle checksum mismatch.")
  return bundle
}

/** @param {string} [destination] @returns {Promise<Record<string, string>>} */
export async function prepareCycleArtifacts(
  destination = resolve(
    repository,
    "apps/web/public/research-materials/002-aya-qlora-evaluation"
  )
) {
  const allowlist = {
    "evidence.json":
      "apps/web/content/research/studies/002-aya-qlora-evaluation.evidence.json",
    "makata-qlora-full.ipynb": "research/colab/makata-qlora-full.ipynb",
    "makata-post-training.ipynb": "research/colab/makata-post-training.ipynb",
    "reproduce.md": "docs/research/report-002-reproduce.md",
    "0004-exploratory-aya-adaptation.md":
      "docs/research/decisions/0004-exploratory-aya-adaptation.md",
  }
  const files = new Map(
    await Promise.all(
      Object.entries(allowlist).map(async ([name, path]) => [
        name,
        await readFile(resolve(repository, path)),
      ])
    )
  )
  const evidence = JSON.parse(files.get("evidence.json").toString("utf8"))
  files.set(
    "training-source-snapshot.zip",
    verifiedCycleSourceBundle(
      files.get("makata-qlora-full.ipynb"),
      evidence.artifacts.training
    )
  )
  files.set(
    "evaluation-source-snapshot.zip",
    verifiedCycleSourceBundle(
      files.get("makata-post-training.ipynb"),
      evidence.artifacts.evaluation
    )
  )
  return writePublicMaterials(files, destination)
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
) {
  const files = await prepareStudyArtifacts()
  console.log(
    `Prepared Report 001 materials (${Object.keys(files).length + 1} files).`
  )
  const cycle = await prepareCycleArtifacts()
  console.log(
    `Prepared Report 002 materials (${Object.keys(cycle).length + 1} files).`
  )
}
