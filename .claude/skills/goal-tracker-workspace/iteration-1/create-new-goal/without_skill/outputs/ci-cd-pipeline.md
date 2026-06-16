# Goal: Set up CI/CD Pipeline for the Project

**Created:** 2026-06-16
**Status:** in-progress

## Description

Set up a CI/CD pipeline for the project to automate testing, linting, and deployment to staging on every push.

## Steps

1. [x] Choose a CI platform (GitHub Actions)
2. [x] Write a workflow config that runs tests on push
3. [x] Add linting step
4. [x] Add deployment step to staging
5. [ ] Test the pipeline end-to-end

## Success Criteria

- All tests pass on every push
- Linting catches style issues
- Staging deploy is automatic

## Constraints

- Must use free tier services
- Should complete in under 5 minutes

## Progress Log

### 2026-06-16

- **Step 1 completed:** Selected GitHub Actions as the CI platform. It is free for public repositories (2,000 minutes/month for private repos on free tier), integrates natively with GitHub, and meets all constraints.

- **Steps 2-4 completed:** Created `.github/workflows/ci.yml` with three jobs:
  - `test` — runs `pytest` on every push to any branch (Python 3.12, ubuntu-latest)
  - `lint` — runs `ruff check .` on every push
  - `deploy-staging` — runs only on main/master after test+lint pass, deploys to staging (placeholder for real deploy command)
  - All jobs have `timeout-minutes` set to stay under the 5-minute constraint
  - Uses only free tier GitHub Actions runners (ubuntu-latest)

### Next Actions
- Add real tests to the project so the `test` job has something to run
- Replace the placeholder deploy step with actual deployment logic (e.g., rsync, SCP, or a cloud provider CLI)
- Configure `STAGING_HOST` and `STAGING_DEPLOY_KEY` secrets in the GitHub repository settings
- Push the workflow and verify it runs end-to-end on GitHub
