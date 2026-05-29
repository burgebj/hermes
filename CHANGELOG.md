# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changes

- plugins/honcho: Strip version path suffix (e.g. `/v3`) from `base_url` before passing to Honcho SDK constructor for local/self-hosted instances to prevent double-prefixing (e.g. `/v3/v3/workspaces`) that causes 404 errors (#20688)
