# Makata

**Building the foundations of Philippine intelligence.**

Makata is an independent Filipino artificial intelligence research initiative focused on Philippine languages, cultural context, and local knowledge. Its name comes from the Filipino word for _poet_: a reminder that language carries more than information.

Our long-term ambition is to help develop the scientific and engineering capabilities needed to train, evaluate, and operate Philippine-centered language models. We begin with Filipino and Taglish, with other Philippine languages remaining an exploratory direction as expertise and appropriately sourced data become available.

**Current stage: Foundations.** This repository contains Makata's public website. No Makata model has been trained or publicly released, and no research results are claimed. Makata has no confirmed institutional affiliation, funding, partnership, or endorsement.

## Why this work matters

Philippine participation in AI should include the ability to investigate and develop the underlying technology. Makata's research direction brings together three concerns:

- **Language representation:** understanding Filipino, code-switching, and the contexts in which people use them.
- **Research capacity:** developing practical expertise in datasets, neural networks, training, and evaluation.
- **Technological independence:** progressively building the ability to make informed decisions about models, data, and computing infrastructure.

International research and open-weight models are valuable foundations for this work. Independence is a capability to develop through evidence and collaboration, not a claim that external technology has no role.

## Research directions

These are intended areas of investigation, not completed projects.

| Direction                    | Questions to investigate                                                                                    |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Philippine-language modeling | How well do models understand and generate Filipino and Taglish in context?                                 |
| Dataset engineering          | How can language data be sourced, licensed, cleaned, and documented responsibly?                            |
| Training and adaptation      | What changes through controlled adaptation of existing models, and what would original pretraining require? |
| Independent evaluation       | How can improvements, regressions, and limitations be measured reproducibly?                                |
| Efficient local AI           | Which model and inference choices make experiments practical on accessible hardware?                        |

### What different methods establish

| Method                             | What it means for Makata                                                                                                                      |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| External model API                 | Application development or an experimental comparison using a provider's model. It does not establish model ownership or training capability. |
| Adaptation of an open-weight model | Research that changes an existing pretrained model. The underlying model's external provenance must remain explicit.                          |
| Pretraining from scratch           | Training newly initialized model weights. This requires separate work on data, tokenization, architecture, computing, and evaluation.         |

A fine-tuned model must never be presented as an independently developed Philippine foundation model.

### Research standards

Future experiment reports should identify model versions, dataset provenance and licenses, preprocessing, configurations, evaluation methods, compute costs, and limitations. Results should report regressions alongside improvements. Personal data and restricted material require appropriate handling before inclusion in any dataset.

The next research work is expected to establish baselines and assess data suitability. Original pretraining remains a longer-term objective. No training framework, dataset pipeline, or model-serving backend is included in this website release.

## What exists today

| Area                             | Status                                                        |
| -------------------------------- | ------------------------------------------------------------- |
| Public identity and website      | Implemented in this repository; deployment is a separate step |
| Research environment             | Not yet implemented                                           |
| Curated training dataset         | Not yet available                                             |
| Baseline evaluation              | Not yet completed                                             |
| Trained or released Makata model | None                                                          |
| Published research results       | None                                                          |

## Repository

```text
makata-llm/
├── apps/web/                    # Public Next.js website
├── packages/ui/                 # Shared shadcn components and Tailwind theme
├── packages/eslint-config/      # Shared lint rules
├── packages/typescript-config/  # Shared TypeScript configuration
├── pnpm-workspace.yaml
└── turbo.json
```

The website uses Next.js App Router, React, TypeScript, Tailwind CSS, and the existing shadcn Base Nova preset. Its content is server-rendered. Two isolated client components handle Lenis scrolling and the native Canvas particle background; neither requires a backend.

Touch scrolling remains native. Reduced-motion preferences disable enhanced scrolling and render a still particle frame. Styling uses Tailwind utilities and the shared global theme. Google Sans is served locally after the build; its font download requires network access during building. The generated social card uses the image renderer's bundled Noto Sans because that renderer does not support Google Sans's ligature tables.

### Run locally

Use **Node.js 24.x** and **pnpm 11.25.0**, pinned in the root manifest. With Corepack available:

```powershell
git clone https://github.com/cadornajansen/makata-llm.git
cd makata-llm
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

Open [localhost:3000](http://localhost:3000).

### Verify a production build

From the repository root:

```powershell
pnpm lint
pnpm typecheck
pnpm build
pnpm --filter web start
```

Stop the development server before starting the production server on the same port. Check desktop and mobile layouts, keyboard navigation, section links, collaboration email, and reduced-motion behavior.

### Search metadata

`apps/web/lib/site.ts` is the shared source for the public name, description, and canonical URL. The app generates canonical, Open Graph, and Twitter metadata, a social image, `/robots.txt`, `/sitemap.xml`, and factual Organization/WebSite structured data. The sitemap lists the homepage, not its fragment links.

These provide crawl and presentation information; they do not establish search indexing or rankings. There are no fabricated reviews, model results, institutional relationships, or publication claims in the structured data.

## Deploy to Vercel

Import this repository with the following settings:

| Setting                                         | Value                                  |
| ----------------------------------------------- | -------------------------------------- |
| Framework preset                                | Next.js                                |
| Root directory                                  | `apps/web`                             |
| Include source files outside the root directory | Enabled, for shared workspace packages |
| Node.js version                                 | `24.x`                                 |
| Environment variable                            | `ENABLE_EXPERIMENTAL_COREPACK=1`       |
| Install command                                 | `pnpm install --frozen-lockfile`       |
| Build command                                   | `pnpm build`                           |
| Output directory                                | Next.js default (`.next`)              |

Corepack uses the root `packageManager` field to select pnpm. Next.js already transpiles the shared UI package. No database, API key, or inference service is required.

The intended address is **`https://makata-llm.vercel.app`**, subject to availability. If the assigned production address differs, update `site.url` in `apps/web/lib/site.ts` and rebuild before publishing.

After deployment:

1. Confirm the production homepage is publicly accessible and its canonical URL matches the final domain.
2. Open `/robots.txt`, `/sitemap.xml`, and the social image URL in the page metadata.
3. Verify the property in Google Search Console and submit `/sitemap.xml`.

Vercel's standard preview deployments carry a noindex response header; see [Vercel's preview indexing documentation](https://vercel.com/kb/guide/are-vercel-preview-deployment-indexed-by-search-engines). Check the actual production response rather than assuming a preview represents the public site.

## Collaboration

Researchers, language specialists, universities, engineers, and prospective institutional collaborators are welcome to discuss evaluation methods, data suitability, and practical research directions. Opening an issue with a concrete question or reproducible website bug is a useful starting point.

For collaboration inquiries: [jansencadorna5@gmail.com](mailto:jansencadorna5@gmail.com).

Discussions and outreach do not imply an existing partnership or institutional endorsement.

## Licensing

A project-wide license has not yet been specified. Third-party components retain their respective licenses. The Google Sans Open Font License is included in [apps/web/public/licenses/google-sans-OFL.txt](apps/web/public/licenses/google-sans-OFL.txt).
