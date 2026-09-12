/**
 * One finder, shared by the masthead field and the results body. Retrieval is a
 * job, not a page — so this state lives above the routes and every page can be
 * replaced by results without navigating.
 */
export const finder = $state({
	q: '',
	firm: '',
	lens: '',
	band: 0,
	topic: '',
	rows: null
});

export const isActive = () =>
	Boolean(finder.q.trim() || finder.firm || finder.lens || finder.band || finder.topic);

export function reset() {
	finder.q = '';
	finder.firm = '';
	finder.lens = '';
	finder.band = 0;
	finder.topic = '';
}

// the row index is the one heavy payload. Load it the first time it is needed,
// so no page pays for search it did not use.
export async function ensureRows() {
	if (!finder.rows) finder.rows = (await import('./data/rows.json')).default;
}
