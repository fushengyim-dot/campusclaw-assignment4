## MODIFIED Requirements

### Requirement: class isolation

The system MUST derive the class scope from the server-side session and MUST NOT trust a client-provided `class_id`. A user MUST NOT read or download another class's material or content.

#### Scenario: cross-class material is rejected

- **WHEN** `student_a1` requests a material belonging to class B
- **THEN** the server returns 404 and does not include the material title or content

## ADDED Requirements

### Requirement: class-scoped material download

Authenticated teachers and students MUST be able to download the original file for materials in their own class. The server MUST determine class scope from the authenticated session, serve the stored file as an attachment using its display filename, and return 404 without file bytes for cross-class or missing materials.

#### Scenario: same-class user downloads original material

- **WHEN** an authenticated teacher or student requests a material download in their own class
- **THEN** the server returns the original uploaded bytes as an attachment with the display filename

#### Scenario: cross-class download is rejected

- **WHEN** a user requests a download for a material belonging to another class
- **THEN** the server returns 404 and does not return the file bytes
