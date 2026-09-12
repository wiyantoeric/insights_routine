<script>
	import Score from './Score.svelte';
	import { md, mdDoc, isHttp } from './md.js';

	let { item, date = null, href = null } = $props();
	const ref = $derived(`item-${item.ord}`);
	const fields = [
		['Signal', 'signal'],
		['Why it matters', 'why'],
		['Angle', 'angle']
	];
</script>

<article class="entry" id="item-{item.ord}">
	<div class="apparatus">
		<span class="ordinal">{String(item.ord).padStart(2, '0')}</span>
		<Score score={item.score} />
		{#if item.lens}<span class="tag">{item.lens}</span>{/if}
		{#if item.follow_up}<span class="tag flag">follow-up</span>{/if}
		{#if date}<a class="tag" href="/d/{date}">{date}</a>{/if}
	</div>

	<div>
		<h3>
			{#if href}<a {href}>{item.title}</a>{:else}{item.title}{/if}
		</h3>

		{#each fields as [label, key]}
			{#if item[key]}
				<div class="field">
					<span class="label">{label}</span>{@html mdDoc(item[key], ref)}
				</div>
			{/if}
		{/each}
		{#if item.action}
			<div class="field do">
				<span class="label">Do this week</span>{@html mdDoc(item.action, ref)}
			</div>
		{/if}

		{#if item.sources?.length}
			<ol class="sources">
				{#each item.sources as s, n}
					<li id="{ref}-s{n + 1}">
						{#if isHttp(s.url)}
							<a href={s.url} rel="noreferrer">{s.url}</a>
						{:else}
							<span class="not-a-url">{s.url}</span>
						{/if}{#if s.published} · {s.published}{/if}
					</li>
				{/each}
			</ol>
		{/if}
	</div>
</article>
