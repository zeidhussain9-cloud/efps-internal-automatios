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
- connection/error handling suitable for calling modules

Business meaning, field ownership, validation, duplicate rules, and decisions about when to read or write remain with the owning module.

## Implementation

`client.py` provides credential loading plus spreadsheet, worksheet, range-read, range-write, and row-append primitives. Tests inject a fake client so validation does not require Google network access.

## Credentials

Credentials must never be committed. The current implementation accepts `GOOGLE_SERVICE_ACCOUNT_JSON` or `GOOGLE_APPLICATION_CREDENTIALS` at runtime. Secret values stay outside the repository.
