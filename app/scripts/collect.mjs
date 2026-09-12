#!/usr/bin/env node
/**
 * Build-time data layer. Reads the digest sidecars, emits what the site imports.
 *
 * Never throws on a bad digest. It lands in the output with parse_ok:false and a
 * reason, so the page shows a broken card. A site that refuses to build because
 * one digest is malformed tells you nothing and hides the other 364.
 *
 *   node scripts/collect.mjs           emit src/lib/data/*.json
 *   node scripts/collect.mjs --check   assert the contract, exit 1 on a breach
 */
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert';

const APP = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ROOT = resolve(APP, '..');
const OUT = join(APP, 'src/lib/data');

// the digest path lives in config.json, not here
const cfg = JSON.parse(readFileSync(join(ROOT, 'config.json'), 'utf8'));
const DIGESTS = resolve(ROOT, cfg.paths.digest_dir);

// "what has KPMG said about agentic AI" is one of the two jobs, so the firm has
// to be a filter, not something to read off a url by eye.
const NAMED = { 'kpmg.com': 'KPMG', 'deloitte.com': 'Deloitte', 'pwc.com': 'PwC' };
function firmOf(url) {
	try {
		const host = new URL(url).hostname.replace(/^www\d?\./, '');
		const key = Object.keys(NAMED).find((d) => host === d || host.endsWith(`.${d}`));
		return key ? NAMED[key] : host;
	} catch {
		return null;
	}
}
// the index is read as prose in results, so links and emphasis flatten to their
// text. The rendered digest still gets the markup through md().
const plain = (v) =>
	String(v ?? '')
		.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '$1')
		.replace(/\*\*([^*]+)\*\*/g, '$1')
		.replace(/`([^`]+)`/g, '$1');

const firmsOf = (sources) => [...new Set((sources ?? []).map((s) => firmOf(s.url)).filter(Boolean))];

const REQUIRED = ['date', 'tape', 'items', 'watchlist'];

// tape.line is an object of asset -> reading. A digest written before that shape
// carries a sentence instead; keep it as the remark rather than dropping it.
function tapeOf(tape = {}) {
	const legacy = typeof tape.line === 'string' ? tape.line : null;
	return {
		as_of: tape.as_of ?? null,
		as_of_note: tape.as_of_note ?? null,
		line: legacy ? {} : (tape.line ?? {}),
		line_remark: [legacy, tape.line_remark].filter(Boolean).join(' · ') || null,
		alerts: tape.alerts ?? [],
		readings: tape.readings ?? null
	};
}
const broken = (date, reason) => ({
	date, parse_ok: false, reason, top_score: null,
	topics: [], items: [], watchlist: [], run_notes: null,
	tape: { as_of: null, as_of_note: null, line: {}, line_remark: null, alerts: [], readings: null }
});

// A watchlist body that opens with its own title renders it twice: the card
// already shows title and score. Strip the repeat, bold or plain.
function stripHead(w) {
	let body = String(w.body ?? '');
	const title = String(w.title ?? '');
	const bold = body.match(/^\*\*(.+?)\*\*\s*/s);
	if (title && bold && bold[1].startsWith(title)) body = body.slice(bold[0].length);
	else if (title && body.startsWith(title)) body = body.slice(title.length).replace(/^[\s.·—-]+/, '');
	return { ...w, body };
}

function load(file) {
	const date = file.slice(0, -5);
	try {
		const d = JSON.parse(readFileSync(join(DIGESTS, file), 'utf8'));
		const missing = REQUIRED.filter((k) => d[k] === undefined);
		if (missing.length) return broken(date, `missing ${missing.join(', ')}`);
		return {
			...d,
			parse_ok: true,
			reason: null,
			backfilled: Boolean(d._backfilled),
			topics: d.topics ?? [],
			tape: tapeOf(d.tape),
			items: d.items ?? [],
			watchlist: (d.watchlist ?? []).map(stripHead)
		};
	} catch (e) {
		return broken(date, e.message);
	}
}

const files = existsSync(DIGESTS)
	? readdirSync(DIGESTS).filter((f) => f.endsWith('.json')).sort().reverse()
	: [];
const digests = files.map(load);

const index = digests.map((d) => ({
	date: d.date,
	parse_ok: d.parse_ok,
	reason: d.reason ?? null,
	backfilled: d.backfilled ?? false,
	top_score: d.top_score ?? null,
	item_count: d.items.length,
	lenses: [...new Set(d.items.map((i) => i.lens).filter(Boolean))],
	firms: [...new Set(d.items.flatMap((i) => firmsOf(i.sources)))].sort(),
	topics: d.topics,
	tape: d.tape ?? { line: {}, line_remark: null },
	has_run_notes: Boolean(d.run_notes)
}));

// search payload. Items and watchlist entries both, they are both worth finding.
const rows = [];
for (const d of digests) {
	for (const i of d.items)
		rows.push({
			date: d.date, kind: 'item', ord: i.ord ?? null, title: i.title ?? null,
			score: i.score ?? null, lens: i.lens ?? null,
			url: i.sources?.[0]?.url ?? null,
			firms: firmsOf(i.sources),
			action: plain(i.action) || null,
			text: plain([i.signal, i.why, i.angle, i.action].filter(Boolean).join(' '))
		});
	for (const [n, w] of d.watchlist.entries())
		rows.push({
			date: d.date, kind: 'watchlist', ord: n + 1, title: w.title ?? null,
			score: w.score ?? null, lens: null,
			url: w.sources?.[0]?.url ?? null, firms: firmsOf(w.sources),
			action: null, text: plain(w.body)
		});
}

// topics by occurrence. A digest whose topics the agent never wrote contributes
// nothing here — absent, not guessed.
const seen = {};
for (const d of digests) for (const t of d.topics) (seen[t] ??= []).push(d.date);
const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const topics = Object.entries(seen)
	.map(([topic, dates]) => {
		const sorted = dates.sort();
		return {
			topic, slug: slugify(topic), dates: sorted, count: sorted.length,
			first_seen: sorted[0], last_seen: sorted.at(-1)
		};
	})
	.sort((a, b) => b.count - a.count || a.topic.localeCompare(b.topic));

const tape = digests.map((d) => ({ date: d.date, ...d.tape }));

// the scoring bar and the lens vocabulary belong to config.json, not to the UI
const meta = {
	min_score_to_publish: cfg.scoring.min_score_to_publish,
	max_score: cfg.scoring.max_score,
	lenses: cfg.focus.lenses,
	firms: [...new Set(rows.flatMap((r) => r.firms))].sort(),
	generated_at: new Date().toISOString()
};

mkdirSync(OUT, { recursive: true });
for (const [name, data] of Object.entries({ digests, index, rows, topics, tape, meta }))
	writeFileSync(join(OUT, `${name}.json`), JSON.stringify(data));

const unlinkable = digests.flatMap((d) =>
	[...d.items, ...d.watchlist].flatMap((r) =>
		(r.sources ?? []).map((s) => s.url).filter((u) => u && !/^https?:\/\//i.test(u))
	)
);
const bad = index.filter((d) => !d.parse_ok);
const noTopics = index.filter((d) => d.parse_ok && d.topics.length === 0).map((d) => d.date);
console.error(
	`collect: ${digests.length} digests from ${DIGESTS}, ${rows.length} searchable rows, ${topics.length} topics` +
		(bad.length ? `, ${bad.length} BROKEN: ${bad.map((d) => `${d.date} (${d.reason})`).join('; ')}` : '') +
		(noTopics.length ? `, no topics declared: ${noTopics.join(', ')}` : '') +
		(unlinkable.length ? `, ${unlinkable.length} source(s) are not urls: ${unlinkable[0].slice(0, 60)}…` : '')
);

if (process.argv.includes('--check')) {
	assert(digests.length > 0, `no digests found in ${DIGESTS} — is the routine writing json there?`);
	assert(bad.length === 0, `broken digests: ${bad.map((d) => d.date).join(', ')}`);
	assert(rows.length >= digests.length, 'every digest should contribute at least one row');
	assert(
		digests.flatMap((d) => d.items).some((i) => (i.sources?.length ?? 0) > 1),
		'expected a multi-source item — sources must stay a list, not collapse to one url'
	);
	assert(
		index.every((d) => d.item_count === 0 || typeof d.top_score === 'number'),
		'a digest with items must carry top_score'
	);
	console.error('check ok');
}
