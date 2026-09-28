## ADDED Requirements

### Requirement: login and role authorization

The system MUST authenticate seeded teacher and student users with hashed passwords. Unauthenticated requests to protected routes MUST redirect to `/login`. Student upload requests MUST return 403.

#### Scenario: unauthenticated access

- **WHEN** a client requests `/materials` without a session
- **THEN** the server returns a redirect to `/login`

#### Scenario: student cannot upload

- **WHEN** `student_a1` posts a valid material to `/materials/upload`
- **THEN** the server returns 403 and creates no material or knowledge entry

### Requirement: class isolation

The system MUST derive the class scope from the server-side session and MUST NOT trust a client-provided `class_id`. A user MUST NOT read another class's material title or content.

#### Scenario: cross-class material is rejected

- **WHEN** `student_a1` requests a material belonging to class B
- **THEN** the server returns 404 and does not include the material title or content

### Requirement: material upload and knowledge ingestion

Teachers MUST be able to upload non-empty `.txt` or `.md` files. A successful upload MUST create one material record and one class-scoped knowledge entry in the same transaction.

#### Scenario: teacher uploads material

- **WHEN** `teacher_a` uploads a valid Markdown file
- **THEN** class A's material list contains the new title and the knowledge table contains its content

### Requirement: reproducible deployment

The application MUST provide `GET /health` without login and a Compose configuration with persistent `data/` and `uploads/` mounts.

#### Scenario: health check

- **WHEN** a client requests `/health`
- **THEN** the server returns HTTP 200 JSON with status `ok`
