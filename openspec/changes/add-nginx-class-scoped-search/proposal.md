# Proposal: add NGINX entry and class-scoped knowledge search

Keep Flask and SQLite for the current low-cost deployment, put NGINX in front of the API, and add a retrieval endpoint that derives the class scope from the authenticated session.

This change does not introduce MySQL, a vector database, semantic embeddings, or AI answers.
