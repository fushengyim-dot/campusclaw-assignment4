## MODIFIED Requirements

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
