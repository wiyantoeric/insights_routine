<script>
	import Entry from './Entry.svelte';
	import Score from './Score.svelte';
	import Icon from './Icon.svelte';
	import Tape from './Tape.svelte';
	import { md, mdDoc } from './md.js';

	let { digest: d, heading } = $props();
</script>

<h1>{heading}</h1>

{#if !d.parse_ok}
	<p class="lede broken">Could not read this digest. {d.reason}</p>
{:else}
	<Tape tape={d.tape} />
	{#if d.tape?.alerts?.length}
		<p><span class="tag flag"><Icon name="alert" size={12} /> {d.tape.alerts.length} alert</span></p>
	{/if}
	{#if d.tape?.as_of_note}
		<p class="label" style="margin:0 0 1.6rem">{d.tape.as_of_note}</p>
	{/if}

	{#if d.tape_note}
		<div class="read">{@html md(d.tape_note)}</div>
	{/if}

	{#if d.items.length}
		{#each d.items as item}
			<Entry {item} />
		{/each}
	{:else}
		<p class="lede">
			Nothing cleared the bar{#if d.top_score}. Highest candidate reached {d.top_score} of 60{/if}.
		</p>
	{/if}

	{#if d.watchlist.length}
		<h2 style="margin:3rem 0 0.6rem">Watchlist</h2>
		{#each d.watchlist as w, i}
			<article class="entry">
				<div class="apparatus">
					<span class="ordinal">{String(i + 1).padStart(2, '0')}</span>
					<Score score={w.score} />
				</div>
				<div>
					<h3>{w.title}</h3>
					<div class="field">{@html mdDoc(w.body)}</div>
				</div>
			</article>
		{/each}
	{/if}

	{#if d.run_notes}
		<details class="notes" id="run-notes">
			<summary>Run notes</summary>
			<div class="notes-body">{@html mdDoc(d.run_notes)}</div>
		</details>
	{/if}
{/if}
