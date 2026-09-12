import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

// Static output. Digests change once a day from cron, so every page is built,
// never rendered on request. Nothing runs on the server.
export default {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter({ pages: 'build', assets: 'build', fallback: null, strict: true }),
		// a fresh box has no digests yet, so the dynamic routes generate zero
		// entries. That is an empty site, not a broken build.
		prerender: { handleHttpError: 'fail', handleUnseenRoutes: 'warn' }
	}
};
