import digests from '$lib/data/digests.json';

// Today is the home page: job one is reading the newest digest and deciding.
export const load = () => ({ digest: digests[0] ?? null, older: digests[1]?.date ?? null });
