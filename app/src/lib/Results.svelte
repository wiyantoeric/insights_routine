<script>
	import meta from '$lib/data/meta.json';
	import topics from '$lib/data/topics.json';
	import Score from './Score.svelte';
	import { finder, reset } from './finder.svelte.js';

	const terms = $derived(finder.q.toLowerCase().split(/\s+/).filter(Boolean));
	const topicDates = $derived(
		finder.topic ? new Set(topics.find((t) => t.topic === finder.topic)?.dates ?? []) : null
	);

	const hits = $derived(
		(finder.rows ?? []).filter((r) => {
			if (finder.firm && !r.firms.includes(finder.firm)) return false;
			if (finder.lens && r.lens !== finder.lens) return false;
			if (finder.band && (r.score ?? 0) < finder.band) return false;
			if (topicDates && !topicDates.has(r.date)) return false;
			const hay = `${r.title ?? ''} ${r.text}`.toLowerCase();
			return terms.every((t) => hay.includes(t));
		})
	);

	// the sentence around the first match, split so the term can be marked
	// without putting untrusted text through {@html}
	function excerpt(r) {
		const t = terms[0];
		const at = t ? r.text.toLowerCase().indexOf(t) : -1;
		let from = at > 70 ? at - 70 : 0;
		if (from) from = r.text.indexOf(' ', from) + 1 || from;
		const body = r.text.slice(from, from + 230);
		const text = (from ? '…' : '') + body + (r.text.length > from + 230 ? '…' : '');
		if (!t) return [{ text, hit: false }];
		const out = [];
		let i = 0;
		const low = text.toLowerCase();
		for (let at2 = low.indexOf(t); at2 !== -1; at2 = low.indexOf(t, i)) {
			if (at2 > i) out.push({ text: text.slice(i, at2), hit: false });
			out.push({ text: text.slice(at2, at2 + t.length), hit: true });
			i = at2 + t.length;
		}
		out.push({ text: text.slice(i), hit: false });
		return out;
	}
</script>

<p class="label" style="margin-bottom:1rem">
	{hits.length} of {finder.rows?.length ?? 0} entries
</p>

{#each hits as r, i (r.date + r.kind + r.ord)}
	<article class="result" style="--i:{Math.min(i, 10)}">
		<h3>
			<a href="/d/{r.date}{r.kind === 'item' ? `#item-${r.ord}` : ''}">{r.title}</a>
		</h3>
		<div class="meta">
			<Score score={r.score} meter={false} />
			<span class="tag">{r.date}</span>
			{#if r.lens}<span class="tag">{r.lens}</span>{/if}
			{#each r.firms as f}<span class="tag">{f}</span>{/each}
			{#if r.kind === 'watchlist'}<span class="tag">watchlist</span>{/if}
		</div>
		{#if r.action}<p><strong>Do this week.</strong> {r.action}</p>{/if}
		<p>{#each excerpt(r) as part}{#if part.hit}<mark>{part.text}</mark>{:else}{part.text}{/if}{/each}</p>
	</article>
{:else}
	<p class="empty">
		Nothing matches. <button class="plain" onclick={reset}>Clear the finder</button> to go back to
		the page.
	</p>
{/each}
