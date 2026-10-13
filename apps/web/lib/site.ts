// Shared canonical origin for pages, structured data, and social previews.
export const site = {
  name: "Makata",
  url: "https://makata.jansencadorna.com",
  title: "Makata — Philippine-language AI research",
  description:
    "An independent Filipino AI research initiative exploring language models, datasets, and evaluation for Filipino and Taglish. Foundational research, Philippine roots.",
} as const

export const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${site.url}/#organization`,
      name: site.name,
      url: site.url,
      description: site.description,
      logo: `${site.url}/makata.svg`,
      email: "jansencadorna5@gmail.com",
    },
    {
      "@type": "WebSite",
      "@id": `${site.url}/#website`,
      name: site.name,
      url: site.url,
      description: site.description,
      inLanguage: "en",
      publisher: { "@id": `${site.url}/#organization` },
    },
  ],
} as const
