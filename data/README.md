# Data handling notes

- `data/sample/` — **synthetic sample inputs only**, safe to commit. Populated in Stage 2 together with the data dictionary (which will be added to this file).
- Real or confidential business data must **not** be committed. Put it in `data/raw/` or `data/private/` (both git-ignored) and point `DATA_DIR` at it if needed.
- Generated artifacts (Chroma vector store, logs) live in `var/` (git-ignored).
