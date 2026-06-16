# Set up CI/CD pipeline for the project

## Description
Establish a continuous integration and deployment pipeline for the project using GitHub Actions. The pipeline will automatically run tests on every push, enforce code style through linting, and deploy to a staging environment. All tooling must use free tier services and the entire pipeline should complete in under 5 minutes.

## Steps
1. Choose a CI platform — Select GitHub Actions as the CI/CD platform (free tier, tightly integrated with GitHub repositories)
2. Write a workflow config that runs tests on push — Create a `.github/workflows/ci.yml` file that triggers on push and runs the test suite
3. Add linting step — Extend the workflow to include a code linting job (e.g., flake8 or ruff for Python, ESLint for JavaScript)
4. Add deployment step to staging — Add a deployment job that deploys to a staging environment after tests and linting pass
5. Test the pipeline end-to-end — Push changes, verify the full pipeline runs successfully, and confirm staging deployment

## Success Criteria
- All tests pass on every push
- Linting catches style issues automatically
- Staging deploy is automatic after tests and linting succeed

## Constraints
- Must use free tier services (GitHub Actions free tier)
- Pipeline should complete in under 5 minutes
- No paid CI/CD platforms or services
