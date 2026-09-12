<script>
	import index from '$lib/data/index.json';
	import digests from '$lib/data/digests.json';
	import Score from '$lib/Score.svelte';
	import Tape from '$lib/Tape.svelte';

	const byDate = Object.fromEntries(digests.map((d) => [d.date, d]));
</script>

<svelte:head><title>Archive</title></svelte:head>

<h1>Archive</h1>
<p class="lede">
	{index.length} digest{index.length === 1 ? '' : 's'}. Press <kbd>/</kbd> to search inside them.
</p>

{#each index as d}
	<div class="index-row">
		<div class="apparatus" style="display:flex;flex-direction:column;gap:0.4rem;align-items:flex-start">
			<a class="date" href="/d/{d.date}">{d.date}</a>
			<Score score={d.top_score} />
			{#if d.backfilled}<span class="tag">backfilled</span>{/if}
		</div>
		<div>
			{#if !d.parse_ok}
				<p class="broken" style="margin:0">Could not read this digest. {d.reason}</p>
			{:else if d.item_count}
				<ol>
					{#each byDate[d.date].items as it}
						<li><a href="/d/{d.date}#item-{it.ord}">{it.title}</a> · {it.score} · {it.lens}</li>
					{/each}
				</ol>
			{:else}
				<p style="margin:0" class="muted">
					Nothing cleared the bar. {byDate[d.date].watchlist.length} on the watchlist.
				</p>
			{/if}
			<Tape tape={d.tape} />
		</div>
	</div>
{:else}
	<p class="empty">No digests yet.</p>
{/each}
