# Proposal: safer and clearer material uploads

## Why

Teachers need clear file-type guidance, unsupported or renamed binary files must not be treated as teaching text, and repeated uploads must not overwrite earlier files.

## What Changes

- Explicitly state in the upload interface that only TXT and Markdown files are accepted.
- Validate the extension and readable text content on the server.
- When a filename already exists in the same class, append an increasing suffix such as `(1)` or `(2)` before its extension.
- Store each uploaded file under a unique internal storage name so earlier uploads are preserved.

## Non-goals

- Adding PDF, Word, spreadsheet, image, or other document parsers.
- Adding malware scanning, OCR, vector indexing, or semantic retrieval.
- Changing the existing class and teacher permissions.
