<script>
	// self-hosted, weight axis only. No request leaves the page.
	import '@fontsource-variable/noto-sans/wght.css';
	import '@fontsource-variable/urbanist/wght.css';
	import '../app.css';

	import { page } from '$app/state';
	import index from '$lib/data/index.json';
	import Finder from '$lib/Finder.svelte';
	import Filters from '$lib/Filters.svelte';
	import ThemeToggle from '$lib/ThemeToggle.svelte';
	import Results from '$lib/Results.svelte';
	import { isActive } from '$lib/finder.svelte.js';

	let { children } = $props();

	const newest = index[0]?.date ?? null;
	const links = [
		['/', 'Today'],
		['/archive', 'Archive'],
		['/topics', 'Topic'],
		['/tape', 'Tape']
	];
</script>

<header class="masthead">
	<div>
		<a class="wordmark" href="/">Insights{#if newest}<span>{newest}</span>{/if}</a>
		<Finder />
		<nav>
			{#each links as [href, label]}
				<a {href} aria-current={page.url.pathname === href ? 'page' : undefined}>{label}</a>
			{/each}
		</nav>
		<ThemeToggle />
	</div>
	{#if isActive()}
		<div class="filterbar"><Filters /></div>
	{/if}
</header>

<main>
	{#if isActive()}
		<Results />
	{:else}
		{@render children()}
	{/if}
</main>
