<script>
	import Digest from '$lib/Digest.svelte';
	import Icon from '$lib/Icon.svelte';
	let { data } = $props();
</script>

<svelte:head><title>Insights</title></svelte:head>

{#if data.digest}
	<Digest digest={data.digest} heading="Insights {data.digest.date}" />
	{#if data.older}
		<nav class="pager"><a href="/d/{data.older}"><Icon name="left" /> {data.older}</a></nav>
	{/if}
{:else}
	<h1>Insights</h1>
	<p class="lede">No digest yet. The routine writes one each morning.</p>
{/if}
