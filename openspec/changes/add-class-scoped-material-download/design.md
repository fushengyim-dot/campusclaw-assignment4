# Design: Class-scoped material download

## Decision
Add `GET /materials/<id>/download`, protected by the existing login guard. Resolve the material with both its ID and the authenticated session's `class_id`; return 404 when no matching row exists. Serve the stored file using its server-generated `storage_name` through Flask's safe directory-serving helper, and set the original display filename as the attachment name.

## Security
- Never accept a path or class ID from the download request.
- Keep the stored random filename as the filesystem lookup key.
- Keep the display filename only as the browser's suggested download name.
- Same-class students and teachers share read/download permission; uploads remain teacher-only.

## Failure behavior
Unauthenticated users are redirected to login. Missing, cross-class, or absent-on-disk materials do not expose file bytes; missing database records return 404 and missing files are safely returned as 404 by the file-serving helper.
