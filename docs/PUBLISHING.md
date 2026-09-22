# Publication readiness

Checked on 2026-09-22 for version 0.4.0. This is a locally validated release
candidate, not a published GitHub release or an approved marketplace listing.

## Identity and listing

- Repository to publish: `https://github.com/ilysorc/omarchy-mouse-style`.
- Permanent plugin ID: `ilysorc.mouse-style`; display name: Mouse Style.
- Release tag: `v0.4.0`. Use a GitHub prerelease for this first public candidate.
- Marketplace category: Hardware. Tags: `bar`, `hyprland`, `quickshell`.
- License: GPL-2.0-or-later, with retained BSD Windows and GPL libpointing notices.
- Root `preview.png` captures the current real panel, including its profile icon;
  it contains no other windows or personal information.

GitHub authentication is available for the owner account, but the repository
does not exist yet. The plugin ID was absent from the current marketplace
registry, including retired IDs. Recheck uniqueness before submitting.

## Checked locally

- Omarchy manifest validation passes.
- 70 Python tests pass, including fresh install, rollback, missing dependencies,
  denied authentication, trial/readiness races, and removal. Two release-path
  tests cover installing from the plugin's own Git checkout and refusing to
  overwrite a different Git-managed checkout.
- A fresh build of both native modules succeeds against Hyprland 0.56.2.
  All 24 native tests and 1,280 published Mac reference samples pass.
- Actual QML panel controls, queued polling and first-use setup tests pass.
- The candidate was installed through the real unified installer. Both native
  modules built and passed activation checks; source and installed readiness are
  true. Saved profile/UI files are byte-for-byte unchanged, no trial is pending,
  and Hyprland reports no configuration errors.
- QML lint reports no project warnings or errors. Three known warnings come
  from Quickshell's missing `QProcess::ExitStatus` type metadata; they are
  explicitly reported, and the real process signal is exercised by QML tests.
- `tools/check_release.py` checks pinned vendor hashes, version consistency,
  entry points, preview limits, source archive/checksum and extracted bundle
  identity. Native binaries and private research/build caches are excluded.
- The hosted GitHub Actions workflow is prepared. It has **not run on GitHub**;
  its first successful run is still a publication gate. It never uses personal
  self-hosted runners. Desktop/QML checks are separate from that portable job.

Missing-package and failure cases use isolated homes and controlled commands.
A separate clean Omarchy OS/VM install, wider mouse/monitor coverage, and future
Hyprland versions are not verified. Mac uses measured Sequoia tables and does
not claim exact modern macOS parity. These limits are public in the README.

## Marketplace preflight

The marketplace's static analysis functions were run locally on 19 selected
working-tree files, using marketplace commit
`db4c6873015f573e78586a2c8e4097a8f134ef52`.
Result: zero findings, capabilities `installer`, `package-manager`, `privilege`,
disposition `review-required`, `blocksApproval: false` under the selective policy.
The local report is `build/marketplace-preflight.json`.

This preparation check is not an official remote snapshot scan or approval.
After submission, the marketplace must fetch and scan the exact public commit,
and a maintainer must review its results. Request `manual-setup` because adding
the repository requires clicking **Install / Repair** once. That action installs
missing dependencies and builds both native modules; Omarchy's plugin manager
does not automatically execute third-party install hooks.

## Remaining publication steps

1. Publish the reviewed source to the owner's public GitHub repository.
2. Wait for the hosted Checks workflow to pass; fix failures before tagging.
3. Create `v0.4.0` from the checked commit and publish the prerelease with the
   source archive, SHA-256 file and [release notes](releases/0.4.0.md).
4. Review the completed [submission draft](MARKETPLACE-SUBMISSION.md) with the
   owner after the public URL works. Confirm all five checklist statements,
   including ownership of source and preview assets.
5. Submit one issue titled `[Plugin]: Mouse Style`. Follow its validation results
   and maintainer review; do not open duplicate submissions.
6. A maintainer finalizes setup labels and applies `approved-and-verified` after
   reviewing the exact commit. Verify that the listing actually appears.

The repository, release and marketplace issue have not been created by this
readiness check. There is no public download/listing URL to announce yet.

Primary instructions: [Publish](https://plugins.omarchy.org/publish.html),
[Develop](https://plugins.omarchy.org/develop.html), and the marketplace's
[CLI/agent submission contract](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md).
