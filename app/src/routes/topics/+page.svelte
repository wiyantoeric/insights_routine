<script>
	import topics from '$lib/data/topics.json';
	import index from '$lib/data/index.json';

	const dates = index.map((d) => d.date).sort();
	const undeclared = index.filter((d) => d.parse_ok && d.topics.length === 0);
</script>

<svelte:head><title>Topics</title></svelte:head>

<h1>Topics</h1>
<p class="lede">What the digests keep coming back to. Lens D counts volume shifts and vocabulary migration.</p>

{#each topics as t}
	<div class="index-row">
		<div style="display:flex;flex-direction:column;gap:0.5rem;align-items:flex-start">
			<span class="occurrence" title="{t.count} of {dates.length} digests">
				{#each dates as d}<i class={t.dates.includes(d) ? 'on' : ''}></i>{/each}
			</span>
			<span class="label">
				{#if t.count === 1}Once{:else}{t.count} digests{/if}
			</span>
		</div>
		<div>
			<h3><a href="/topics/{t.slug}">{t.topic}</a></h3>
			<p class="muted" style="margin:0.2rem 0 0">
				{#if t.count === 1}
					{t.first_seen}
				{:else}
					{t.first_seen} to {t.last_seen}
				{/if}
			</p>
		</div>
	</div>
{:else}
	<p class="empty">No topics declared yet.</p>
{/each}

{#if undeclared.length}
	<p class="label" style="margin-top:1.5rem">
		{undeclared.map((d) => d.date).join(', ')} declared no topics, so {undeclared.length === 1
			? 'it counts'
			: 'they count'} toward nothing here.
	</p>
{/if}
