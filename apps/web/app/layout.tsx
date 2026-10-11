import type { Metadata, Viewport } from "next"
import type { ReactElement, ReactNode } from "react"
import { Google_Sans } from "next/font/google"
import { SmoothScroll } from "@/components/smooth-scroll"
import { site, structuredData } from "@/lib/site"

import "@workspace/ui/globals.css"
const googleSans = Google_Sans({
  subsets: ["latin"],
  weight: "variable",
  style: "normal",
  display: "swap",
  fallback: ["Arial", "sans-serif"],
  // Next does not yet include automatic fallback metrics for Google Sans.
  adjustFontFallback: false,
  variable: "--font-google-sans",
})

const { title, description } = site

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title,
  description,
  applicationName: site.name,
  alternates: { canonical: "/" },
  openGraph: {
    title,
    description,
    url: "/",
    siteName: site.name,
    locale: "en_PH",
    type: "website",
  },
  twitter: { card: "summary_large_image", title, description },
}

export const viewport: Viewport = {
  themeColor: "#F5F6F8",
  colorScheme: "light",
}

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <html
      lang="en"
      dir="ltr"
      className={`${googleSans.variable} scroll-pt-8 font-sans antialiased scheme-light [scrollbar-color:var(--muted-foreground)_transparent] [scrollbar-width:thin] motion-safe:scroll-smooth forced-colors:[scrollbar-color:auto] forced-colors:[scrollbar-width:auto] [&.lenis]:h-auto [&.lenis]:scroll-auto`}
    >
      <body className="selection:bg-primary/15 motion-reduce:[&_*]:animate-none motion-reduce:[&_*]:transition-none [&_a:focus-visible]:outline-2 [&_a:focus-visible]:outline-offset-4 [&_a:focus-visible]:outline-ring">
        <SmoothScroll />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(structuredData).replace(/</g, "\\u003c"),
          }}
        />
        {children}
      </body>
    </html>
  )
}
