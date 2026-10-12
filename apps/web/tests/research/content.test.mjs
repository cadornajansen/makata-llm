import test from "node:test"
import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { articles } from "../../lib/research/catalog.ts"
import { sources } from "../../lib/research/sources.ts"
import { extractOutline } from "../../lib/research/outline.ts"

test("catalog connects eight unique articles and real source entries", () => {
  const slugs = new Set(articles.map(({ slug }) => slug))
  assert.equal(slugs.size, 8)
  for (const article of articles) {
    assert.ok(article.abstract.length > 80)
    assert.ok(article.objectives.length >= 3)
    for (const related of article.related)
      assert.ok(slugs.has(related), related)
    for (const id of article.sources) {
      assert.ok(sources[id], `${article.slug}: missing source ${id}`)
      assert.equal(new URL(sources[id].url).protocol, "https:")
    }
  }
})

test("outline ignores code and gives repeated headings unique fragment IDs", () => {
  assert.deepEqual(
    extractOutline("## One\n```python\n## Not a section\n```\n### Two\n## One"),
    [
      { id: "one", title: "One", level: 2 },
      { id: "two", title: "Two", level: 3 },
      { id: "one-1", title: "One", level: 2 },
    ]
  )
})

for (const article of articles) {
  test(`${article.slug}: article, outline and diagram contract`, async () => {
    const body = await readFile(
      new URL(`../../content/research/${article.slug}.mdx`, import.meta.url),
      "utf8"
    )
    const outline = extractOutline(body)
    assert.ok(
      outline.length >= 10,
      "Article should develop its topics as sections"
    )
    assert.equal(new Set(outline.map(({ id }) => id)).size, outline.length)
    const prose = body.replace(/^(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1\s*$/gm, "")
    assert.doesNotMatch(
      prose,
      /^# /m,
      "Title is rendered once by the article shell"
    )
    assert.doesNotMatch(prose, /(?:\bTODO\b|\[PLACEHOLDER\]|coming soon)/i)
    assert.ok(body.includes("## Key takeaways"), "Missing takeaways")
    assert.match(body, /[Mm]isconception/)
    const imports = [
      ...body.matchAll(
        /import\s+\{([^}]+)\}\s+from\s+["']@\/components\/research\/diagrams\/([^"']+)["']/g
      ),
    ]
    assert.ok(imports.length > 0, "No interactive explanations")
    for (const [, names, file] of imports) {
      const diagramSource = await readFile(
        new URL(
          `../../components/research/diagrams/${file}.tsx`,
          import.meta.url
        ),
        "utf8"
      )
      for (const name of names
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean)) {
        if (file === "lazy") {
          const loader = diagramSource.match(
            new RegExp(
              `export const ${name} = dynamic\\(\\(\\) =>\\s*import\\(["']\\./([^"']+)["']\\)\\.then\\(\\s*\\(module\\) => module\\.${name}\\s*\\)\\s*\\)`
            )
          )
          assert.ok(loader, `Missing lazy diagram loader ${name}`)
          const implementation = await readFile(
            new URL(
              `../../components/research/diagrams/${loader[1]}.tsx`,
              import.meta.url
            ),
            "utf8"
          )
          assert.ok(
            implementation.includes(`function ${name}(`),
            `Missing diagram ${name}`
          )
          assert.doesNotMatch(
            diagramSource,
            /ssr:\s*false/,
            "Diagrams must retain their server-rendered initial state"
          )
        } else {
          assert.ok(
            diagramSource.includes(`function ${name}(`),
            `Missing diagram ${name}`
          )
        }
        assert.ok(body.includes(`<${name}`), `Unused diagram ${name}`)
      }
    }
  })
}

test("tokenization fixtures preserve text and document exact provenance", async () => {
  const fixture = JSON.parse(
    await readFile(
      new URL("../../lib/research/tokenization.json", import.meta.url),
      "utf8"
    )
  )
  assert.equal(fixture.model, "Qwen/Qwen3-0.6B")
  assert.match(fixture.revision, /^[a-f0-9]{40}$/)
  assert.equal(fixture.addSpecialTokens, false)
  for (const example of fixture.examples) {
    assert.equal(example.ids.length, example.pieces.length)
    assert.equal(example.pieces.join(""), example.text)
    assert.ok(example.ids.every(Number.isInteger))
  }
})
