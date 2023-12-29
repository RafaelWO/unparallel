# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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


[unreleased]: https://github.com/RafaelWO/unparallel/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/RafaelWO/unparallel/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/RafaelWO/unparallel/releases/tag/v0.1.0
