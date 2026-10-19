# 0042. MDX-Umwandlung: eigene Anker, Agent-Prompts und Video-Karten bleiben

## Status

Angenommen (19.10.2026; ersetzt die Ankerregel von [ADR 0019](0019-korpus-ausschnitt.md); ergänzt [ADR 0038](0038-korpus-e2e.md))

## Kontext

- ADR 0019 benennt Abschnitte als `section_id = {doc_id}#{anchor}` aus den expliziten VitePress-Ankern (`{#…}`) der
  H2/H3-Überschriften, ohne eigene Slug-Erzeugung. Die e2e-Seiten (Mintlify-MDX) haben keine expliziten Anker; die
  Website bildet sie nach einer festen Regel aus dem Überschriftentext.
- Die Website hat für die H1 keinen Anker. Der Titel einer Seite kann mit einer Überschrift derselben Seite
  kollidieren: `reference/config` heißt `E2EConfig` und hat eine H3 gleichen Namens (`D041#e2econfig`).
- ADR 0038 sagt, bei der Bereinigung entfielen „nur Navigation, Videos und Einrichtungs-Prompts für Coding-Agenten“.
  Die Prompts (`<SetupPrompt>` mit `<Prompt>`) und die Video-Karten (`<VideoCard>`, Titel und Untertitel) sind aber
  Text, den eine Leserin oder ein Leser der Website sieht.
- Beim Bau der MDX-Umwandlung (Spezifikation
  [`2026-10-18-e2e-snapshot-design.md`](../superpowers/specs/2026-10-18-e2e-snapshot-design.md), Pull Request #22,
  18.10.2026) wurde als Ziel festgelegt, jeden auf der Website sichtbaren Text zu behalten; Jonas hat die Abweichung von
  ADR 0038 am 19.10.2026 bestätigt.

## Entscheidung

Wir werden die Anker der H2/H3-Überschriften selbst berechnen (`mdx.slug`), mit der Regel der Website: Linkziele und
Backticks entfernen, Kleinschreibung, jede Folge anderer Zeichen als `a-z0-9` durch `-` ersetzen, `-` an den Rändern
streichen; die Regel ist am 18.10.2026 an der Live-Seite geprüft und in `tests/test_mdx.py` festgehalten.
Wir werden der H1, die aus dem Titel im Frontmatter entsteht, als Anker den Slug des Seitenpfads ohne Endung geben
(`reference/config` → `reference-config`).
Wir werden die berechneten Anker als `{#…}` in den umgewandelten Text schreiben; `preprocess.py` liest sie wie in
ADR 0019, verlangt genau eine H1 und bricht bei doppelten Ankern einer Seite ab.
Wir werden Agent-Prompts als Zeile `**Agent prompt**` mit dem Prompt als ```` ```text ````-Block und Video-Karten als
Listenpunkt `- **Titel**: Untertitel` behalten; entfallen nur `import`-Zeilen, eingebettete Videos (`<video>`, die
Bildunterschrift bleibt) und alte Anker (`<a id>`, `<span id>`).
Alle Regeln: [Korpus](../reference/corpus.md#aufbereitung-mdx--markdown).

## Konsequenzen

- Positiv: `section_id` und die Relevanzregel bleiben wie in ADR 0019; die H2/H3-Anker stimmen mit der Website
  überein, jeder Abschnitt lässt sich dort nachschlagen.
- Positiv: Der Korpus enthält jeden sichtbaren Text; Agent-Prompts stehen auf 10 Seiten und gehören zum Retrieval wie
  jeder andere Abschnittstext.
- Negativ: Die Slug-Regel ist eigener Code, der der Website folgt; ein neuer Snapshot muss sie erneut an der Website
  prüfen.
- Neutral: Den H1-Anker gibt es auf der Website nicht; er dient nur der `section_id` des Seitenabschnitts.
