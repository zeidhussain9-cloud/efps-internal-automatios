# Google Sheets Shared Service

Provides the reusable technical capability for connecting to and operating Google Sheets.

## Responsibility

This shared layer owns technical access only:

- Google service-account credential loading
- authenticated Sheets client creation
- spreadsheet and worksheet access
- reading ranges
- writing ranges
- appending rows when explicitly requested by the caller
- clearing/updating ranges when explicitly requested by the caller
- connection/error handling suitable for calling modules

Business meaning, field ownership, validation, duplicate rules, and decisions about when to read or write remain with the owning module.

## Credentials

Credentials must never be committed. Supported runtime configuration must be established by the implementation and documented without storing secret values in the repository.

## Implementation state

This folder is a shared integration boundary. Concrete code should be added here only for verified Google Sheets capabilities required by EFPS modules.
