# Release

## Prerequisites

- A clone of
  [mon-compte-deploiement](https://github.com/suitenumerique/mon-compte-deploiement)
  next to this repository (`../mon-compte-deploiement`).
- A clean working tree on an up-to-date `main`: the script branches from the
  current `HEAD`, so any local commit would end up in the release.

## Run

```bash
make release DRY_RUN=1   # shows the changes, does nothing
make release
```

The script asks for the kind of release (`p`, `m`, `mj`) and the version, then:

1. creates the `release/X.Y.Z` branch and rebases it on `origin/main`;
2. moves `[Unreleased]` to `[vX.Y.Z] - <date>` in `CHANGELOG.md`;
3. bumps the version in `src/backend/pyproject.toml`, `src/backend/uv.lock`
   and the `package.json` files under `src/frontend`;
4. commits and pushes the branch after confirmation;
5. in `../mon-compte-deploiement`, creates the `X.Y.Z/preprod` branch with the preprod image tags set to `vX.Y.Z`, commits and pushes
   after confirmation.

The script does not create the git tag: it must point to the commit merged
into `main`, which only exists once the steps below are done.

## After the script

1. Wait for the Crowdin GitHub action to open the `i18n/update-translations`
   PR, then approve and merge it into `release/X.Y.Z`.
2. Open the `release/X.Y.Z` PR and merge it into `main`.
3. Tag the merged commit and push the tag:

   ```bash
   git checkout main
   git pull
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. Wait for the `vX.Y.Z` images to be published on Docker Hub
   ([backend](https://hub.docker.com/r/lasuite/accounts-backend/tags),
   [frontend](https://hub.docker.com/r/lasuite/accounts-frontend/tags)).
5. Manually launch the image signing for `vX.Y.Z`, for preprod and prod. This
   must be done before deploying.
6. Create the GitHub release for the `vX.Y.Z` tag.
7. In `mon-compte-deploiement`, on the `X.Y.Z/preprod` branch, the script
   already set the image tags to `vX.Y.Z`. If the release needs it, add
   commits to:
   - bump the chart version in `manifests/mon-compte/helmfile.yaml.gotmpl`
     when the Helm chart changed;
   - update `manifests/mon-compte/env.d/preprod/values.mon-compte.yaml.gotmpl`
     when the release adds, renames or removes environment variables or
     other settings.

   Then open the PR and merge it into `main`.
