import { error } from '@sveltejs/kit';
import topics from '$lib/data/topics.json';
import digests from '$lib/data/digests.json';

export const entries = () => topics.map((t) => ({ slug: t.slug }));

export function load({ params }) {
	const topic = topics.find((t) => t.slug === params.slug);
	if (!topic) error(404, `no topic ${params.slug}`);
	return { topic, digests: digests.filter((d) => d.topics.includes(topic.topic)) };
}
