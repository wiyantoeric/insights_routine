<script>
	import Entry from '$lib/Entry.svelte';
	import Score from '$lib/Score.svelte';
	import { md } from '$lib/md.js';
	let { data } = $props();
</script>

<svelte:head><title>{data.topic.topic}</title></svelte:head>

<h1>{data.topic.topic}</h1>
<p class="lede">
	{#if data.topic.count === 1}
		Declared once, {data.topic.first_seen}.
	{:else}
		{data.topic.count} digests, {data.topic.first_seen} to {data.topic.last_seen}.
	{/if}
</p>

{#each data.digests as d}
	<h2 style="margin:2.5rem 0 0.4rem"><a href="/d/{d.date}">{d.date}</a></h2>
	{#each d.items as item}
		<Entry {item} />
	{/each}
	{#each d.watchlist as w, i}
		<article class="entry">
			<div class="apparatus">
				<span class="ordinal">{String(i + 1).padStart(2, '0')}</span>
				<Score score={w.score} />
				<span class="tag">watchlist</span>
			</div>
			<div>
				<h3>{w.title}</h3>
				<div class="field">{@html md(w.body)}</div>
			</div>
		</article>
	{/each}
{/each}
