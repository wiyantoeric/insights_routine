import { sveltekit } from '@sveltejs/kit/vite';

const host = process.env.VITE_HOST || '127.0.0.1';

const allowedHosts = ['.ts.net'];

export default {
	plugins: [sveltekit()],
	server: { host, allowedHosts },
	preview: { host, allowedHosts }
};
