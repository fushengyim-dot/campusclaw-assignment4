# Add class-scoped material download

## Why
Teachers and students need to retrieve the original uploaded teaching material, while preserving the existing class-isolation boundary.

## What Changes
- Add an authenticated download route for the original uploaded file.
- Allow same-class teachers and students to view and download materials.
- Return 404 for cross-class detail and download requests.
- Show a download action on each material detail page.

## Capabilities
- Modified: `auth-upload`

## Impact
- Flask routes and material detail template.
- Automated authorization and byte-preservation tests.
