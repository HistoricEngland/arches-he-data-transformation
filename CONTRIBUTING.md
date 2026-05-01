# Contributing to arches-he-data-transformation

We welcome contributions to Arches-HER. This guide follows the same general approach as the
[Arches contributing guide](https://github.com/archesproject/arches/blob/dev/8.1.x/CONTRIBUTING.md),
with arches-he-data-transformation specific requirements described below.

- [Contributing to arches-he-data-transformation](#arches-he-data-transformation)
  - [Found an Issue?](#found-an-issue)
  - [Contributing Code](#contributing-code)
    - [Keeping your branch up to date](#keeping-your-branch-up-to-date)
  - [Shared Development Branches](#shared-development-branches)
  - [Commit Message Guidelines](#commit-message-guidelines)
  - [arches-he-data-transformation Specific Requirements](#arches-he-data-transformation-specific-requirements)
    - [Accessibility](#accessibility)
  - [Contributing Documentation](#contributing-documentation)

  ## Found an Issue?

If you find a bug, please open an issue in the `HistoricEngland/arches-he-data-transformation` repository and include:

- clear steps to reproduce
- expected vs actual behaviour
- screenshots/gifs where relevant
- environment details (Arches version, browser, OS)

Please check existing open/closed issues first to avoid duplicates.

## Contributing Code

1. Fork `HistoricEngland/arches-he-data-transformation` and clone your fork.
2. Create a feature branch from the current enhancement branch (this should be the default when you first clone the repo)

   ```shell
   git checkout -b 1231_short_description release/1.1.x
   ```

3. Make focused changes for one issue/feature.
4. Run relevant tests locally:

   ```shell
   python manage.py test tests --settings="tests.test_settings"
   ```

5. Commit and push your branch.
6. Open a pull request against `HistoricEngland/arches-he-data-transformation`.

### Keeping your branch up to date

If requested during review, rebase your branch against the current enhancement branch, e.g. `release/1.1.x`, and force-push:

```shell
git rebase release/1.1.x -i
git push origin my-fix-branch -f
```

## Shared Development Branches

Arches-HER follows long-lived `release/A.B.x` branches for ongoing development, that allow future enhancements to be made to the next release (the default branch) while the current release is being stabilized. For example, `release/1.1.x` is the current default and is receiving minor enhancments and fixes. The previous release branch, `release/1.0.x`, would continue to receive critical bug fixes.

When a new major version is being developed, a new `release/2.0.x` branch will be created for that work, and `release/1.1.x` will continue to receive bug fixes and minor improvements until the next major release.

Contributors should normally branch from the current default branch unless a reviewer asks for a different target.

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature").
- Use imperative mood ("Fix bug" not "Fixes bug").
- Keep the first line to 72 characters or fewer.
- Reference the related issue where possible.

## arches-he-data-transformation Specific Requirements

### Accessibility

arches-he-data-transformation contributions must maintain WCAG 2.2 AA accessibility standards. In particular:

- preserve keyboard accessibility and visible focus order
- ensure sufficient contrast and readable content structure
- provide meaningful labels/text alternatives for controls and media

Include accessibility considerations in PR descriptions for UI changes.

## Contributing Documentation

arches-he-data-transformation currently has no separate documentation repository.

For documentation updates:

- update `README.md` as the primary developer/user-facing documentation
- include any setup, configuration, and operational changes needed to run the application
- where relevant, link to core Arches documentation for shared platform behaviour

Thank you for contributing to arches-he-data-transformation.