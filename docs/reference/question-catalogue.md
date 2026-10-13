# Fragenkatalog (Ground Truth)

> Seitentyp: Nachschlagen (reference). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).


**Umfang:** ca. 40 Fragen (Minimum 30, optimal 40–50, nicht über 60). Der Fragenkatalog ist eine der wichtigsten Eigenleistungen und dauert länger als gedacht — früh beginnen.

**Fragetypen und Beispiele (Vue.js, englisch):**

| Typ | Anzahl | Beispiel |
|-----|------:|----------|
| Faktisch | 10 | Which lifecycle hooks are available in the Composition API? |
| Prozedural | 10 | How do you define props in a component using `<script setup>`? |
| Konzeptuell | 10 | What is a composable in Vue and what problem does it solve? |
| Vergleichend | 5 | What is the difference between the Options API and the Composition API? |
| Einschränkung/Fehler | 5 | What happens if a child component mutates a prop directly? |

**Ground-Truth-Felder pro Frage:** `question_id`, `question`, `question_type`, `expected_answer`, `relevant_doc_ids`, `relevant_section_ids`, `difficulty`, `notes`.

> **Wichtig:** Referenzantworten und relevante Quellen müssen **vor** der Evaluation feststehen, um nachträgliche, ergebnisorientierte Anpassungen auszuschließen.
