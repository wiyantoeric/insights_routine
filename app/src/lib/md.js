/**
 * The markdown the digests actually contain, and nothing else.
 *
 * Item fields carry inline markup only: links, bold, inline code. Run notes
 * carry blocks too: paragraphs, bullet lists, and a table when the agent is
 * showing its working.
 *
 * Everything is escaped before any markup is added. The text is agent-written,
 * but {@html} on unescaped input is wrong regardless of who wrote it.
 *
 * ponytail: hand-rolled over the documented digest shape. Swap in a real parser
 * if WORKFLOWS.md ever widens what a digest may contain.
 */
const escape = (s) =>
	String(s ?? '')
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;');

/**
 * Inline only. What an item field is allowed to hold.
 *
 * `[^2]` is a footnote marker: it points at the second entry in the item's own
 * `sources` list, so prose can carry a reference without swallowing a url.
 * Pass `refBase` (the item's dom id) to make the markers links.
 */
export function md(text, refBase) {
	return escape(text)
		.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" rel="noreferrer">$1</a>')
		.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
		.replace(/`([^`]+)`/g, '<code>$1</code>')
		.replace(/\[\^(\d{1,2})\]/g, (_, n) =>
			refBase
				? `<sup class="fn"><a href="#${refBase}-s${n}">${n}</a></sup>`
				: `<sup class="fn">${n}</sup>`
		);
}

/**
 * Only an absolute http(s) url may become a link. The agent sometimes puts a
 * repo path or a sentence where a url belongs; rendering that as an anchor made
 * the prerenderer crawl it, 404, and fail the whole build.
 */
export const isHttp = (u) => /^https?:\/\//i.test(String(u ?? ''));

const cells = (row) =>
	row
		.trim()
		.replace(/^\|/, '')
		.replace(/\|$/, '')
		.split('|')
		.map((c) => c.trim());

const isRow = (line = '') => line.trim().startsWith('|');
const isDivider = (line = '') => isRow(line) && /^\|[\s:|-]*-[\s:|-]*\|?$/.test(line.trim());
const isBullet = (line = '') => /^\s*[-*]\s+/.test(line);
const isHeading = (line = '') => /^#{1,6}\s+/.test(line);

/** Blocks as well: headings, tables, bullet lists, paragraphs. */
export function mdDoc(text, refBase) {
	const lines = String(text ?? '')
		.replace(/\r\n?/g, '\n')
		.split('\n');
	const out = [];
	let i = 0;

	while (i < lines.length) {
		const line = lines[i];

		if (!line.trim()) {
			i++;
			continue;
		}

		if (isRow(line) && isDivider(lines[i + 1])) {
			const head = cells(line);
			i += 2;
			const body = [];
			while (i < lines.length && isRow(lines[i])) body.push(cells(lines[i++]));
			out.push(
				'<table><thead><tr>' +
					head.map((c) => `<th>${md(c, refBase)}</th>`).join('') +
					'</tr></thead><tbody>' +
					body
						.map((r) => '<tr>' + r.map((c) => `<td>${md(c, refBase)}</td>`).join('') + '</tr>')
						.join('') +
					'</tbody></table>'
			);
			continue;
		}

		if (isHeading(line)) {
			out.push(`<h4>${md(line.replace(/^#{1,6}\s+/, ''), refBase)}</h4>`);
			i++;
			continue;
		}

		if (isBullet(line)) {
			const items = [];
			while (i < lines.length && isBullet(lines[i])) {
				let item = lines[i++].replace(/^\s*[-*]\s+/, '');
				// a wrapped bullet continues on an indented line
				while (i < lines.length && /^\s{2,}\S/.test(lines[i]) && !isBullet(lines[i]))
					item += ' ' + lines[i++].trim();
				items.push(`<li>${md(item, refBase)}</li>`);
			}
			out.push(`<ul>${items.join('')}</ul>`);
			continue;
		}

		// the first line always goes in, so a stray `|` row cannot stall the cursor
		const para = [lines[i++].trim()];
		while (
			i < lines.length &&
			lines[i].trim() &&
			!isRow(lines[i]) &&
			!isBullet(lines[i]) &&
			!isHeading(lines[i])
		)
			para.push(lines[i++].trim());
		out.push(`<p>${md(para.join(' '), refBase)}</p>`);
	}

	return out.join('');
}
