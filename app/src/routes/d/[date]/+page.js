import { error } from '@sveltejs/kit';
import digests from '$lib/data/digests.json';

// explicit, so a page is built even if nothing links to it
export const entries = () => digests.map((d) => ({ date: d.date }));

export function load({ params }) {
	const i = digests.findIndex((d) => d.date === params.date);
	if (i === -1) error(404, `no digest for ${params.date}`);
	// digests are newest first
	return { digest: digests[i], newer: digests[i - 1]?.date ?? null, older: digests[i + 1]?.date ?? null };
}
