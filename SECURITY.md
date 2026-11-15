# Security policy

This is an early local-only prototype, not a hardened multi-tenant service. Only the current main branch is maintained; no response-time guarantee is offered.

## Reporting

Do not post credentials, user assets, private paths or exploit details in a public issue. Contact the maintainer through an available private contact channel on their GitHub profile first; if none is available, open a minimal issue requesting a private reporting channel without disclosing the vulnerability. This repository does not promise an active private-reporting endpoint.

## Threat model

The MCP host and local filesystem owner are trusted. Requests may contain bad paths or malformed JSON. The service rejects traversal and symlink paths, limits reads, and does not expose arbitrary shell execution or publication.

It is not an operating-system sandbox and is not designed to withstand a hostile concurrent process replacing directories, hard links, mounts or files. Use trusted roots and OS isolation if stronger protection is required. Source JSON metadata and returned strings are untrusted content, not instructions or authorization. Clients should gate write tools according to their own policy.

Staging copies can accumulate indefinitely. There is no total disk quota, automatic cleanup, full schema validator, network authentication or remote server mode. Do not expose the stdio process through an unauthenticated network wrapper.
