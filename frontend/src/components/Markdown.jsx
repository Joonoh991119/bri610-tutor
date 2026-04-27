import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'
import katex from 'katex'
import { fromHtml } from 'hast-util-from-html'
import { visit } from 'unist-util-visit'

/**
 * Custom rehype plugin that runs AFTER rehype-raw has parsed HTML strings
 * into the HAST tree. At that point, text nodes inside <figcaption>,
 * <details>, <summary>, table cells, etc. are plain text nodes containing
 * raw `$...$` / `$$...$$` delimiters AND `**bold**` / `*italic*` markers
 * that remark-math / remark-gfm never saw (because they were inside opaque
 * HTML blocks during the remark phase).
 *
 * This plugin walks every text node and tokenises it in priority order:
 *   1. $$...$$ display math → KaTeX HTML → HAST via fromHtml
 *   2. $..$   inline math   → KaTeX HTML → HAST via fromHtml
 *   3. **...** bold         → <strong> element node
 *   4. *...*   italic       → <em> element node
 *   5. plain remainder      → text node
 *
 * Nodes are skipped when the parent is <code>, <pre>, <a>, <strong>, or
 * <em> to avoid breaking code samples, links, and double-wrapping.
 *
 * Uses type:'element' HAST nodes (via fromHtml for math, manual construction
 * for emphasis) — NOT type:'raw', which react-markdown v10 converts back to
 * literal strings.
 */
function rehypeKatexInRawHtml() {
  // Tags where we must not touch text nodes
  const SKIP_TAGS = new Set(['code', 'pre', 'a', 'strong', 'em'])

  /**
   * Tokenise `value` into segments tagged by kind:
   *   { kind: 'math-display' | 'math-inline' | 'bold' | 'italic' | 'text', raw, inner }
   * Priority: $$...$$ > $..$  > **...** > *...*  > text
   */
  function tokenise(value) {
    // Combined regex with named groups, ordered by priority
    // (?<dmath>  $$...$$  ) — allows newlines inside display math blocks
    // (?<imath>  $...$    ) — requires non-space after opening $ to avoid currency matches
    // (?<bold>   **...**  )  — must come before italic
    // (?<italic> *...*    )
    const re = /(?<dmath>\$\$[\s\S]+?\$\$)|(?<imath>\$(?=[^\s$])(?:[^$\n]|\\\$)+?(?<=[^\s\\])\$)|(?<bold>\*\*(?:[^*]|\*(?!\*))+?\*\*)|(?<italic>\*(?:[^*\n]+?)\*)/gs
    const tokens = []
    let last = 0
    let m
    while ((m = re.exec(value)) !== null) {
      if (m.index > last) {
        tokens.push({ kind: 'text', raw: value.slice(last, m.index) })
      }
      if (m.groups.dmath !== undefined) {
        // strip opening and closing $$
        tokens.push({ kind: 'math-display', raw: m[0], inner: m[0].slice(2, -2) })
      } else if (m.groups.imath !== undefined) {
        tokens.push({ kind: 'math-inline', raw: m[0], inner: m[0].slice(1, -1) })
      } else if (m.groups.bold !== undefined) {
        tokens.push({ kind: 'bold', raw: m[0], inner: m[0].slice(2, -2) })
      } else if (m.groups.italic !== undefined) {
        tokens.push({ kind: 'italic', raw: m[0], inner: m[0].slice(1, -1) })
      }
      last = re.lastIndex
    }
    if (last < value.length) tokens.push({ kind: 'text', raw: value.slice(last) })
    return tokens
  }

  /**
   * Recursively convert a token's inner text into child HAST nodes,
   * so that e.g. **bold with $math$** works correctly.
   */
  function tokensToHast(tokens) {
    const nodes = []
    for (const tok of tokens) {
      if (tok.kind === 'text') {
        if (tok.raw) nodes.push({ type: 'text', value: tok.raw })
      } else if (tok.kind === 'math-display' || tok.kind === 'math-inline') {
        try {
          const html = katex.renderToString(tok.inner, {
            throwOnError: false,
            displayMode: tok.kind === 'math-display',
          })
          const fragment = fromHtml(html, { fragment: true })
          nodes.push(...fragment.children)
        } catch {
          nodes.push({ type: 'text', value: tok.raw })
        }
      } else if (tok.kind === 'bold') {
        // Recursively handle nested tokens inside the bold span
        const innerTokens = tokenise(tok.inner)
        const innerNodes = tokensToHast(innerTokens)
        nodes.push({
          type: 'element',
          tagName: 'strong',
          properties: {},
          children: innerNodes.length ? innerNodes : [{ type: 'text', value: tok.inner }],
        })
      } else if (tok.kind === 'italic') {
        const innerTokens = tokenise(tok.inner)
        const innerNodes = tokensToHast(innerTokens)
        nodes.push({
          type: 'element',
          tagName: 'em',
          properties: {},
          children: innerNodes.length ? innerNodes : [{ type: 'text', value: tok.inner }],
        })
      }
    }
    return nodes
  }

  return (tree) => {
    visit(tree, 'text', (node, index, parent) => {
      if (!node.value) return
      // Skip protected contexts (tag name or class-based katex spans)
      if (parent && SKIP_TAGS.has(parent.tagName)) return
      // Skip nodes already inside a rendered KaTeX element
      if (parent && parent.properties &&
          Array.isArray(parent.properties.className) &&
          parent.properties.className.some(c => c === 'katex' || c === 'katex-html' || c === 'katex-display')) return

      const tokens = tokenise(node.value)

      // Fast-path: only a single 'text' token means nothing to process
      if (tokens.length === 1 && tokens[0].kind === 'text') return

      const children = tokensToHast(tokens)
      if (!children.length) return

      parent.children.splice(index, 1, ...children)
      return index + children.length
    })
  }
}

/**
 * Markdown renderer for BRI610 cards.
 *
 *   Markdown body         → react-markdown
 *   $..$, $$..$$          → remark-math + rehype-katex
 *   inline <svg>, <figure> → rehype-raw (allows trusted HTML — content is authored
 *                            by us / by the LLM with strict prompts that don't
 *                            permit <script>; safe for our threat model)
 *
 * Cross-summary hyperlinks: a markdown link with href `#summary?lecture=L#`
 * is intercepted as in-app navigation — switches to summary tab + selects
 * lecture in localStorage. No full page reload.
 */
function navigateInApp(href, e) {
  // Match #summary?lecture=L3 form
  const m = href && href.match(/^#summary\?lecture=(L[2-8])/i)
  if (!m) return false
  e.preventDefault()
  try {
    localStorage.setItem('bri610.summary.lecture', m[1].toUpperCase())
    window.location.hash = 'summary'
    // Trigger a hashchange in case we're already on #summary
    window.dispatchEvent(new HashChangeEvent('hashchange'))
  } catch {}
  return true
}

export default function Markdown({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeRaw, rehypeKatexInRawHtml, rehypeKatex]}
      components={{
        a: ({ node, href, children, ...props }) => (
          <a
            href={href}
            onClick={(e) => navigateInApp(href, e)}
            {...props}
          >
            {children}
          </a>
        ),
        // Pass-through for figure / svg / details / summary so we can author
        // schematic illustrations inline. Apply academic figure styling.
        figure: ({ node, ...props }) => (
          <figure
            style={{
              margin: '2em auto',
              padding: '0.5em 0',
              textAlign: 'center',
              maxWidth: '100%',
            }}
            {...props}
          />
        ),
        figcaption: ({ node, ...props }) => (
          <figcaption
            style={{
              fontSize: '0.92em',
              color: 'var(--color-text)',
              fontStyle: 'normal',
              lineHeight: '1.6',
              textAlign: 'left',
              maxWidth: '90%',
              margin: '0 auto',
              padding: '0.4em 1em 0.5em',
              fontFamily: 'var(--font-sans)',
              letterSpacing: '0.01em',
              background: 'var(--color-surface-2)',
              borderRadius: '6px',
              borderLeft: '2px solid var(--color-accent-soft)',
            }}
            {...props}
          />
        ),
        svg: ({ node, ...props }) => (
          <svg
            style={{
              maxWidth: '100%',
              height: 'auto',
              display: 'block',
              margin: '0 auto',
            }}
            {...props}
          />
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
