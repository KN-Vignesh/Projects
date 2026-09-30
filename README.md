# Projects Repository

This repository contains the actual project implementations, notebooks, source code, documentation, and project metadata for the work in this workspace.

The repository is intentionally kept as a developer-first project store. The portfolio UI itself is maintained separately in the portfolio repository, while this repository remains the source of truth for the code and documentation that the portfolio links to.

Portfolio metadata is maintained at:

- [portfolio/projects.json](portfolio/projects.json)

The portfolio UI lives separately here:

- [KN-Vignesh/Project-Portfolio](https://github.com/KN-Vignesh/Project-Portfolio)

The portfolio repository consumes the machine-readable project registry from this repository.

## Repository structure

- `Ai-Cookbook/` — notebooks, model engineering experiments, and supporting documentation
- `Data-recipe/` — data science and tabular ML projects
- `Shiny-Agents/` — agent and app experiments
- `VERO/` — the VERO application and its server/client implementation
- `docs/` — project architecture and deployment documentation
- `projects/` — project-specific documentation and supporting markdown
- root notebooks and datasets — project artifacts and reproducible experiments

## Important notes

- This repository is not a hosted portfolio site.
- The portfolio UI and presentation layer are not stored here.
- Project code, notebooks, and documentation remain in place and are the canonical source for implementation details.

## Typical commands

```bash
npm install
npm run build
npm start
```

The root package configuration supports the VERO application, while the actual project implementations remain in their original directories without being duplicated into the metadata registry.

## Project registry

The portfolio registry can be consumed directly from [portfolio/projects.json](portfolio/projects.json). It contains lightweight metadata only and points back to the real project files in this repository.
