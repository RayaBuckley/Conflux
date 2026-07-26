"""Provider adapters.

Layer: outer adapter boundary. This package translates filesystem, Docker, and
future provider resources into canonical ``conflux.core`` values. Providers
must not define Principal Context or bypass ITES authorisation.

See ``docs/ARCHITECTURE.md`` and ``docs/AUDIT.md`` for ownership and contracts.
"""
