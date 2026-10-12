import { isValidElement, type ComponentProps, type ReactNode } from "react"
import Link from "next/link"
import type { MDXComponents } from "mdx/types"
import { CodeCopy } from "@/components/research/code-copy"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@workspace/ui/components/table"
import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Separator } from "@workspace/ui/components/separator"

function textContent(node: ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node)
  if (Array.isArray(node)) return node.map(textContent).join("")
  if (isValidElement<{ children?: ReactNode }>(node))
    return textContent(node.props.children)
  return ""
}

function Heading({
  children,
  id,
  ...props
}: ComponentProps<"h2">): React.ReactElement {
  return (
    <h2
      {...props}
      id={id}
      className="group mt-16 mb-6 scroll-mt-28 text-2xl leading-tight font-medium tracking-tight text-foreground sm:text-3xl"
    >
      <a
        href={`#${id}`}
        className="decoration-border underline-offset-8 hover:underline"
      >
        {children}
        <span
          className="ml-2 text-base text-muted-foreground opacity-0 group-hover:opacity-100"
          aria-hidden="true"
        >
          #
        </span>
      </a>
    </h2>
  )
}

const components: MDXComponents = {
  h2: Heading,
  h3: ({ children, ...props }) => (
    <h3
      {...props}
      className="mt-10 mb-4 scroll-mt-28 text-xl font-medium tracking-tight text-foreground"
    >
      {children}
    </h3>
  ),
  h4: ({ children, ...props }) => (
    <h4
      {...props}
      className="mt-8 mb-3 scroll-mt-28 text-lg font-medium text-foreground"
    >
      {children}
    </h4>
  ),
  p: ({ children, ...props }) => (
    <p {...props} className="my-5 leading-[1.85] text-pretty">
      {children}
    </p>
  ),
  a: ({ href = "", children, ...props }) =>
    href.startsWith("/") ? (
      <Link
        href={href}
        {...props}
        className="font-medium text-primary underline decoration-primary/35 underline-offset-4 hover:decoration-primary"
      >
        {children}
      </Link>
    ) : (
      <a
        href={href}
        {...props}
        className="font-medium text-primary underline decoration-primary/35 underline-offset-4 hover:decoration-primary"
      >
        {children}
      </a>
    ),
  ul: ({ children }) => (
    <ul className="my-6 flex list-disc flex-col gap-3 pl-6 marker:text-primary">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="my-6 flex list-decimal flex-col gap-3 pl-6 marker:font-medium marker:text-primary">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="pl-1 leading-[1.8]">{children}</li>,
  strong: ({ children }) => (
    <strong className="font-semibold text-foreground">{children}</strong>
  ),
  blockquote: ({ children }) => (
    <Alert className="my-8">
      <AlertDescription className="text-base leading-relaxed [&_p]:my-1">
        {children}
      </AlertDescription>
    </Alert>
  ),
  hr: () => <Separator className="my-12" />,
  pre: ({ children }) => {
    const text = textContent(children)
    const language = isValidElement<{ className?: string }>(children)
      ? children.props.className?.replace("language-", "")
      : undefined
    return (
      <div className="my-8 min-w-0 overflow-hidden rounded-xl border bg-secondary/60">
        <div className="flex items-center justify-between gap-4 border-b px-4 py-2">
          <span className="font-mono text-xs text-muted-foreground">
            {language || "Example"}
          </span>
          <CodeCopy text={text} />
        </div>
        <pre
          tabIndex={0}
          aria-label={`${language || "Example"} code`}
          data-lenis-prevent
          className="overflow-x-auto overscroll-x-contain p-5 font-mono text-[13px] leading-[1.8] text-foreground outline-offset-[-3px] focus-visible:outline-2 focus-visible:outline-ring [&_code]:bg-transparent [&_code]:p-0"
        >
          {children}
        </pre>
      </div>
    )
  },
  code: ({ children, ...props }) => (
    <code
      {...props}
      className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[0.88em] text-foreground"
    >
      {children}
    </code>
  ),
  table: ({ children }) => (
    <div className="my-8 min-w-0" data-lenis-prevent>
      <Table className="text-sm leading-relaxed">{children}</Table>
    </div>
  ),
  thead: TableHeader,
  tbody: TableBody,
  tr: TableRow,
  th: ({ children, ...props }) => (
    <TableHead
      {...props}
      className="h-auto p-3 align-top font-semibold whitespace-normal"
    >
      {children}
    </TableHead>
  ),
  td: ({ children, ...props }) => (
    <TableCell {...props} className="p-3 align-top whitespace-normal">
      {children}
    </TableCell>
  ),
}

export function useMDXComponents(): MDXComponents {
  return components
}
