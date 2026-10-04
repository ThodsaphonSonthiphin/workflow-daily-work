# The architecture-document skill draws its UML views in Mermaid — the Diagram convention does not change

```mermaid
flowchart TD
    Q{the owner asked for UML, and the Diagram convention is<br/>the Mermaid family, not strict UML: which notation<br/>does the architecture document use?} -->|chosen| A["Mermaid, inside the Markdown document — the
    Diagram convention as it stands; each diagram is
    named by its UML view (deployment view, component
    view, sequence diagram), and the picture shows
    when the document is read on GitHub"]
    Q -->|rejected| B["PlantUML — strict UML deployment and component
    diagrams, but GitHub shows only the code text, an
    image needs a PlantUML tool and Java, and the
    Diagram convention would have to change"]
    Q -->|rejected| C["Mermaid in the document plus PlantUML files
    beside it — every diagram then exists twice, and
    the two copies can come apart"]
```

The owner's request named UML. The glossary's **Diagram convention** entry says the
convention is the Mermaid family and warns against calling it a UML rule. Asked
2026-10-03 which one this skill uses — with the example of a network team that opens the
document on GitHub to see which ports to open — the owner chose Mermaid.

So "UML" in this skill names the *view*, not the notation: deployment view, component
view, sequence diagram. The deployment view is boxes for zones and servers, with one
arrow per connection that carries its port. Mermaid has no strict UML deployment or
component diagram, and that is accepted. Which views the document carries is its own
decision.
