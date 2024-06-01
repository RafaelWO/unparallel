# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Types of changes:
    Added for new features.
    Changed for changes in existing functionality.
    Deprecated for soon-to-be removed features.
    Removed for now removed features.
    Fixed for any bug fixes.
    Security in case of vulnerabilities.
-->

## [Unreleased]

### Fixed
* Fix synchronization of async tasks and HTTPX timeouts by using a semaphore with the
same value as ``max_connections`` (#197) @RafaelWO

## [0.3.0] - 2024-03-02

### Added
* **Breaking Change**: Support different URLs per request (#108) @RafaelWO
* Feature: Add parameter to configure custom response function (#109) @RafaelWO
* Feature: Publish to PyPI within GitHub CI (#129) @RafaelWO

### Changed
* Change: Mitigate timeouts by adding Semaphore (#128) @RafaelWO
* Bump pytest from 7.4.3 to 7.4.4 (#110) @dependabot
* Bump tj-actions/verify-changed-files from 16 to 17 (#111) @dependabot
* Bump pytest-asyncio from 0.23.2 to 0.23.3 (#112) @dependabot
* Bump mkdocstrings-python from 1.7.5 to 1.8.0 (#114) @dependabot
* Bump actions/cache from 3.3.2 to 3.3.3 (#113) @dependabot
* Bump mkdocs-material from 9.5.3 to 9.5.4 (#115) @dependabot
* Bump actions/cache from 3.3.3 to 4.0.0 (#116) @dependabot
* Bump bandit from 1.7.6 to 1.7.7 (#117) @dependabot
* Bump coverage from 7.4.0 to 7.4.1 (#118) @dependabot
* Bump pytest from 7.4.4 to 8.0.0 (#119) @dependabot
* Bump pytest-asyncio from 0.23.3 to 0.23.4 (#120) @dependabot
* Bump mkdocs-material from 9.5.4 to 9.5.6 (#122) @dependabot
* Downgrade pytest to 7.4.4 to match pytest-asyncio requirement (#123) @RafaelWO
* Bump tj-actions/verify-changed-files from 17 to 18 (#124) @dependabot
* Bump release-drafter/release-drafter from 5.25.0 to 6.0.0 (#125) @dependabot
* Bump mkdocs-material from 9.5.6 to 9.5.7 (#126) @dependabot
* Bump tqdm from 4.66.1 to 4.66.2 (#131) @dependabot
* Bump actions/cache from 3 to 4 (#130) @dependabot
* Bump pytest-asyncio from 0.23.4 to 0.23.5 (#132) @dependabot
* Bump pytest from 7.4.4 to 8.0.0 (#127) @dependabot
* Bump mkdocs-material from 9.5.7 to 9.5.9 (#134) @dependabot
* Bump safety from 2.4.0b2 to 3.0.1 (#133) @dependabot
* Upgrade multiple packages manually (#133) @RafaelWO
* Bump pytest from 8.0.1 to 8.0.2 (#139) @dependabot

### Fixed
* Fix: Code in Docs (#138) @RafaelWO


## [0.2.0] - 2023-12-29

### Added
* Feature: Configure HTTPX timeouts and limits (#87) @RafaelWO
* Feature: Add support for single payload for multiple paths (#101) @RafaelWO
* Docs: Add a changelog (#107) @RafaelWO
* Docs: Add versioning via mike (#106) @RafaelWO
* Docs: Add section "Why?" with GIF to README (#82) @RafaelWO
* Docs: Add more detailed usage examples (#105) @RafaelWO

### Changed

* **Breaking Change**: To be in line with HTTPX's options, the parameter `connection_limit` was renamed to `max_connections` in function `up()` (#87) @RafaelWO
* Bump mypy from 1.7.0 to 1.7.1 (#76) @dependabot
* Bump pytest-asyncio from 0.21.1 to 0.23.2 (#78) @dependabot
* Bump mkdocs-material from 9.5.1 to 9.5.2 (#92) @dependabot
* Bump coverage from 7.3.2 to 7.3.3 (#91) @dependabot
* Bump actions/setup-python from 4 to 5 (#83) @dependabot
* Bump httpx from 0.25.2 to 0.26.0 (#97) @dependabot
* Bump mypy from 1.7.1 to 1.8.0 (#96) @dependabot
* Bump mkdocs-material from 9.5.2 to 9.5.3 (#95) @dependabot
* Bump coverage from 7.3.3 to 7.3.4 (#94) @dependabot
* Bump black from 23.11.0 to 23.12.1 (#93) @dependabot
* Bump isort from 5.12.0 to 5.13.2 (#89) @dependabot
* Bump pylint from 3.0.2 to 3.0.3 (#88) @dependabot


## [0.1.0] - 2023-12-09

### Added

* Final improvements for initial release (#79) @RafaelWO
* Add code for MVP (#72) @RafaelWO
* Add docs via MkDocs (#80) @RafaelWO


[unreleased]: https://github.com/RafaelWO/unparallel/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/RafaelWO/unparallel/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/RafaelWO/unparallel/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/RafaelWO/unparallel/releases/tag/v0.1.0
