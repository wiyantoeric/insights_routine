#!/usr/bin/env node
/** Asserts for the markdown the digests contain. Run by `npm run check`. */
import assert from 'node:assert';
import { readFileSync } from 'node:fs';
import { isHttp, md, mdDoc } from '../src/lib/md.js';

// escaping comes before markup, always
assert.equal(md('<script>x</script>'), '&lt;script&gt;x&lt;/script&gt;');
assert.equal(md('a & b'), 'a &amp; b');

// inline
assert.equal(md('see [KPMG](https://kpmg.com/x)'), 'see <a href="https://kpmg.com/x" rel="noreferrer">KPMG</a>');
assert.equal(md('**80%** vs 21%'), '<strong>80%</strong> vs 21%');
assert.equal(md('check `lastmod` first'), 'check <code>lastmod</code> first');
assert.equal(md('[a](javascript:alert(1))'), '[a](javascript:alert(1))', 'only http(s) links become anchors');

// blocks
assert.equal(mdDoc('one\ntwo\n\nthree'), '<p>one two</p><p>three</p>', 'wrapped lines join, blank line splits');
assert.equal(mdDoc('- a\n- b'), '<ul><li>a</li><li>b</li></ul>');
assert.equal(mdDoc('- a\n  still a\n- b'), '<ul><li>a still a</li><li>b</li></ul>', 'indented continuation');
assert.equal(mdDoc('## Notes'), '<h4>Notes</h4>');

const table = mdDoc('| Candidate | `lastmod` |\n|---|---|\n| issue-33 | 2026-09-07 |');
assert.equal(
	table,
	'<table><thead><tr><th>Candidate</th><th><code>lastmod</code></th></tr></thead>' +
		'<tbody><tr><td>issue-33</td><td>2026-09-07</td></tr></tbody></table>'
);
assert.equal(mdDoc('| not | a table |'), '<p>| not | a table |</p>', 'a table needs its divider row');

// the real thing: the 2026-09-08 run notes carry every construct at once
const notes = JSON.parse(readFileSync(new URL('../../digests/2026-09-08.json', import.meta.url))).run_notes;
const html = mdDoc(notes);
for (const tag of ['<p>', '<ul>', '<table>', '<strong>', '<code>']) {
	assert.ok(html.includes(tag), `expected ${tag} in the rendered run notes`);
}
assert.ok(!html.includes('|---|'), 'divider row must not survive as text');
assert.ok(!/\*\*/.test(html), 'no bold markers left unrendered');

console.error('md check ok');

// footnotes: a marker points at that item's own numbered source
assert.equal(md('the 21% gap[^2] holds'), 'the 21% gap<sup class="fn">2</sup> holds');
assert.equal(
	md('the 21% gap[^2] holds', 'item-4'),
	'the 21% gap<sup class="fn"><a href="#item-4-s2">2</a></sup> holds'
);
assert.ok(mdDoc('- claim[^1]', 'item-1').includes('#item-1-s1'), 'markers work inside blocks');
assert.equal(md('array[^foo] is not a marker'), 'array[^foo] is not a marker');

// the repo's own prose rule, asserted on what the site will render
const dashed = JSON.parse(readFileSync(new URL('../../digests/2026-09-08.json', import.meta.url)));
assert.ok(typeof dashed.tape.line === 'object', 'tape.line is one entry per asset');
assert.ok('line_remark' in dashed.tape, 'tape carries line_remark');

// only an absolute http(s) url may become a link. A repo path rendered as an
// anchor made the prerenderer crawl it, 404, and fail the build (2026-09-12).
assert.ok(isHttp('https://kpmg.com/x') && isHttp('http://x.test'));
for (const notUrl of [
	'state/candidates.json → tape',
	'sources/quotes.json',
	'digests/2026-09-12-am.md and digests/2026-09-08.md through digests/2026-09-11.md',
	'',
	null
]) {
	assert.ok(!isHttp(notUrl), `must not link: ${notUrl}`);
}
