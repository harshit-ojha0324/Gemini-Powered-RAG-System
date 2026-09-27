// A rehype plugin for answers rendered with react-markdown.
//   - Page citations such as "(page 3)", "(pp. 3–4)", "(see page 3)" or
//     "(Source: report.pdf, page 3)" become <cite data-page="3"> chips that
//     link to the retrieved passage from that page.
//   - Tokens such as "[REDACTED]" or "[API_KEY_REDACTED]" (from the backend's
//     output filter) become <redaction> bars.
// Citations are only rewritten when at least one of their pages is among the
// answer's sources, so the chips never point at nothing.

const SEPARATOR = String.raw`\s*(?:[-–—]|,(?:\s*and)?|and|&)\s*`;
const PAGE_LIST = String.raw`\d+(?:${SEPARATOR}\d+)*`;
const CITATION = String.raw`[([](?:[^()[\]\n]{0,80}?(?:[,;:]\s*|\s))?(?:pages?|pp?\.)\s*:?\s*(${PAGE_LIST})(?:\s+(?:of|in)\s+[^()[\]\n]{1,80}?)?[)\]]`;
const REDACTION = String.raw`\[(?:[A-Z]+_)*REDACTED\]`;
const EVIDENCE = new RegExp(`${CITATION}|(${REDACTION})`, 'gi');

const SKIP_INSIDE = new Set(['a', 'code', 'pre']);

export function parsePages(spec) {
  const pages = [];
  for (const part of spec.split(/\s*(?:,(?:\s*and)?|and|&)\s*/i)) {
    const range = /^(\d+)\s*[-–—]\s*(\d+)$/.exec(part);
    if (range) {
      const start = Number(range[1]);
      const end = Number(range[2]);
      if (end > start && end - start <= 10) {
        for (let page = start; page <= end; page += 1) pages.push(page);
      } else {
        pages.push(start, end);
      }
    } else if (/^\d+$/.test(part)) {
      pages.push(Number(part));
    }
  }
  return [...new Set(pages)].map(String);
}

function citeNode(page, linked) {
  return {
    type: 'element',
    tagName: 'cite',
    properties: { dataPage: page, dataLinked: linked ? 'true' : 'false' },
    children: [{ type: 'text', value: `p. ${page}` }],
  };
}

function redactionNode() {
  return { type: 'element', tagName: 'redaction', properties: {}, children: [] };
}

/** Returns replacement nodes for a text value, or null when nothing matched. */
function splitText(value, linkedPages) {
  const nodes = [];
  let last = 0;
  for (const match of value.matchAll(EVIDENCE)) {
    let replacement;
    if (match[2]) {
      replacement = [redactionNode()];
    } else {
      const pages = parsePages(match[1]);
      if (!pages.some((page) => linkedPages.has(page))) continue;
      replacement = pages.map((page) => citeNode(page, linkedPages.has(page)));
    }
    let before = value.slice(last, match.index);
    // A no-break space keeps a citation chip on the same line as the word it cites.
    if (!match[2]) before = before.replace(/ $/, '\u00a0');
    if (before) nodes.push({ type: 'text', value: before });
    nodes.push(...replacement);
    last = match.index + match[0].length;
  }
  if (!nodes.length) return null;
  if (last < value.length) nodes.push({ type: 'text', value: value.slice(last) });
  return nodes;
}

function transform(node, linkedPages) {
  if (!Array.isArray(node.children)) return;
  const children = [];
  for (const child of node.children) {
    if (child.type === 'text') {
      const replaced = splitText(child.value, linkedPages);
      if (replaced) children.push(...replaced);
      else children.push(child);
      continue;
    }
    if (!(child.type === 'element' && SKIP_INSIDE.has(child.tagName))) transform(child, linkedPages);
    children.push(child);
  }
  node.children = children;
}

export default function rehypeEvidence({ pages = [] } = {}) {
  const linkedPages = new Set(pages.map(String));
  return (tree) => transform(tree, linkedPages);
}
