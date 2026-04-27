import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'

/**
 * Markdown renderer for BRI610 cards.
 *
 *   Markdown body         → react-markdown
 *   $..$, $$..$$          → remark-math + rehype-katex
 *   inline <svg>, <figure> → rehype-raw (allows trusted HTML — content is authored
 *                            by us / by the LLM with strict prompts that don't
 *                            permit <script>; safe for our threat model)
 */
export default function Markdown({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeRaw, rehypeKatex]}
      components={{
        // Pass-through for figure / svg / details / summary so we can author
        // schematic illustrations inline. Apply academic figure styling.
        figure: ({ node, ...props }) => (
          <figure
            style={{
              margin: '1.4em 0',
              padding: '0.5em 0',
              textAlign: 'center',
            }}
            {...props}
          />
        ),
        figcaption: ({ node, ...props }) => (
          <figcaption
            style={{
              fontSize: '0.85em',
              color: 'var(--color-text-dim)',
              fontStyle: 'italic',
              marginTop: '0.5em',
              fontFamily: 'var(--font-sans)',
              letterSpacing: '0.01em',
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
