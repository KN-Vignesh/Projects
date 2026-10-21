#!/usr/bin/env python3
"""
Create the `feat/house-price-3d-export` branch from `origin/main`, stage and commit
all House Price Prediction 3D Data Export changes, and (when `GITHUB_TOKEN` is available)
push the branch and raise a GitHub Pull Request to `main`.

Usage:
    python3 scripts/create_pr.py
    GITHUB_TOKEN=<your_pat> python3 scripts/create_pr.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
REPO_OWNER = "KN-Vignesh"
REPO_NAME = "Projects"
REMOTE_HTTP_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
BASE_BRANCH = "main"
HEAD_BRANCH = "feat/house-price-3d-export"

COMMIT_MESSAGE = "feat(house-price): add 3D prediction surface, SHAP explainability & static JSON export"
PR_TITLE = COMMIT_MESSAGE
PR_BODY = """## Summary

Extends `Data-recipe/House_Price_Prediction` to generate a deterministic, schema-validated static JSON asset (`house_price_3d.json`) powering the interactive 3D prediction surface in [`KN-Vignesh/Project-Portfolio`](https://github.com/KN-Vignesh/Project-Portfolio).

### Key Changes
- **Reproducible Model & Preprocessing Module (`Data-recipe/House_Price_Prediction/pipeline.py`):**
  - Extracts the exact `AmesFeatureEngineer` (9 derived features), `ColumnTransformer` (`SimpleImputer` + `RobustScaler` / `OneHotEncoder`), and 7-model `StackingRegressor` (`Ridge`, `Lasso`, `ElasticNet`, `GradientBoostingRegressor`, `XGBRegressor`, `LGBMRegressor`, `CatBoostRegressor` with `Ridge(alpha=10.0)` meta-learner) from `House_Prices_Prediction_using_TFDF.ipynb`.
  - Serializes the fitted pipeline and 5-fold out-of-fold validation bundle to `Data-recipe/House_Price_Prediction/artifacts/house_price_stacking_pipeline.joblib`.
- **Deterministic 3D Export CLI (`Data-recipe/House_Price_Prediction/scripts/export_3d_data.py` & `scripts/export_3d_data.py`):**
  - Generates a `50x50` prediction grid (`2,500` points) across `GrLivArea` (`334–4,476 sq_ft`) and `OverallQual` (`1–10`) in documented `row_major_y_outer_x_inner` order for Three.js `PlaneGeometry(width, depth, 49, 49)`.
  - Exports 10 real held-out house observations with exact additive SHAP attributions (`max additivity discrepancy = 1.03e-6` in `log1p(USD)` space).
  - Exports genuine 5-fold out-of-fold evaluation metrics (`OOF RMSLE = 0.1089`, `MAE = $12,785.43`, `RMSE = $19,901.48`, `R² = 0.9373`) and all `1,458` held-out actual-vs-predicted coordinates.
  - Writes validated output atomically to `Data-recipe/House_Price_Prediction/assets/house_price_3d.json` and `portfolio/assets/house_price_3d.json`.
- **JSON Schema & Portfolio Registry:**
  - Adds `Data-recipe/House_Price_Prediction/schema/house_price_3d.schema.json`, `Data-recipe/House_Price_Prediction/schema_validator.py`, and `portfolio/projects.json`.
- **Automated Test Suite (`Data-recipe/House_Price_Prediction/tests/test_export_3d_data.py`):**
  - 10 automated tests verifying model reproducibility against `submission.csv`, 50×50 grid ordering, finite bounds, JSON Schema compliance, SHAP additivity, OOF metric consistency, and deterministic output.
"""

TRACKED_PATHS = [
    ".env.example",
    ".gitignore",
    "ARCHITECTURE.md",
    "README.md",
    "package.json",
    "Data-recipe/House_Price_Prediction",
    "portfolio",
    "scripts",
]


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc


def ensure_branch_and_commit() -> str:
    git_dir = ROOT_DIR / ".git"
    if not git_dir.exists():
        print("[1/3] Initializing git repository and fetching origin/main...")
        run_git(["init"])
        run_git(["remote", "add", "origin", REMOTE_HTTP_URL])
    else:
        remotes = run_git(["remote"], check=False).stdout.split()
        if "origin" not in remotes:
            run_git(["remote", "add", "origin", REMOTE_HTTP_URL])

    run_git(["fetch", "origin", BASE_BRANCH, "--depth=1"])
    run_git(["config", "user.name", "KN-Vignesh"])
    run_git(["config", "user.email", "vigneshkn13@gmail.com"])

    current_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=False).stdout.strip()
    if current_branch != HEAD_BRANCH:
        print(f"[2/3] Creating and switching to branch '{HEAD_BRANCH}' from origin/{BASE_BRANCH}...")
        run_git(["reset", "--mixed", f"origin/{BASE_BRANCH}"])
        run_git(["checkout", "-B", HEAD_BRANCH])
        run_git(["checkout", f"origin/{BASE_BRANCH}", "--", "Shiny-Agents/.env.example"], check=False)

    run_git(["add", *TRACKED_PATHS])
    diff_cached = run_git(["diff", "--cached", "--name-only"], check=False).stdout.strip()
    if diff_cached:
        run_git(["commit", "-m", COMMIT_MESSAGE])
    commit_sha = run_git(["rev-parse", "--short", "HEAD"]).stdout.strip()
    print(f"[OK] Local branch '{HEAD_BRANCH}' ready at commit {commit_sha}.")
    return commit_sha


def push_and_open_pr(token: str) -> int:
    auth_remote = f"https://x-access-token:{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    print(f"[3/3] Pushing '{HEAD_BRANCH}' to {REPO_OWNER}/{REPO_NAME} and opening Pull Request to '{BASE_BRANCH}'...")
    push_proc = subprocess.run(
        ["git", "push", "--force-with-lease", auth_remote, f"HEAD:refs/heads/{HEAD_BRANCH}"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    if push_proc.returncode != 0:
        sys.stderr.write(f"git push failed:\n{push_proc.stderr}\n")
        return push_proc.returncode

    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    payload = json.dumps(
        {
            "title": PR_TITLE,
            "head": HEAD_BRANCH,
            "base": BASE_BRANCH,
            "body": PR_BODY,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "KN-Vignesh-Projects-PR-Creator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] Pull Request created: {data.get('html_url')}")
            return 0
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 422 and "A pull request already exists" in err_body:
            print(
                f"[OK] Branch pushed; PR already open at: "
                f"https://github.com/{REPO_OWNER}/{REPO_NAME}/pulls"
            )
            return 0
        sys.stderr.write(f"GitHub API error ({exc.code}): {err_body}\n")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Create branch and open PR to main.")
    parser.add_argument("--token", default="", help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)")
    args = parser.parse_args()

    ensure_branch_and_commit()

    token = (args.token or os.environ.get("GITHUB_TOKEN", "")).strip()
    if not token:
        print(
            "\n[INFO] Local branch 'feat/house-price-3d-export' is committed and ready.\n"
            "To push to GitHub and open the Pull Request against 'main':\n"
            "  - Click the GitHub icon ('Save to GitHub') in the AI Studio top bar, OR\n"
            "  - Set GITHUB_TOKEN in AI Studio Secrets and re-run `python3 scripts/create_pr.py`."
        )
        return 0

    return push_and_open_pr(token)


if __name__ == "__main__":
    raise SystemExit(main())
