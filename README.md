# josephthachilgeorge.com

Bilingual (EN / DE) portfolio, built to static pages and deployed with GitHub Pages.

## Edit once, both languages update
Pages live in `src/`. Every translated element carries `data-en` and `data-de`.
`python3 build.py` emits English pages at `/` and German pages at `/de/`
(plus `sitemap.xml`, `robots.txt`, canonical, hreflang and Open Graph tags) into `dist/`.
The build fails on a missing translation, inline script/style, or a broken internal link.

## Preview
    python3 build.py && python3 -m http.server -d dist 8787

## Deploy
Push to `main`; `.github/workflows/deploy.yml` runs the build and publishes `dist/`.

## Notes
- Fonts (Inter, JetBrains Mono; OFL) are self-hosted in `src/fonts/`; no third-party requests.
- A strict Content-Security-Policy is injected via `{{HEAD_COMMON}}`; do not add inline `<script>`/`<style>`.
