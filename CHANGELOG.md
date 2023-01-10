# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Handle failure in purl creation gracefully (custom components will probably be skipped)

## [1.1.3] - 2022-09-29
### Fixed
- Updated x bit for create_report.sh


## [1.1.2] - 2022-08-30
### Fixed
- purl creationg for pypi and npm
- Report name change to allow for deletion

## [1.1.1] - 2022-06-12
### Removed
- CVSS Version Option - use v3
### Fixed
- Vulnerability determination
### Added
- Presort inventory data by component name, component version and license name

## [1.1.0] - 2022-06-09
### Fixed
- Report name change
- Add purl elements
- Use Application Name and Application Version project attributes for report artifacts
- Change default setting for including vulnerability details

## [1.0.12] - 2022-05-23
### Fixed
- Registration updates

## [1.0.11] - 2022-02-19
### Fixed
- jstree hierachy display with duplicated child projects

## [1.0.10] - 2022-02-19
### Added
- Support self signed certificates

## [1.0.9] - 2021-12-15
### Changed
- Updated requirements

## [1.0.8] - 2021-12-01
### Changed
- Update submodules to flexera-public repos

## [1.0.7] - 2021-11-16
### Fixed
- Fixed support for server_properties.json file
### Changed
- Removed urllib logging

## [1.0.6] - 2021-11-08
### Added
- Add requrements file

## [1.0.5] - 2021-11-05
### Added
- Initial public release
- Common artifact names and times
- Updates for error report
- Common config file for registration and any report links

## [1.0.2] - 2021-10-25
### Added
- Add xlsx report artifact


## [1.0.1] - 2021-10-15
### Added
- Initial release of SBOM report
- HTML version of report created