<script>
	import meta from '$lib/data/meta.json';
	import topics from '$lib/data/topics.json';
	import { finder, isActive, reset } from './finder.svelte.js';
</script>

{#if isActive()}
	<div class="filters">
		<select bind:value={finder.firm} class:on={finder.firm} aria-label="firm">
			<option value="">Any firm</option>
			{#each meta.firms as f}<option value={f}>{f}</option>{/each}
		</select>
		<select bind:value={finder.lens} class:on={finder.lens} aria-label="lens">
			<option value="">Any lens</option>
			{#each meta.lenses as l}<option value={l}>{l}</option>{/each}
		</select>
		<select bind:value={finder.band} class:on={finder.band} aria-label="score">
			<option value={0}>Any score</option>
			<option value={meta.min_score_to_publish}>Cleared the bar ({meta.min_score_to_publish}+)</option>
			<option value={meta.min_score_to_publish + 5}>{meta.min_score_to_publish + 5}+</option>
		</select>
		<select bind:value={finder.topic} class:on={finder.topic} aria-label="topic">
			<option value="">Any topic</option>
			{#each topics as t}<option value={t.topic}>{t.topic}</option>{/each}
		</select>
		<button class="plain" onclick={reset}>Clear</button>
	</div>
{/if}
