# Repository Architecture

## Purpose
This repository serves as the **content source and documentation hub** for AI/ML projects.  
It is **NOT** a standalone portfolio website.

---

## Primary Portfolio Website

**Main Portfolio UI:**  
🌐 https://vignesh-kn-portfolio.vercel.app/

**Repository:**  
📦 https://github.com/KN-Vignesh/Project-Portfolio

The Project-Portfolio repository contains a modern React 19 + TypeScript application that:
- Fetches project data from this repository at runtime
- Provides interactive 3D visualizations
- Includes an AI assistant powered by Gemini
- Offers PWA support for offline access
- Generates downloadable resume PDFs

---

## This Repository's Role

**Content Source Only:**
1. **Project Documentation** - READMEs, notebooks, and technical writeups
2. **Code Examples** - Jupyter notebooks, Python scripts, and project files
3. **Data Files** - Datasets, models, and configuration files
4. **Metadata** - Project registry JSON for portfolio consumption

**Data Flow:**
```
Projects Repo (GitHub)
      ↓
   (Runtime Fetch)
      ↓
Project-Portfolio (Vercel)
      ↓
   User's Browser
```

---

## Repository Structure

```
Projects/
├── README.md                    # Main portfolio index
├── PORTFOLIO_ENHANCEMENT_STRATEGY.md
├── PHASE_0_VERIFICATION_REPORT.md
│
├── VERO/                        # Tier A: PR Review Engine
│   ├── README.md
│   ├── index.html               # React app (part of VERO project)
│   └── src/                     # VERO source code
│
├── Shiny-Agents/                # Tier A: Multi-Agent Systems
│   ├── README.md
│   ├── app/static/              # Agent interface (part of project)
│   └── [agent implementations]
│
├── Ai-Cookbook/                 # Deep Learning & LLM Experiments
│   ├── LoraFine-tuning/
│   ├── QLoraFine-Tuning/
│   ├── Combined_metric_Calc/
│   ├── BERT_MODEL/
│   └── CNN-Fundamentals/
│
├── Data-recipe/                 # Classical ML Pipelines
│   ├── House_Price_Prediction/
│   └── Titanic_Model/
│
└── [Individual Notebooks]       # Standalone experiments
```

---

## Important Notes

### Static Files in Project Directories
Some projects (VERO, Shiny-Agents) contain their own `index.html` and static assets.  
**These are legitimate project files and should NOT be removed.**

They serve project-specific purposes:
- **VERO/index.html** - Entry point for the PR review React application
- **Shiny-Agents/app/static/** - Web interface for the multi-agent system

### Former Docsify Portfolio Site
Previously, this repository hosted a Docsify-based documentation site with:
- `index.html` (Docsify shell)
- `assets/portfolio.css` (styling)
- `assets/portfolio.js` (scripts)

**Status:** Removed as of Phase 0 cleanup (2026-10-02)  
**Reason:** Eliminated duplication with primary Project-Portfolio site  
**Replacement:** Minimal redirect to primary portfolio

---

## For Developers

### Cloning This Repository
```bash
git clone https://github.com/KN-Vignesh/Projects.git
cd Projects
```

### Running Individual Projects
Each project directory contains its own README with setup instructions.

**Example - VERO:**
```bash
cd VERO
npm install
npm run dev
```

**Example - Shiny-Agents:**
```bash
cd Shiny-Agents
pip install -r requirements.txt
python app/server.py
```

### Jupyter Notebooks
Most notebooks are designed to run in Google Colab (free GPU access).

Click the "Open in Colab" badge in each notebook, or:
```bash
jupyter notebook
```

---

## Contributing

This is a personal portfolio repository, but feedback and suggestions are welcome!

**Found an issue?**  
Open an issue at: https://github.com/KN-Vignesh/Projects/issues

**Want to suggest improvements?**  
Contact: vigneshknagaraj@outlook.com

---

## Related Repositories

| Repository | Purpose | Technology |
|------------|---------|------------|
| [Project-Portfolio](https://github.com/KN-Vignesh/Project-Portfolio) | Primary portfolio UI | React 19, TypeScript, Vite |
| [Projects](https://github.com/KN-Vignesh/Projects) | Content source (this repo) | Markdown, Jupyter, Python |

---

## License

All projects and content © 2024 Vignesh K N

Individual projects may have specific licenses - refer to project directories.

---

## Contact

**Vignesh K N** - AI Software Engineer  
📧 vigneshknagaraj@outlook.com  
🔗 [LinkedIn](https://www.linkedin.com/in/vignesh-k-n/)  
🐙 [GitHub](https://github.com/KN-Vignesh)
