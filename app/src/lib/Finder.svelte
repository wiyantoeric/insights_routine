<script>
	import { onMount } from 'svelte';
	import Icon from './Icon.svelte';
	import { finder, isActive, reset, ensureRows } from './finder.svelte.js';

	let input = $state(null);

	onMount(() => {
		const onKey = (e) => {
			if (e.key === 'Escape' && isActive()) {
				reset();
				input?.blur();
				return;
			}
			const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName ?? '');
			if ((e.key === '/' && !typing) || (e.key === 'k' && (e.metaKey || e.ctrlKey))) {
				e.preventDefault();
				ensureRows();
				input?.focus();
			}
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="finder-field">
	<Icon name="search" />
	<input
		bind:this={input}
		bind:value={finder.q}
		onfocus={ensureRows}
		oninput={ensureRows}
		type="search"
		placeholder="Find a claim, number, firm or topic"
		aria-label="Find across every digest"
	/>
	<kbd>/</kbd>
</div>
