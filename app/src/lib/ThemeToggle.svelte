<script>
	import { onMount } from 'svelte';

	// Swatch colours are literal on purpose: each one stands for a theme other
	// than the one currently painting the page.
	const THEMES = [
		{ id: 'light', label: 'Light', bg: '#faf8f4', fg: '#17161b' },
		{ id: 'beige', label: 'Beige', bg: '#ece4d3', fg: '#2b2013' },
		{ id: 'dark', label: 'Dark', bg: '#16151a', fg: '#eae7e0' }
	];
	const KEY = 'insights-theme';

	let current = $state('');

	onMount(() => {
		// an unstamped root is following the system; show which one that resolved to
		current =
			document.documentElement.dataset.theme ||
			(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
	});

	function pick(id) {
		document.documentElement.dataset.theme = id;
		current = id;
		try {
			localStorage.setItem(KEY, id);
		} catch {
			// private window or blocked storage: the choice holds for this page only
		}
	}
</script>

<div class="swatches" role="group" aria-label="Colour theme">
	{#each THEMES as t}
		<button
			type="button"
			class="swatch"
			aria-pressed={current === t.id}
			style="--bg:{t.bg};--fg:{t.fg}"
			onclick={() => pick(t.id)}
		>
			<span class="sr">{t.label}</span>
		</button>
	{/each}
</div>
