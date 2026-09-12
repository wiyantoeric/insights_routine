<script>
	import Digest from '$lib/Digest.svelte';
	import Icon from '$lib/Icon.svelte';
	let { data } = $props();
</script>

<svelte:head><title>Insights {data.digest.date}</title></svelte:head>

<Digest digest={data.digest} heading="Insights {data.digest.date}" />

<nav class="pager">
	{#if data.older}
		<a href="/d/{data.older}"><Icon name="left" /> {data.older}</a>
	{:else}
		<span></span>
	{/if}
	{#if data.newer}
		<a href="/d/{data.newer}">{data.newer} <Icon name="right" /></a>
	{/if}
</nav>
