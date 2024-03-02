# How to create a new Release
1. Checkout a new branch for the release, e.g. `release/x.x.x`
2. Run `bump2version <major|minor|patch>`
3. Update the `CHANGELOG.md` file (use the drafted GH release as a reference)
4. Push the changes, create a PR and merge it
5. Create tag via `git tag -a vx.x.x`and push
6. The package is automatically built and published within the CI
