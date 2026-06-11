# Studying a Dynamics 365 / Dataverse Org — Step-by-Step Method

> A read-only methodology for learning the business logic of an existing Dynamics 365
> CRM environment (custom + standard entities, JS / React web resources, workflows,
> plugins, flows, ribbon/commands) and producing a single architecture document.
> All commands and queries below were verified against official Microsoft Learn docs
> (June 2026). Designed to be turned into a Claude skill: Steps 1–7 are scriptable
> extraction; Steps 8–9 are analysis instructions; Step 10 is the deliverable template.

**Core idea:** a live CRM org is unreadable, but nearly everything in it can be pulled
to disk as plain text. Extract first, then study it like a legacy codebase
(per the `drive-to-legacy` 6-phase method), then document.

**Three stages: Extract → Study → Document. Everything is read-only — safe on any org,
but prefer the SANDBOX environment anyway.**

---

## Step 0 — Tooling (one-time)

```powershell
dotnet tool install --global Microsoft.PowerApps.CLI.Tool
pac auth create --environment "https://yourorg.crm.dynamics.com"
pac org who     # verify you are pointed at the right org (SANDBOX!)
```

Environment URL: make.powerapps.com → gear icon → Session details → Instance URL.

For scripted Web API calls, get a token the same way the `dataverse:dv-connect`
skill does (Python + `azure-identity`), or use an authenticated browser session
for one-off GETs. All `GET /api/data/v9.2/...` URLs below are relative to the
environment URL.

---

## Step 1 — Pull the org to disk as readable files

```powershell
pac solution list                       # find the unmanaged solution(s) — publisher prefix is the giveaway
pac solution export --name <SolutionUniqueName> --path .\export\Sol.zip --overwrite
pac solution unpack --zipfile .\export\Sol.zip --folder .\src --allowWrite --allowDelete --clobber
```

| On disk after unpack (XML format) | Contents |
|---|---|
| `WebResources\` | Every JS/HTML/React web resource as a real file |
| `Controls\<Namespace.Name>\` | PCF code components: `ControlManifest.xml` + `bundle.js` |
| `Other\Customizations.xml` | Entities, attributes, FormXml, views, **RibbonDiffXml**, option sets, sitemap |
| `PluginAssemblies\` | Plugin DLLs (registrations readable; source is compiled) |
| Workflow files | Classic workflows / business rules / BPFs as XAML |
| `AppModule*` files | Model-driven app definition + **AppModuleSiteMap** (the left menu) |

Caveats (docs-verified):
- **Cloud flows and canvas apps are NOT decomposed by the XML unpack.** Use
  `pac solution clone --name <X> --outputDirectory .\src-yaml` — its YAML layout has
  `modernflows/` (readable flow JSON) and `canvasapps/` (.msapp, needed for Power Fx
  commands, Step 6).
- Customizations living only in the **Default Solution** must be added to an
  exportable unmanaged solution first (maker portal → Solutions → New → Add existing).
- `git init` the folder. Re-export + re-unpack later diffs cleanly — this is the
  documented source-control workflow.

---

## Step 2 — Build the entity universe (ALL business entities, not just custom)

Union four sources; annotate each entity with where it came from.

**Source 1 — App components (the superset users can reach).**
```
GET /api/data/v9.2/appmodules?$select=name,uniquename,appmoduleid,appmoduleidunique
GET /api/data/v9.0/RetrieveAppComponents(AppModuleId=<appmoduleid>)
```
Rows with `componenttype eq 1` are the app's tables; resolve each `objectid` via
`EntityDefinitions(<objectid>)?$select=LogicalName,DisplayName`.
Gotcha: filtering `appmodulecomponents` directly uses `_appmoduleidunique_value`
(the app's `appmoduleidunique`, **not** `appmoduleid`) — wrong GUID returns zero rows silently.

**Source 2 — The SiteMap (the left menu = navigation subset + business taxonomy).**
Parse `AppModuleSiteMap` from the unpack (or `GET /sitemaps?$select=sitemapname,isappaware,sitemapxml`).
`<Area>/<Group>/<SubArea Entity="...">` → each `Entity=` attribute is a table users
navigate to; the Group names (e.g. *Cargo Management, Operations, Relationships,
Quotes, Administration*) become the documentation chapters. An "Administration"-style
group marks the master/reference tables (ERD dimension tables).

**Source 3 — Standard tables the business customized.**
```
GET /api/data/v9.2/EntityDefinitions?$select=LogicalName&$filter=IsCustomEntity eq false&$expand=Attributes($select=LogicalName,IsManaged;$filter=IsCustomAttribute eq true)
```
Drop entities whose `Attributes` array is empty (must be client-side — no lambda
operators on metadata queries). `IsManaged` + publisher prefix separates the org's
own columns from installed ISV columns.

**Source 4 — Tables with data / actual usage.**
```
GET /api/data/v9.2/RetrieveTotalRecordCount(EntityNames=@p1)?@p1=["account","contact","quote",...]
```
Counts are a snapshot up to 24h old — confirm "empty" with a `$top=1` probe.
Cross-check with Power Platform admin center → Dataverse analytics →
**Most Used OOB / Custom Entities** (API-call volume, the closest to ground truth).

Noise filter for any standard-entity listing:
`IsIntersect eq false and IsPrivate eq false and IsValidForAdvancedFind eq true`.

Finally **expand outward**: from each entity, follow lookups (Step 3 relationships)
to catch child/line entities that never appear in navigation.

---

## Step 3 — Data model detail (ERD + data dictionary)

For every entity in the Step-2 universe:
```
GET /api/data/v9.2/EntityDefinitions(LogicalName='<table>')?$expand=Attributes($select=LogicalName,AttributeType,RequiredLevel)
GET /api/data/v9.2/RelationshipDefinitions/Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata?$select=SchemaName,ReferencedEntity,ReferencingEntity,ReferencingAttribute&$filter=ReferencedEntity eq '<table>'
GET /api/data/v9.2/EntityDefinitions(LogicalName='<table>')/Attributes/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$select=LogicalName&$expand=OptionSet,GlobalOptionSet
```
- Repeat the cast query per enum type (MultiSelectPicklist, State, Status, Boolean) —
  casting to the abstract `EnumAttributeMetadata` is not allowed.
- Exactly one of `OptionSet`/`GlobalOptionSet` is non-null — that's how you tell
  local vs global choices.
- Always trim with `$select` + `&LabelLanguages=1033` — metadata queries have no paging.

Deliverables: mermaid `erDiagram` (1:N edges from `ReferencingEntity/Attribute`),
data dictionary table, and **every option-set value with its label** — the labels are
the business vocabulary (statuses, categories, types).

---

## Step 4 — Server-side automation inventory

All process automation is rows in the `workflow` table, split by `category`:
`0` classic workflow · `2` business rule · `3` action · `4` business process flow ·
`5` cloud flow (`6` desktop flow, `7` AI flow exist too).

```
GET /api/data/v9.2/workflows?$filter=type eq 1 and statecode eq 1&$select=name,category,primaryentity,mode,scope,triggeroncreate,triggerondelete,triggeronupdateattributelist,createstage,updatestage&$orderby=category
```
- `type eq 1` (Definition) avoids double-counting Activation rows.
- Definition body: `xaml` column (classic/rules/BPF) or `clientdata` JSON (cloud flows).
- Business rule scope matters: scope *Entity* runs server-side (generated plugin);
  *All Forms* / specific form is client-side only — record the scope.
- "My Flows" outside solutions are NOT reliably in this table — cross-check the
  Power Automate portal.

Plugins (+ webhooks) are registration rows:
```
GET /api/data/v9.2/sdkmessageprocessingsteps?$select=name,stage,mode,rank,filteringattributes,statecode&$expand=sdkmessageid($select=name),sdkmessagefilterid($select=primaryobjecttypecode),plugintypeid($select=friendlyname)
GET /api/data/v9.2/plugintypes?$select=friendlyname&$expand=pluginassemblyid($select=name)
```
Stage: 10 pre-validation, 20 pre-operation, 40 post-operation; mode 0 sync / 1 async
(capture both — they define rollback semantics). Steps whose event handler is a
`serviceendpoint` are webhooks/Service Bus, not code plugins. Filter out
`ishidden`/Microsoft-managed steps.

Per automation, record one line: **trigger → what it does → why the business needs it.**

---

## Step 5 — Client-side logic map (forms, JS, React)

1. **Form → event → function map.** Pull form XML:
   `GET /systemforms?$select=name,objecttypecode,type,formxml&$filter=formactivationstate eq 1`
   Parse `<formLibraries><Library name>` and
   `<event name|attribute><Handlers><Handler libraryName functionName>`.
   OnChange events carry the column in the event's `attribute`. `<InternalHandlers>`
   are compiled business rules — include but label separately.
2. **Web resources** are already on disk (Step 1); or dump via
   `GET /webresourceset?$select=name,content&$filter=webresourcetype eq 3`
   (content is Base64; type 1 = HTML, 3 = JS). Single file:
   `<EnvURL>/WebResources/<name>` in an authenticated browser.
3. **React — determine which kind:**
   - **PCF control** → `Controls\` folder / `GET /customcontrols?$select=name,version,manifest`.
     `control-type="virtual"` = platform-React; `<uses-feature name="WebAPI">` = proof
     it talks to Dataverse.
   - **HTML web resource hosting a React bundle** → `WebResources\`, grouped by
     folder-style names (`prefix_/app/...`). Note: JS-to-JS references are NOT
     tracked as dependencies — group by name prefix, not dependency queries.
4. **Minified bundles** (no source repo): the entity names and queries survive
   minification —
   `rg 'Xrm\.WebApi|webAPI\.retrieveMultipleRecords|\$select=|\$filter=|/api/data/v9|<fetch|GetGlobalContext' bundle.js`
   Every hit names a table the app reads/writes = its business function.
5. **Runtime cross-check:** in-app **Monitor → FormEvents** lists every handler that
   actually fires (catches `addOnLoad`/`addOnChange` registered in code, which
   FormXml misses).

---

## Step 6 — Command bar / ribbon (BOTH generations)

Two coexisting systems; a full inventory needs both.

**A. Classic — RibbonDiffXml.** Lives in 3 places in `customizations.xml`:
1. Per-entity: `Entities/Entity/RibbonDiffXml` (already in the Step-1 export).
2. **Application ribbon** (global / all-tables, uses `{!EntityLogicalName}` token):
   the ROOT `ImportExportXml/RibbonDiffXml` node — exported **only if** you add the
   *Application Ribbons* client-extension component to a solution before exporting.
3. Per-form (legacy; not supported on Unified Interface — usually ignorable).

Anatomy → mapping table:
`<CustomAction Id Location>` (the Location/Id encodes the bar:
`Mscrm.Form.<entity>.*` = form, `Mscrm.HomepageGrid.<entity>.*` = main grid,
`Mscrm.SubGrid.<entity>.*` = subgrid) → button's `Command` →
`<CommandDefinition>` → `<Actions>`: `JavaScriptFunction Library="$webresource:x" FunctionName`
or `Url Address` → plus `<EnableRules>/<DisplayRules>` (ValueRule, SelectionCountRule,
FormStateRule, RecordPrivilegeRule, CustomRule = JS returning bool/Promise…).
`<HideCustomAction>` removes built-in buttons. Note: on the modern command bar,
commands failing EnableRules are **hidden, not greyed**.

Effective runtime ribbon (merged, per table):
```
GET /api/data/v9.2/RetrieveEntityRibbon(EntityName='<table>',RibbonLocationFilter=Microsoft.Dynamics.CRM.RibbonLocationFilters'All')
GET /api/data/v9.2/RetrieveApplicationRibbon
```
Response is Base64 → **a zip** → extract the `RibbonXml.xml` part (any zip reader).
Diff against Microsoft's published defaults (`ExportedRibbonXml.zip`) to isolate
customizations.

**B. Modern — command designer.** Each modern command is a row in `appaction`:
```
GET /api/data/v9.2/appactions?$select=name,buttonlabeltext,location,context,contextvalue,sequence,type,hidden,isdisabled,origin,onclickeventtype,onclickeventformulacomponentname,onclickeventformulafunctionname,onclickeventjavascriptfunctionname,visibilitytype&$expand=AppModuleId($select=uniquename),ContextEntity($select=logicalname),OnClickEventJavaScriptWebResourceId($select=name)
```
- `location`: 0 Form, 1 Main Grid, 2 Sub Grid, 3 Associated Grid, 5 Global Header…
- `onclickeventtype`: **1 = Power Fx**, **2 = JavaScript** (one web resource + one
  function only).
- **Power Fx expressions are NOT in the row** — they live in the app's
  **command component library** (a canvas app). Get its `.msapp`
  (`pac canvas download`, or `canvasapps/` in the YAML clone) — it's a zip; the
  source is `Src\*.pa.yaml` (`pac canvas unpack --msapp <file> --sources <dir>`).
- `origin` records classic→modern migration; migrated classic visibility rules hang
  off the `appactionrule` M:M relation.

**C. Runtime ground truth — Command Checker.** Append `&ribbondebug=true` to the app
URL → a Command Checker button appears on each command bar → lists every command
(hidden ones in italics), each rule's True/False/Skipped evaluation, and solution
layers. Use it to verify the static A+B map matches reality (classic/modern merge
precedence is not fully documented — Command Checker is the authority).

Deliverable: one table — Bar (entity+location) | Button | Generation | What runs
(JS `file.function` / Power Fx `component.function` / URL) | When shown (rules) | Why.

---

## Step 7 — Security model (= the personas)

```
GET /api/data/v9.2/roles?$select=name
GET /api/data/v9.2/roles(<id>)/roleprivileges_association?$select=name      # names only; depth via RetrieveRolePrivilegesRole
GET /api/data/v9.2/businessunits?$select=name,_parentbusinessunitid_value
GET /api/data/v9.2/fieldsecurityprofiles?$select=name&$expand=lk_fieldpermission_fieldsecurityprofileid($select=entityname,attributelogicalname,canread,canupdate)
GET /api/data/v9.0/appmodules(<appmoduleid>)?$expand=appmoduleroles_association&$select=name   # which roles can use the app
```
Custom security roles ≈ business personas — they seed the user stories.
Note: team-granted privileges need `RetrieveUsersPrivilegesThroughTeams` if you
document *effective* access.

---

## Step 8 — Analytics layer (embedded Power BI)

If the app's Dashboards area embeds Power BI (an "Open in Power BI" button is the
giveaway), the analytics logic lives in a Power BI semantic model **outside** the
solution export. Document: which reports/dashboards are embedded, which dataset each
reads, and which Dataverse tables feed it (confirms business-critical entities).
Use the `pbi-cli` skills (`power-bi-docs` auto-documents the model).

---

## Step 9 — Trace business processes end-to-end (the actual learning)

For each key entity, connect the layers into a lifecycle:

> Who creates it (role) → which form + JS validates/cascades (Step 5) → which
> command-bar actions exist (Step 6) → which plugin/workflow/flow fires on save
> (Step 4) → what status transitions exist (statuscode labels, Step 3) → what
> downstream records appear.

Read the extracted files AND walk the app as admin (create a test record in SANDBOX,
watch auto-population, check audit history, use Monitor). Write each flow as a user
story + mermaid `sequenceDiagram`.

---

## Step 10 — Write the document

One `ARCHITECTURE.md`, in this reading order (drive-to-legacy structure):

1. **User stories** (per persona/security role, with sequence diagrams)
2. **Overview** — apps, solutions, tech stack, component map
3. **Data model** — ERD, data dictionary, option-set values (business vocabulary)
4. **Business logic and rules** — per layer (JS / business rule / plugin / flow),
   validation, cascades, auto-population, with flowcharts
5. **Automation inventory** — every workflow/plugin/flow: trigger, behavior, and a
   **Why row** (what breaks without it) — non-negotiable
6. **Client-side map** — form → event → function table; React components and the
   tables they touch
7. **Command bar map** — the Step-6 table
8. **Security model** — roles, BU tree, field security
9. **Analytics** — embedded Power BI inventory

Rules: clickable TOC, mermaid everywhere, every API/automation entry has a Why,
no speculation — unclear behavior is marked unclear.

---

## Appendix — Turning this into a Claude skill

- **Scriptable (Steps 1–7):** Python scripts (per `dataverse` plugin conventions:
  SDK first, raw Web API only where listed) — `export_solution.ps1`,
  `dump_entities.py`, `dump_automation.py`, `dump_forms_js.py`, `dump_ribbon.py`,
  `dump_security.py`. Each emits JSON/markdown fragments into a workdir.
- **Skill instructions (Steps 8–10):** how Claude analyzes the extracted files,
  traces lifecycles, and assembles ARCHITECTURE.md from the fragments.
- **Safety:** read-only by design; still confirm the target environment URL with the
  user before the first call (multi-environment rule), and prefer SANDBOX.
- Existing building blocks: `dataverse:dv-connect` (Step 0), `drive-to-legacy`
  (Steps 9–10 method), `power-bi-docs` (Step 8).
