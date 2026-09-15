# Google Maps Credential Registry

This file records approved credential references only.
Raw API keys and private credentials MUST NOT be stored in this repository.

## Google Cloud Project

- Project: `easyfind-automations`

## Current EFPS Maps API Key

- Display name: `Google Maps Key`
- Resource UID: `2334a827-466f-4a7a-8962-68c2afa29e34`
- AWS Secrets Manager secret: `efps-google-maps-api-key`
- AWS region: `us-east-1`
- Local macOS Keychain account: `efps`
- Local macOS Keychain service: `efps-google-maps-api-key`
- Environment override: `GOOGLE_MAPS_API_KEY`
- API restriction: `geocoding-backend.googleapis.com`

## Existing Maps Platform API Key

- Display name: `Maps Platform API Key`
- Resource UID: `7e4a67f6-2333-4d9d-80ed-8c29c89f8404`
- Known API target: `geocoding-backend.googleapis.com`
- Secret storage mapping: NOT VERIFIED
- Raw key value: NOT STORED IN REPOSITORY

## Credential policy

Priority:

1. Explicit constructor API key
2. `GOOGLE_MAPS_API_KEY`
3. Approved local Keychain credential

Never commit API keys, service-account private keys, or other credentials.
