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

## [0.4.0] - 2024-06-02

### Added
* Add option to pass a custom HTTPX Client to Unparallel (#186) @RafaelWO

### Changed
* Use ruff instead of black and isort (#165) @RafaelWO
* Refactor tests and mock URLs (#169) @RafaelWO
* Use bump-my-version instead of bump2version (#141) @RafaelWO
* Update dependencies due to CVEs (#197) @RafaelWO

### Fixed
* Fix Code Blocks in Docs (use pytest-examples for testing) (#146) @RafaelWO
* Fix synchronization of async tasks and HTTPX timeouts by using a semaphore with the
same value as ``max_connections`` (#197) @RafaelWO

## [0.3.0] - 2024-03-02

### Added
* **Breaking Change**: Support different URLs per request (#108) @RafaelWO
* Feature: Add parameter to configure custom response function (#109) @RafaelWO
* Feature: Publish to PyPI within GitHub CI (#129) @RafaelWO

### Changed
* Change: Mitigate timeouts by adding Semaphore (#128) @RafaelWO
* Dependencies:
  * Downgrade pytest to 7.4.4 to match pytest-asyncio requirement (#123) @RafaelWO
  * Upgrade multiple packages manually (#133) @RafaelWO

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


## [0.1.0] - 2023-12-09

### Added

* Final improvements for initial release (#79) @RafaelWO
* Add code for MVP (#72) @RafaelWO
* Add docs via MkDocs (#80) @RafaelWO


[unreleased]: https://github.com/RafaelWO/unparallel/compare/0.4.0...HEAD
[0.4.0]: https://github.com/RafaelWO/unparallel/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/RafaelWO/unparallel/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/RafaelWO/unparallel/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/RafaelWO/unparallel/releases/tag/0.1.0
