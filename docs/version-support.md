# Graph API version support

| Adapter | Status | Notes |
| ------- | ------ | ----- |
| v19.0 | supported | Legacy baseline; preserved wrapper even after Meta EOL. |
| v20.0 | supported | Intermediate migration baseline between v19.0 and v26.0. |
| v26.0 | supported (latest) | Current pinned adapter; `latest` resolves here. |
| others (v21.0+) | planned | Added behind isolated adapters with contract fixtures. |

Rules: `latest` is a code pin (`LATEST_VERSION`), never a network lookup. Pinned versions are
never silently upgraded; SDK-deprecated versions warn. "Adapter exists" != "Meta still serves it".
Every adapter gets success + failure fixtures per resource family plus cross-version serialization tests.
