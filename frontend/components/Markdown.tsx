"use client";

import React from "react";

// Minimal, safe markdown renderer (bold, italic, code, lists, links, breaks).
// Renders to React elements — no dangerouslySetInnerHTML.

function inline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  // Order matters: code first, then bold, then italic, then links.
  const pattern = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = pattern.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    const token = m[0];
    const key = `${keyPrefix}-${i++}`;
    if (token.startsWith("`")) {
      nodes.push(<code key={key}>{token.slice(1, -1)}</code>);
    } else if (token.startsWith("**")) {
      nodes.push(<strong key={key}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("*")) {
      nodes.push(<em key={key}>{token.slice(1, -1)}</em>);
    } else {
      const lm = /\[([^\]]+)\]\(([^)]+)\)/.exec(token);
      if (lm) {
        nodes.push(
          <a key={key} href={lm[2]} target="_blank" rel="noreferrer" className="text-brand-600 underline dark:text-brand-300">
            {lm[1]}
          </a>
        );
      }
    }
    last = m.index + token.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

export default function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let list: string[] | null = null;
  let key = 0;

  const flushList = () => {
    if (list && list.length) {
      blocks.push(
        <ul key={`ul-${key++}`}>
          {list.map((item, i) => (
            <li key={i}>{inline(item, `li-${key}-${i}`)}</li>
          ))}
        </ul>
      );
    }
    list = null;
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    if (bullet) {
      if (!list) list = [];
      list.push(bullet[1]);
      continue;
    }
    flushList();
    if (!line.trim()) continue;
    if (/^#{1,6}\s/.test(line)) {
      const level = line.match(/^#/)![0].length;
      const Tag = (`h${Math.min(level, 3)}`) as "h1" | "h2" | "h3";
      blocks.push(<Tag key={`h-${key++}`}>{inline(line.replace(/^#+\s*/, ""), `h-${key}`)}</Tag>);
    } else {
      blocks.push(<p key={`p-${key++}`}>{inline(line, `p-${key}`)}</p>);
    }
  }
  flushList();

  return <div className="md text-[15px] leading-relaxed">{blocks}</div>;
}
