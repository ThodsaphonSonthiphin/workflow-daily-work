# The live read is an explicit read-only request on the row, never a loaded skill that carries write steps

```mermaid
flowchart TD
    Q{how is 'the exact read-only query' on an open row written?} -->|chosen| A["as the request itself - for a Dataverse option set the
    metadata GET on EntityDefinitions/Attributes with
    $expand=OptionSet, a SELECT, a REST GET - so the
    worked example is copyable and nothing but a read is
    in front of the agent"]
    Q -->|rejected| B["name a skill to load (dataverse:dv-metadata) - that
    skill opens with solution and publisher creation steps
    (client.records.create); loading it inside the one
    phase that must stay read-only (ADR 0263) puts write
    steps on screen, and the name is a third-party plugin
    that the other supported harness may not have"]
```

Ruled 2026-10-29 at the final whole-branch review, which read `dv-metadata/SKILL.md:1-39` and
found it titled "Metadata - Making Changes". The spec (§4.3) and `SKILL.md` phase 3 named it
as the example; the worked block in `why-file-template.md` wrote `dv-metadata: … option set`
on the Source line, which is a description, not the query the template's own rule requires.
Both now carry the GET:

```
GET <org>/api/data/v9.2/EntityDefinitions(LogicalName='mgw_telephoneenquiry')/Attributes(LogicalName='mgw_loggingstatus')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$expand=OptionSet($select=Options)
```
