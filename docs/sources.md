# Sources and provenance

All sources are public and retrieved live by the pipeline.

| Source | Dataset ID | Resolver/API |
|---|---|---|
| CMS Hospital General Information | `xubh-q36u` | `https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u` |
| CMS Unplanned Hospital Visits | `632h-zaca` | `https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/632h-zaca` |
| CMS HCAHPS Hospital | `dgck-syfz` | `https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/dgck-syfz` |
| CDC PLACES County | `swc5-untb` | `https://data.cdc.gov/resource/swc5-untb.json` |

The live CMS resolver provides versioned CSV URLs and publication metadata. Exact URLs, retrieval UTC, release/modified fields, byte counts, raw rows, and SHA-256 hashes from this executed run are in `outputs/source_snapshot.csv` and the SQLite `source_snapshot` table. This is stronger provenance than hard-coding a transient download URL.

Publisher definitions and caveats govern interpretation. CDC PLACES measures are modeled estimates; CMS measure specifications define the score periods and populations. No extract is relabeled as longitudinal history.
