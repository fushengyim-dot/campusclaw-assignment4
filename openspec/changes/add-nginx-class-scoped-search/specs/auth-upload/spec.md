## ADDED Requirements

### Requirement: NGINX is the host entrypoint

The Compose deployment MUST expose the web entrypoint through NGINX and MUST NOT publish the Flask API service directly to the host. NGINX MUST proxy the application pages, health endpoint, and `/api/` routes to the internal API service.

#### Scenario: health is reachable through NGINX

- **WHEN** a client requests `/health` from the published web port
- **THEN** NGINX proxies the request to the internal API and returns HTTP 200 when the API is healthy

#### Scenario: API has no host port mapping

- **WHEN** the Compose services are inspected
- **THEN** the API service has no published host port and is reachable only through the Compose network

### Requirement: class-scoped knowledge search API

Authenticated users MUST be able to search stored knowledge through `GET /api/knowledge/search?q=...`. The server MUST derive the class scope from the authenticated session, filter both knowledge and material records by that scope, and return source metadata including material ID, title, and filename. The current implementation MAY use bounded SQLite text matching and MUST NOT claim semantic vector retrieval.

#### Scenario: authenticated user receives same-class search results

- **WHEN** an authenticated user searches for text present in a material from their class
- **THEN** the server returns HTTP 200 with matching results and source metadata

#### Scenario: unauthenticated search is rejected

- **WHEN** a client searches without a valid login session
- **THEN** the server returns HTTP 401 and does not return knowledge content

#### Scenario: cross-class search results are excluded

- **WHEN** a user searches for text that exists only in another class
- **THEN** the server returns HTTP 200 with no result from that other class

### Requirement: browser knowledge search

The authenticated materials page MUST provide a keyword search form that calls the class-scoped knowledge search API and displays each result's material name, source filename, material ID, and returned text excerpt. The browser MUST not send a client-selected class identifier as an authorization parameter.

#### Scenario: user searches from the materials page

- **WHEN** an authenticated user enters a keyword and submits the search form
- **THEN** the page requests `/api/knowledge/search` and renders the returned source metadata and excerpt
