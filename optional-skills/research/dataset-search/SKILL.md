---
name: dataset-search
description: Search and discover open datasets from HuggingFace Datasets. Filter by task, modality, size, language. Get dataset metadata (downloads, likes, tags, licenses). Free API, no key required.
platforms: [linux, macos, windows]
---

# Dataset Search

Search open datasets via HuggingFace Datasets API. **No API key required.**

## Helper script

This skill includes `scripts/dataset_search.py` — a complete CLI tool.

```bash
# Search by keyword
python3 SKILL_DIR/scripts/dataset_search.py search "chest xray"

# Filter by task
python3 SKILL_DIR/scripts/dataset_search.py search "text classification" --task text-classification

# Filter by modality
python3 SKILL_DIR/scripts/dataset_search.py search "image" --modality image

# Top datasets by likes
python3 SKILL_DIR/scripts/dataset_search.py popular --limit 10

# Get dataset details
python3 SKILL_DIR/scripts/dataset_search.py detail "keremberke/chest-xray-classification"
```

Commands: search, popular, detail. Output is structured JSON.