# sa-doc professional profile

Additions to the core template for a work-deliverable SDD:

- After **7. Data model**: **Security design** — table from `security`
  (concern → control), REQUIRED non-empty (validator E8). Must state how
  credentials are stored (hashing) and how payment data is handled
  (gateway-delegated vs stored) whenever the model touches either topic.
- After **8. Architecture**: **Deployment view** — from
  `architecture.deployment`, expanded to environments and one `graph TD`.
- At the end, before the traceability matrix: **Test-case seed** — one table
  row per use case main flow and per extension (id `TC-<uc>-<n>`, steps
  summary, expected result). Close the section with a pointer: for the full
  evidence-grounded suite, run the `generating-test-cases` skill from this
  plugin.

Everything else follows the core template unchanged.
