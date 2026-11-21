# learn-the-business asks first, and reveals business, then technical, then ADR, then thinking

```mermaid
flowchart TD
    Q{"who asks, and in what order<br/>does the answer come?"} -->|chosen| A["the skill asks one business question, the person<br/>answers first, then the reveal card: business reason,<br/>the technical choice it leads to, the ADR text<br/>that decided it, the thinking trick"]
    Q -->|rejected| B["the person asks and the skill answers - they learn<br/>only what they thought to ask, and it is<br/>feynman-explain with one more rule"]
    Q -->|rejected| C["both entries - the description's triggers blur<br/>into feynman-explain for any 'why do we do X'"]
    Q -->|rejected| D["technical first, business last - the order the<br/>code already gives; the business reason is then<br/>read as a footnote"]
```

Ruled 2026-11-21 by the user. Answering before the reveal is what makes the thinking lesson
hold: the person sees where their own reasoning left the method. The card's order is the
user's own wording - business as the lead, then the link to the technical side "ว่าทำไมต้อง
ทำแบบนั้น ประกอบกับข้อความใน adr". A part with no ADR says so on the ADR line.
