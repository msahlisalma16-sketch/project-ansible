# AI Role, Limitations, and Controls

## What AI does in this project
- Optional diagnostic-only component: `generate_ai_review()` in `utils/xml_migration.py` uses `sentence-transformers` to compute similarity scores between placeholders and candidate values.
- Output: `mapping_ai_review.txt` — suggestions for manual review. It does not alter `vars.yaml` or rendering.

## Why AI is optional
- Determinism: core matching uses structural heuristics so outputs are predictable.
- Cost: `sentence-transformers` (and its dependencies like `torch`) are heavy; they increase CI resource usage.

## Limitations and risks
- Privacy: `v1`/`v5` XML can contain secrets; sending these strings to external models (or cloud-hosted models) risks leakage. This project uses local sentence-transformers, not cloud APIs, but be mindful of model downloads and caches.
- Determinism: AI scores are probabilistic; do not use them to make automated changes without human review.
- Dependency size: `sentence-transformers` can pull `torch` and other large packages; avoid installing on small CI agents unless needed.

## Controls and recommendations
- Default: do not install `sentence-transformers` in CI. Install locally only when you want an AI review.
- To run AI review manually:

```bash
python -m pip install sentence-transformers
python utils/xml_migration.py v1.xml v5.xml --ai-review mapping_ai_review.txt
```

- To disable AI in the script explicitly, add a CLI flag `--no-ai` (not currently implemented) or avoid installing the package.

## Audit and logging
- If AI outputs are sensitive, store `mapping_ai_review.txt` in protected storage or omit it from artifacts.
- Keep an audit trail when AI-based reviews influence manual decisions (who approved changes).
