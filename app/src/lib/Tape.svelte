<script>
	// One pair per asset, so the tape reads as a column of readings rather than a
	// sentence of numbers. The delta keeps its sign from the digest; nothing here
	// recomputes it.
	let { tape } = $props();

	const assets = $derived(Object.entries(tape?.line ?? {}));
	const split = (v) => {
		const m = String(v).match(/^(.*?)\s*\(([+-][^)]*)\)\s*$/);
		return m ? { value: m[1], delta: m[2] } : { value: String(v), delta: null };
	};
</script>

{#if assets.length}
	<dl class="ribbon">
		{#each assets as [label, reading]}
			{@const r = split(reading)}
			<div>
				<dt>{label}</dt>
				<dd>
					{r.value}{#if r.delta}<span class={r.delta.startsWith('-') ? 'down' : 'up'}>{r.delta}</span
						>{/if}
				</dd>
			</div>
		{/each}
	</dl>
{/if}

{#if tape?.line_remark}
	<p class="tape-remark">{tape.line_remark}</p>
{/if}
