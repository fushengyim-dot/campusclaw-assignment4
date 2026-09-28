# Design

- The browser's `accept` attribute and nearby help text guide selection; they are not treated as security controls.
- The server remains authoritative: allow `.txt` and `.md` only, reject known binary signatures and non-text/control-heavy payloads, and decode common UTF-8, UTF-16-with-BOM, or GB18030 text.
- Resolve duplicate display names inside the current class using `(1)`, `(2)`, and so on before the extension. Use a UUID-based internal storage name, independent of the display name.
- Start an immediate SQLite write transaction before checking class-local name collisions. Write the unique file and the material/knowledge rows together; on failure roll back and remove only the new unique file.
- Keep the existing 5 MiB request cap and teacher-only route.
