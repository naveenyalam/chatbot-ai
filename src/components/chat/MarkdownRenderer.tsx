"use client";

import React from "react";
import { CodeBlock } from "./CodeBlock";
import { AlertCircle, Lightbulb, Info, AlertTriangle, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
  content: string;
}

interface Block {
  type: "code" | "table" | "heading" | "blockquote" | "ul" | "ol" | "hr" | "paragraph";
  content: string;
  lang?: string;
  level?: number;
  items?: string[];
  rows?: string[][];
}

// Escapes HTML tags to prevent XSS injection
const escapeHtml = (text: string): string => {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
};

// Formats inline markdown tokens securely using styling classes
export const parseInlineToHtml = (text: string): string => {
  let escaped = escapeHtml(text);

  // 1. Inline code: `code`
  escaped = escaped.replace(
    /`([^`]+)`/g,
    '<code class="px-1.5 py-0.5 rounded bg-surface-secondary text-accent font-mono text-[11px] md:text-xs border border-border-subtle/55">$1</code>'
  );

  // 2. Bold: **text** or __text__
  escaped = escaped.replace(
    /\*\*([^*]+)\*\*/g,
    '<strong class="font-bold text-text-primary">$1</strong>'
  );
  escaped = escaped.replace(
    /__([^_]+)__/g,
    '<strong class="font-bold text-text-primary">$1</strong>'
  );

  // 3. Italic: *text* or _text_
  escaped = escaped.replace(
    /\*([^*]+)\*/g,
    '<em class="italic text-text-primary/85">$1</em>'
  );
  escaped = escaped.replace(
    /_([^_]+)_/g,
    '<em class="italic text-text-primary/85">$1</em>'
  );

  // 4. Links: [text](url)
  escaped = escaped.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-accent hover:underline font-semibold">$1</a>'
  );

  return escaped;
};

// Line-by-line block parser
export function parseMarkdown(text: string): Block[] {
  const lines = text.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Code Block
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++; // skip ending ```
      blocks.push({
        type: "code",
        content: codeLines.join("\n"),
        lang: lang || "text",
      });
      continue;
    }

    // 2. Blockquote / Alert callouts
    if (trimmed.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        const l = lines[i].trim();
        const content = l.slice(1).startsWith(" ") ? l.slice(2) : l.slice(1);
        quoteLines.push(content);
        i++;
      }
      blocks.push({
        type: "blockquote",
        content: quoteLines.join("\n"),
      });
      continue;
    }

    // 3. Horizontal Rule
    if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
      blocks.push({
        type: "hr",
        content: "",
      });
      i++;
      continue;
    }

    // 4. Headings
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length,
        content: headingMatch[2],
      });
      i++;
      continue;
    }

    // 5. Unordered Lists
    const ulMatch = line.match(/^([\-*])\s+(.*)$/);
    if (ulMatch) {
      const items: string[] = [];
      while (i < lines.length) {
        const itemMatch = lines[i].match(/^[\-*]\s+(.*)$/);
        if (!itemMatch) break;
        items.push(itemMatch[1]);
        i++;
      }
      blocks.push({
        type: "ul",
        content: "",
        items,
      });
      continue;
    }

    // 6. Ordered Lists
    const olMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (olMatch) {
      const items: string[] = [];
      while (i < lines.length) {
        const itemMatch = lines[i].match(/^\d+\.\s+(.*)$/);
        if (!itemMatch) break;
        items.push(itemMatch[1]);
        i++;
      }
      blocks.push({
        type: "ol",
        content: "",
        items,
      });
      continue;
    }

    // 7. Table Structure
    if (
      trimmed.startsWith("|") &&
      i < lines.length - 1 &&
      lines[i + 1].trim().match(/^\|[\s\-:|]+$/)
    ) {
      const headerRow = trimmed
        .split("|")
        .map((c) => c.trim())
        .filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
      
      i += 2; // skip header & divider lines
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const rowCells = lines[i]
          .trim()
          .split("|")
          .map((c) => c.trim())
          .filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
        rows.push(rowCells);
        i++;
      }
      blocks.push({
        type: "table",
        content: "",
        rows: [headerRow, ...rows],
      });
      continue;
    }

    // 8. Empty spacing
    if (trimmed === "") {
      i++;
      continue;
    }

    // 9. Standard Paragraphs
    const paraLines: string[] = [];
    while (i < lines.length) {
      const l = lines[i];
      const t = l.trim();
      if (
        t === "" ||
        t.startsWith("```") ||
        t.startsWith(">") ||
        t === "---" ||
        t.match(/^#{1,6}\s/) ||
        t.match(/^[\-*]\s/) ||
        t.match(/^\d+\.\s/) ||
        (t.startsWith("|") &&
          i < lines.length - 1 &&
          lines[i + 1].trim().match(/^\|[\s\-:|]+$/))
      ) {
        break;
      }
      paraLines.push(l);
      i++;
    }
    blocks.push({
      type: "paragraph",
      content: paraLines.join("\n"),
    });
  }

  return blocks;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const blocks = parseMarkdown(content);

  const renderBlock = (block: Block, index: number) => {
    switch (block.type) {
      case "code":
        return (
          <CodeBlock
            key={index}
            code={block.content}
            language={block.lang}
          />
        );

      case "heading": {
        const textHtml = parseInlineToHtml(block.content);
        const level = block.level || 1;
        const tagClasses = cn(
          "font-bold text-text-primary tracking-tight mt-6 mb-3",
          level === 1 && "text-2xl md:text-3xl border-b border-border-subtle/40 pb-2",
          level === 2 && "text-xl md:text-2xl",
          level === 3 && "text-lg md:text-xl",
          level === 4 && "text-base md:text-lg",
          level >= 5 && "text-sm md:text-base text-text-muted"
        );
        const Tag = `h${level}` as "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
        return (
          <Tag
            key={index}
            className={tagClasses}
            dangerouslySetInnerHTML={{ __html: textHtml }}
          />
        );
      }

      case "blockquote": {
        const text = block.content;
        const alertMatch = text.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n([\s\S]*)$/i);
        
        if (alertMatch) {
          const type = alertMatch[1].toUpperCase();
          const innerText = alertMatch[2];
          const innerHtml = parseInlineToHtml(innerText);
          
          let alertStyle = "border-blue-500/30 bg-blue-500/5 text-blue-300";
          let Icon = Info;
          let label = "Note";

          if (type === "TIP") {
            alertStyle = "border-emerald-500/30 bg-emerald-500/5 text-emerald-300";
            Icon = Lightbulb;
            label = "Tip";
          } else if (type === "IMPORTANT") {
            alertStyle = "border-violet-500/30 bg-violet-500/5 text-violet-300";
            Icon = AlertCircle;
            label = "Important";
          } else if (type === "WARNING") {
            alertStyle = "border-amber-500/30 bg-amber-500/5 text-amber-300";
            Icon = AlertTriangle;
            label = "Warning";
          } else if (type === "CAUTION") {
            alertStyle = "border-rose-500/30 bg-rose-500/5 text-rose-300";
            Icon = ShieldAlert;
            label = "Caution";
          }

          return (
            <div
              key={index}
              className={cn(
                "my-5 p-4 rounded-xl border flex gap-3 text-xs md:text-sm leading-relaxed shadow-sm",
                alertStyle
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold mb-1 tracking-wide uppercase text-[10px]">{label}</p>
                <div dangerouslySetInnerHTML={{ __html: innerHtml }} />
              </div>
            </div>
          );
        }

        const quoteHtml = parseInlineToHtml(text);
        return (
          <blockquote
            key={index}
            className="my-4 pl-4 border-l-3 border-accent/40 bg-surface-secondary/20 py-2 rounded-r-lg italic text-text-muted text-xs md:text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: quoteHtml }}
          />
        );
      }

      case "ul":
        return (
          <ul key={index} className="list-disc pl-6 my-3 space-y-1.5 text-text-primary text-xs md:text-sm">
            {block.items?.map((item, idx) => (
              <li
                key={idx}
                dangerouslySetInnerHTML={{ __html: parseInlineToHtml(item) }}
              />
            ))}
          </ul>
        );

      case "ol":
        return (
          <ol key={index} className="list-decimal pl-6 my-3 space-y-1.5 text-text-primary text-xs md:text-sm">
            {block.items?.map((item, idx) => (
              <li
                key={idx}
                dangerouslySetInnerHTML={{ __html: parseInlineToHtml(item) }}
              />
            ))}
          </ol>
        );

      case "hr":
        return <hr key={index} className="my-6 border-t border-border-subtle/50" />;

      case "table":
        return (
          <div key={index} className="overflow-x-auto w-full my-5 rounded-xl border border-border-subtle bg-surface-secondary/15">
            <table className="w-full text-left border-collapse text-xs md:text-sm">
              <thead>
                <tr className="border-b border-border-subtle bg-surface-secondary/45 text-text-muted">
                  {block.rows?.[0].map((cell, idx) => (
                    <th
                      key={idx}
                      className="px-4 py-3 font-semibold"
                      dangerouslySetInnerHTML={{ __html: parseInlineToHtml(cell) }}
                    />
                  ))}
                </tr>
              </thead>
              <tbody>
                {block.rows?.slice(1).map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className="border-b border-border-subtle/50 hover:bg-surface-secondary/10 transition-colors last:border-0"
                  >
                    {row.map((cell, cellIdx) => (
                      <td
                        key={cellIdx}
                        className="px-4 py-3 leading-relaxed text-text-primary"
                        dangerouslySetInnerHTML={{ __html: parseInlineToHtml(cell) }}
                      />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case "paragraph":
      default: {
        const textHtml = parseInlineToHtml(block.content);
        return (
          <p
            key={index}
            className="text-xs md:text-sm text-text-primary leading-relaxed my-3 whitespace-pre-line"
            dangerouslySetInnerHTML={{ __html: textHtml }}
          />
        );
      }
    }
  };

  return <div className="space-y-1 w-full max-w-full overflow-hidden">{blocks.map(renderBlock)}</div>;
}
