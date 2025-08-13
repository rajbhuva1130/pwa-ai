import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ...inside MessageBubble:
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    a: ({ href, children, ...props }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children && children.length ? children : href}
      </a>
    ),
    code: ({ inline, className, children, ...props }) =>
      inline ? (
        <code className={className} {...props}>{children}</code>
      ) : (
        <pre className="code-block"><code {...props}>{children}</code></pre>
      ),
  }}
>
  {content}
</ReactMarkdown>
