# Releasing WalBridge

WalBridge ships as source through an annotated Git tag and a GitHub Release. The installer compiles the Swift tools on the user's Mac. This process does not publish a package, ship a prebuilt app, or deploy a service.

Use `<VERSION>` for the authorized tag, including its leading `v`, and `<CANDIDATE_SHA>` for the exact commit approved for release.

## Prepare the candidate

1. Confirm that the owner has authorized the release.
2. Fetch `origin` and its tags. Check that `main` is clean, matches `origin/main`, and contains `<CANDIDATE_SHA>`.
3. Stop if `<VERSION>` already exists as a local tag, remote tag, or GitHub Release.
4. Move the relevant `[Unreleased]` entries into a dated section for `<VERSION>`. Keep a new empty `[Unreleased]` section at the top.
5. Use the versioned changelog bullets, verbatim and in order, as the GitHub Release body. Review the notes in a file before any public write.

```bash
git fetch --prune --tags origin
git switch main
git pull --ff-only origin main
git status --short
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count main...origin/main
git tag --list '<VERSION>'
git ls-remote --tags origin 'refs/tags/<VERSION>'
gh release view '<VERSION>' --repo paul-cch/WalBridge
```

## Prove the candidate

Run the checks in `CONTRIBUTING.md` and the full local equivalents of `.github/workflows/ci.yml`. Include fresh dependency resolution, `pip check`, all Python tests, Ruff, Bash syntax, ShellCheck, Quartz import and display detection, both Swift builds and runtime smokes, and a sandboxed installer run that cannot change the live launchd session.

Push the release-preparation PR and require every CI job on `<CANDIDATE_SHA>` to pass. Record the exact workflow URL and job results. A green run on an earlier commit is not release proof.

Refresh direct dependencies and the GitHub Advisory Database before tagging. Record current and resolved versions, relevant advisories, and any deferred update with its reason.

User-visible runtime changes need live-host proof on the exact candidate. If a safe live target is unavailable, stop unless the owner gives an explicit release-specific waiver. Record the proof or waiver with the release evidence.

Before each public write, run both gates against the exact candidate diff, tests, fixtures, generated files, local and CI logs, release notes, proof text, and source archive contents:

- Privacy gate: block secrets, credentials, private paths, personal data, and non-public infrastructure details.
- Public Model Identifier Gate: allow only identifiers documented in an official public provider source. Do not repeat an unknown or blocked identifier in the report.

Both gates must return `PASS`. Any change to an audited file, log, note, or artifact invalidates the result and requires another audit.

## Create the tag and release

Set the placeholders only after the candidate passes every gate. The notes file must contain the reviewed changelog section.

```bash
VERSION='<VERSION>'
CANDIDATE_SHA='<CANDIDATE_SHA>'
RELEASE_NOTES_FILE='<REVIEWED_RELEASE_NOTES_FILE>'

test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"
test "$(git rev-parse origin/main)" = "$CANDIDATE_SHA"
git diff --quiet
git diff --cached --quiet

git tag -a "$VERSION" "$CANDIDATE_SHA" -m "WalBridge $VERSION"
git push origin "$VERSION"
gh release create "$VERSION" \
  --repo paul-cch/WalBridge \
  --verify-tag \
  --title "WalBridge $VERSION" \
  --notes-file "$RELEASE_NOTES_FILE"
```

## Verify and close out

Verify that the release is public, is not a draft or prerelease, and points to `<CANDIDATE_SHA>`. Confirm that its title and notes match the reviewed values. Download GitHub's automatic source archives and test that both can be listed without errors.

```bash
VERSION='<VERSION>'
CANDIDATE_SHA='<CANDIDATE_SHA>'
VERIFY_DIR="$(mktemp -d)"

test "$(git rev-list -n 1 "$VERSION")" = "$CANDIDATE_SHA"
gh release view "$VERSION" \
  --repo paul-cch/WalBridge \
  --json url,tagName,name,isDraft,isPrerelease,targetCommitish,assets
git ls-remote --tags origin "refs/tags/$VERSION" "refs/tags/$VERSION^{}"

curl -fsSL "https://github.com/paul-cch/WalBridge/archive/refs/tags/$VERSION.tar.gz" \
  -o "$VERIFY_DIR/source.tar.gz"
curl -fsSL "https://github.com/paul-cch/WalBridge/archive/refs/tags/$VERSION.zip" \
  -o "$VERIFY_DIR/source.zip"
tar -tzf "$VERIFY_DIR/source.tar.gz" >/dev/null
unzip -tq "$VERIFY_DIR/source.zip"

git switch main
git pull --ff-only origin main
git status --short
git rev-list --left-right --count main...origin/main
```

Keep the release proof with the release or its preparation PR. Record the tag, candidate commit, release URL, CI URL, dependency and advisory results, live proof or waiver, gate results, and source archive checks.

## Abort rules

Stop before tagging if the checkout is dirty, `main` differs from `origin/main`, the candidate SHA changes, CI is incomplete or failing, dependency or advisory evidence is stale, live proof or its waiver is missing, either public gate is blocked, or the notes differ from the changelog.

After pushing a tag, do not move or delete it as routine recovery. If GitHub Release creation fails, retry against the same tag and commit. If a published release is defective, preserve its tag and prepare a corrective release.
