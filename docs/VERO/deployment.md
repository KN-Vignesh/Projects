# Deployment

The repository is deployed as one Node application from its root. `npm install` installs the root server dependencies and the VERO workspace. `npm run build` builds the VERO client under `VERO/dist` and bundles the Express server under `dist/server.cjs`.

Run the production process with:

```bash
NODE_ENV=production npm start
```

The server exposes the VERO application at `/vero/` and the API at `/api/*`. The Vite base path is `/vero/`, so asset URLs and direct navigation remain correct after deployment. This repository remains a project/code repository rather than a hosted portfolio front end.

## Environment variables

- `GITHUB_TOKEN`: optional server-side GitHub token for higher public API limits.
- `TYPESAFE_API_KEY`: optional server-side TypeSafe Jev key.
- `GEMINI_API_KEY`: supported by the existing provider integration when live Gemini inference is enabled.
- `APP_URL`: optional public application URL.
- `SONARQUBE_URL` and `SONARQUBE_TOKEN`: reserved optional SonarQube configuration.

Do not commit `.env` files or secret values.