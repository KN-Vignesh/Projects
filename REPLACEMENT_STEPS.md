# Replacement steps

1. Replace `index.html`.
2. Replace `README.md`.
3. Replace `_navbar.md`.
4. Replace `_sidebar.md`.
5. Replace `assets/portfolio.css`.
6. Replace `assets/portfolio.js`.
7. Add `projects/customer-churn.md`.
8. Optional: `_coverpage.md` is no longer used because `coverpage: false` is intentional. You can keep it, but it will not be rendered.
9. Do not run the full navigation validation yet. First open the site and review the visual redesign.
10. For local testing, serve the repository root as a static site instead of using `npm run dev` / the VERO server. Example:

```bash
python -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/#/
```
