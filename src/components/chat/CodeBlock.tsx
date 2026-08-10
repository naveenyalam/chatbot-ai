"use client";

import React, { useState } from "react";
import { Check, Copy, ListOrdered } from "lucide-react";
import { cn } from "@/lib/utils";

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
}

export function CodeBlock({
  code,
  language = "text",
  showLineNumbers = true,
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [displayLineNumbers, setDisplayLineNumbers] = useState(showLineNumbers);

  const cleanCode = code.trim();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(cleanCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy code block", err);
    }
  };

  // Single-pass syntax highlighter — splits code into tokens ONCE using a
  // combined regex, then classifies each token individually. This prevents
  // any later pattern from re-matching HTML that was injected by an earlier
  // pattern (which was the source of the class="text-emerald-400"> corruption).
  const highlightTokenizedCode = (rawCode: string, lang: string): string => {
    if (!rawCode) return "";

    const l = lang.toLowerCase();
    if (!["typescript", "javascript", "ts", "js", "python", "py", "json", "java", "html", "css", "sql", "bash", "sh", "cpp", "c++", "c", "h", "hpp"].includes(l)) {
      // For unsupported languages just HTML-escape and return
      return rawCode
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    const KEYWORDS = new Set([
      "const","let","var","function","class","interface","type","extends",
      "implements","new","typeof","instanceof","def","async","await","return",
      "try","catch","finally","throw","if","else","for","while","do","switch",
      "case","break","continue","import","export","from","as","default","true",
      "false","null","undefined","any","string","number","boolean","void",
      "unknown","never","Promise","public","private","protected","static","final",
      "void","int","long","double","float","char","boolean","SELECT","FROM","WHERE",
      "JOIN","ON","INSERT","UPDATE","DELETE","CREATE","TABLE","DROP","ALTER","GROUP",
      "BY","ORDER","HAVING","LIMIT","AND","OR","NOT","NULL","AS","echo","cd","ls",
      "#include","struct","typedef","template","namespace","using","main","printf","std","cout","cin","endl",
    ]);

    // One combined regex — order matters: longer/higher-priority patterns first.
    // Each alternative captures exactly one logical token. We never run a second
    // regex over a segment that already contains injected HTML.
    const TOKEN_RE = new RegExp(
      [
        // 1. Single-line comments  //...  or  #...
        "(\\/\\/[^\\n]*|#[^\\n]*)",
        // 2. Double-quoted strings (no newline)
        '("(?:[^"\\\\]|\\\\.)*")',
        // 3. Single-quoted strings (no newline)
        "('(?:[^'\\\\]|\\\\.)*')",
        // 4. Template literals (backtick)
        "(`(?:[^`\\\\]|\\\\.)*`)",
        // 5. Identifiers / keywords
        "([A-Za-z_]\\w*)",
        // 6. Numbers
        "(\\b\\d+(?:\\.\\d+)?\\b)",
        // 7. Anything else (punctuation, whitespace, operators) — captured as one char
        "([\\s\\S])",
      ].join("|"),
      "g"
    );

    const esc = (s: string) =>
      s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    let result = "";
    let match: RegExpExecArray | null;

    while ((match = TOKEN_RE.exec(rawCode)) !== null) {
      const [, comment, dStr, sStr, tmpl, ident, num, other] = match;

      if (comment !== undefined) {
        result += `<span class="text-text-muted/65 italic">${esc(comment)}</span>`;
      } else if (dStr !== undefined) {
        result += `<span class="text-emerald-400">${esc(dStr)}</span>`;
      } else if (sStr !== undefined) {
        result += `<span class="text-emerald-400">${esc(sStr)}</span>`;
      } else if (tmpl !== undefined) {
        result += `<span class="text-emerald-400">${esc(tmpl)}</span>`;
      } else if (ident !== undefined) {
        const escapedIdent = esc(ident);
        if (KEYWORDS.has(ident)) {
          result += `<span class="text-accent font-semibold">${escapedIdent}</span>`;
        } else {
          // Peek forward: if the very next non-whitespace char in rawCode is '(',
          // it is a function call. We do this by checking the raw source position.
          const afterPos = TOKEN_RE.lastIndex;
          const rest = rawCode.slice(afterPos);
          if (/^\s*\(/.test(rest)) {
            result += `<span class="text-cyan-400 font-medium">${escapedIdent}</span>`;
          } else {
            result += escapedIdent;
          }
        }
      } else if (num !== undefined) {
        result += `<span class="text-amber-400">${esc(num)}</span>`;
      } else if (other !== undefined) {
        result += esc(other);
      }
    }

    return result;
  };

  const lines = cleanCode.split("\n");
  const highlightedCode = highlightTokenizedCode(cleanCode, language);
  const highlightedLines = highlightedCode.split("\n");

  return (
    <div className="my-5 rounded-2xl border border-border-subtle bg-surface-secondary/40 shadow-xl overflow-hidden font-mono text-xs md:text-sm select-text w-full max-w-full">
      {/* CodeBlock Header Bar */}
      <div className="flex items-center justify-between px-4.5 py-3 border-b border-border-subtle/55 bg-surface-secondary/85 select-none">
        <span className="text-[10px] md:text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          {language}
        </span>
        <div className="flex items-center gap-2">
          {/* Line Numbers Toggle */}
          {lines.length > 1 && (
            <button
              onClick={() => setDisplayLineNumbers(!displayLineNumbers)}
              className={cn(
                "p-1.5 rounded-lg hover:bg-surface-primary border border-transparent hover:border-border-subtle text-text-muted transition-all",
                displayLineNumbers && "text-accent bg-surface-primary/60 border-border-subtle"
              )}
              title="Toggle Line Numbers"
            >
              <ListOrdered className="w-3.5 h-3.5" />
            </button>
          )}
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-surface-primary border border-transparent hover:border-border-subtle text-text-muted hover:text-text-primary transition-all text-xs font-medium cursor-pointer"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code Content Area */}
      <div className="overflow-x-auto w-full py-4 bg-surface-primary/10">
        {displayLineNumbers ? (
          <table className="w-full border-collapse">
            <tbody>
              {highlightedLines.map((lineContent, idx) => (
                <tr key={idx} className="hover:bg-surface-secondary/25 transition-colors group">
                  <td className="w-10 select-none text-right pr-4 text-text-muted/30 group-hover:text-text-muted/50 border-r border-border-subtle/30 font-mono text-[10px] leading-6 align-top">
                    {idx + 1}
                  </td>
                  <td className="pl-4 pr-6 leading-6 whitespace-pre font-mono align-top text-text-primary">
                    <span dangerouslySetInnerHTML={{ __html: lineContent || " " }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <pre className="px-6 leading-6 whitespace-pre font-mono text-text-primary">
            <code
              dangerouslySetInnerHTML={{ __html: highlightedCode }}
            />
          </pre>
        )}
      </div>
    </div>
  );
}
