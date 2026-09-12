<script>
	// One stroke weight, drawn. No icon font, no glyph standing in for a mark.
	let { name, size = 16 } = $props();
	const paths = {
		search: 'M7.2 1.8a5.4 5.4 0 1 0 0 10.8 5.4 5.4 0 0 0 0-10.8ZM11.2 11.2 14.4 14.4',
		left: 'M9.5 3.5 5 8l4.5 4.5',
		right: 'M6.5 3.5 11 8l-4.5 4.5',
		alert: 'M8 2.6 14.4 13.4H1.6L8 2.6ZM8 6.7v3M8 11.4h.01'
	};
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 16 16"
	fill="none"
	stroke="currentColor"
	stroke-width="1.5"
	stroke-linecap="round"
	stroke-linejoin="round"
	aria-hidden="true"
>
	<path d={paths[name]} />
</svg>
