# auth-upload Specification

## Purpose
Provide a secure, class-scoped foundation for teacher and student accounts, teaching-material uploads, and knowledge-base ingestion, with a reproducible container deployment.

## Requirements

### Requirement: login and role authorization

The system MUST authenticate seeded teacher and student users with hashed passwords. Unauthenticated requests to protected routes MUST redirect to `/login`. Student upload requests MUST return 403.

#### Scenario: unauthenticated access

- **WHEN** a client requests `/materials` without a session
- **THEN** the server returns a redirect to `/login`

#### Scenario: student cannot upload

- **WHEN** `student_a1` posts a valid material to `/materials/upload`
- **THEN** the server returns 403 and creates no material or knowledge entry

### Requirement: class isolation

The system MUST derive the class scope from the server-side session and MUST NOT trust a client-provided `class_id`. A user MUST NOT read or download another class's material or content.

#### Scenario: cross-class material is rejected

- **WHEN** `student_a1` requests a material belonging to class B
- **THEN** the server returns 404 and does not include the material title or content

### Requirement: class-scoped material download

Authenticated teachers and students MUST be able to download the original file for materials in their own class. The server MUST determine class scope from the authenticated session, serve the stored file as an attachment using its display filename, and return 404 without file bytes for cross-class or missing materials.

#### Scenario: same-class user downloads original material

- **WHEN** an authenticated teacher or student requests a material download in their own class
- **THEN** the server returns the original uploaded bytes as an attachment with the display filename

#### Scenario: cross-class download is rejected

- **WHEN** a user requests a download for a material belonging to another class
- **THEN** the server returns 404 and does not return the file bytes

### Requirement: material upload and knowledge ingestion

Teachers MUST be able to upload non-empty UTF-8, UTF-16-with-BOM, or GB18030 `.txt` or `.md` text files no larger than the configured 5 MiB request limit. The interface MUST clearly state the supported types and size limit. The server MUST reject other extensions, recognized binary formats, and payloads that are not readable plain text. A successful upload MUST create one material record and one class-scoped knowledge entry in the same transaction. If the display filename already exists in the class, the server MUST append an increasing suffix such as `(1)` or `(2)` before the extension, and MUST preserve the bytes of every earlier upload.

#### Scenario: teacher uploads material

- **WHEN** `teacher_a` uploads a non-empty valid Markdown text file
- **THEN** class A's material list contains its title and the knowledge table contains its decoded text

#### Scenario: unsupported or disguised binary file is rejected

- **WHEN** a teacher uploads a non-text extension or renames a recognized binary file to `.txt` or `.md`
- **THEN** the server returns 400 and creates no material or knowledge entry

#### Scenario: duplicate filename receives an ordered suffix

- **WHEN** a teacher uploads a file whose name already exists in the same class
- **THEN** the new display filename receives the next numeric suffix before the extension and the earlier stored file remains unchanged

### Requirement: reproducible deployment

The application MUST provide `GET /health` without login and a Compose configuration with persistent `data/` and `uploads/` mounts.

#### Scenario: health check

- **WHEN** a client requests `/health`
- **THEN** the server returns HTTP 200 JSON with status `ok`
