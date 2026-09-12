<script>
	import meta from '$lib/data/meta.json';

	let { score = null, meter = true } = $props();
	const cleared = $derived(score != null && score >= meta.min_score_to_publish);
</script>

{#if score != null}
	<span class="score {cleared ? 'cleared' : 'below'}">
		{score}<small>/{meta.max_score}</small>
	</span>
	{#if meter}
		<span
			class="meter {cleared ? 'cleared' : 'below'}"
			title="{score} of {meta.max_score}, bar {meta.min_score_to_publish}"
		>
			<i style="width:{Math.round((score / meta.max_score) * 100)}%"></i>
		</span>
	{/if}
{/if}
