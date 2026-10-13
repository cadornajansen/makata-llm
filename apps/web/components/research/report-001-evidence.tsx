import evidence from "@/content/research/studies/001-tagalog-comprehension.evidence.json"
import { ResultComparison } from "./study-elements"

export function Report001Results(): React.ReactElement {
  return <ResultComparison results={evidence.models} />
}

export function Report001Revisions(): React.ReactElement {
  const entries = [
    ...evidence.models.flatMap((model) => [
      [`${model.model} · model`, model.model_revision],
      [`${model.tokenizer} · tokenizer`, model.tokenizer_revision],
    ]),
    [
      `${evidence.dataset.repository} · ${evidence.dataset.subset}`,
      evidence.dataset.revision,
    ],
    ["FilBench Lighteval fork", evidence.protocol.filbench_revision],
  ]
  return (
    <dl className="my-7 flex flex-col gap-5 text-sm">
      {entries.map(([label, sha]) => (
        <div key={label}>
          <dt className="mb-1 font-medium">{label}</dt>
          <dd className="font-mono text-xs leading-relaxed break-all text-muted-foreground">
            {sha}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function Report001Provenance(): React.ReactElement {
  return (
    <dl className="my-7 flex flex-col gap-5 text-sm">
      {[
        [
          "Frozen source snapshot · SHA-256",
          evidence.artifacts.source_bundle_sha256,
        ],
        [
          "Original result archive · SHA-256 (locally retained)",
          evidence.verification.archive_sha256,
        ],
        [
          "Frozen execution profile · SHA-256 (locally retained)",
          evidence.verification.execution_profile_sha256,
        ],
        ...evidence.models.map((model) => [
          `${model.model} · per-example record SHA-256 (locally retained)`,
          model.samples_sha256,
        ]),
      ].map(([label, hash]) => (
        <div key={label}>
          <dt className="mb-1 font-medium">{label}</dt>
          <dd className="font-mono text-xs leading-relaxed break-all text-muted-foreground">
            {hash}
          </dd>
        </div>
      ))}
    </dl>
  )
}
