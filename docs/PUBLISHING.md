# Publication readiness

Validation and publication record for version 1.0.0, checked on 2026-09-22.
Local validation and a GitHub release do not imply marketplace approval.

## Identity and listing

- Repository: `https://github.com/ilysorc/omarchy-pointer-feel`.
- Permanent plugin ID: `ilysorc.pointer-feel`; display name: Pointer Feel.
- Planned first release: `v1.0.0`, a regular GitHub release. The Mac profile
  remains experimental; the application version does not expand hardware or
  compositor support.
- Marketplace category: Hardware. Tags: `bar`, `hyprland`, `quickshell`.
- License: GPL-2.0-or-later, with retained BSD Windows and GPL libpointing notices.
- Root `preview.png` captures the current real bar and panel, including the filled
  click cursor and active profile icon;
  it contains no other windows or personal information.

The owner authorized making the repository public, releasing 1.0.0 and submitting
it to the marketplace on 2026-09-22. The plugin ID has no collision in the checked
marketplace registry, including retired IDs. Marketplace approval remains a
separate maintainer decision.

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
- The hosted [Checks run for the final code change](https://github.com/ilysorc/omarchy-pointer-feel/actions/runs/35767876536)
  passed. Each later candidate must pass its own run before release. The workflow
  never uses personal self-hosted runners; desktop/QML checks run separately.

Missing-package and failure cases use isolated homes and controlled commands.
A separate clean Omarchy OS/VM install, wider mouse/monitor coverage, and future
Hyprland versions are not verified. Mac uses measured Sequoia tables and does
not claim exact modern macOS parity. These limits are documented in the README.

On 2026-09-22, the owner chose to skip the recommended clean Omarchy OS/VM
installation test for 1.0.0. It is not a release prerequisite. Its status remains
untested; this decision does not count as additional installation evidence.

## Marketplace preflight

For the 1.0.0 preparation on 2026-09-22, the marketplace's static analysis
functions ran on 19 selected working-tree files, using marketplace commit
`cef825b030fbd738fdccb61d1f1b980200d8625f`.
Result: zero findings, capabilities `installer`, `package-manager`, `privilege`,
disposition `review-required`, `blocksApproval: false` under the selective policy.
The same registry snapshot has no occurrence of `ilysorc.pointer-feel`, including
retired identifiers. The local report is in
`build/final-publish-review.json`; it is not part of the distribution.
The submission's six headings, category, tags and checklist text match the
official parser. Documentation links, source/archive contents and a targeted
Git-history scan for credential patterns were also checked. That pattern scan
is not a complete secret audit.
Rerun the preflight if the candidate or marketplace rules change before release.

This preparation check is not an official remote snapshot scan or approval.
After submission, the marketplace must fetch and scan the exact public commit,
and a maintainer must review its results. Request `manual-setup` because adding
the repository requires clicking **Install / Repair** once. That action installs
missing dependencies and builds both native modules; Omarchy's plugin manager
does not automatically execute third-party install hooks.

## Publication procedure

1. Confirm owner authorization for public distribution (received on 2026-09-22).
2. Wait for the hosted Checks workflow to pass; fix failures before tagging.
3. Create `v1.0.0` from the checked commit and publish the release with the
   source archive, SHA-256 file and [release notes](releases/1.0.0.md).
4. Verify that the public URL works and all five statements in the
   [submission record](MARKETPLACE-SUBMISSION.md) are true, including source and
   preview rights. The owner authorized submission as part of publication.
5. Submit one issue titled `[Plugin]: Pointer Feel`. Follow its validation results
   and maintainer review; do not open duplicate submissions.
6. A maintainer finalizes setup labels and applies `approved-and-verified` after
   reviewing the exact commit. Verify that the listing actually appears.

Record the release and marketplace issue URLs after publication. A submitted
issue is not an approved listing.

Primary instructions: [Publish](https://plugins.omarchy.org/publish.html),
[Develop](https://plugins.omarchy.org/develop.html), and the marketplace's
[CLI/agent submission contract](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md).
