<script>
	import tape from '$lib/data/tape.json';
	import Icon from '$lib/Icon.svelte';
	import Tape from '$lib/Tape.svelte';

	const withReadings = tape.filter((t) => t.readings);
</script>

<svelte:head><title>Tape</title></svelte:head>

<h1>Tape</h1>
<p class="lede">
	What the market did on each digest day. Lens C asks whether the tape confirms, contradicts or
	ignores what the firms published that day.
</p>

{#if !withReadings.length}
	<p class="label" style="margin-bottom:1.5rem">
		These digests carry the tape as a written line, not as numbers. Charts appear once a digest
		carries tape.readings.
	</p>
{/if}

{#each tape as t}
	<div class="index-row">
		<div style="display:flex;flex-direction:column;gap:0.4rem;align-items:flex-start">
			<a class="date" href="/d/{t.date}">{t.date}</a>
			{#if t.alerts?.length}
				<span class="tag flag"><Icon name="alert" size={12} /> {t.alerts.length}</span>
			{/if}
		</div>
		<div>
			<Tape tape={t} />
			{#if t.as_of_note}<p class="label" style="margin-top:0.5rem">{t.as_of_note}</p>{/if}
		</div>
	</div>
{:else}
	<p class="empty">No tape recorded.</p>
{/each}
