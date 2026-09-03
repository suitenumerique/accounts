All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- 💄(frontend) add intermediate login page
- ✨(frontend) init the frontend app (webapp + e2e)
- ✨(authentication) support multiple identity providers
- ✨(OIDC Provider) configure and customize the Authorization Server
- ✨(OIDC Provider) add a `guest` claim and the `account` scope

### Changed

- ✨(users) make `email` our username
- ✨(authentication) encrypt identity providers' `extra_data`
- 🔒(authentication) make the logout view POST-only
- 👽(authentication) handle Social Auth's login views requiring POST requests
- 🦖(OIDC Provider) make introspection endpoint fall back to PSA backends
- ✨(OIDC Provider) relay RP-Initiated logout confirmation to the frontend

[unreleased]: https://github.com/suitenumerique/accounts/compare/main
