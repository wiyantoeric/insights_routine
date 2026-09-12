// every page is built at build time
export const prerender = true;
// directory-style output: build/archive/index.html, not build/archive.html, so
// the folder serves correctly from any static server, python -m http.server included
export const trailingSlash = 'always';
