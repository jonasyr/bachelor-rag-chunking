# Korpus (Vue.js)

> Seitentyp: Nachschlagen (reference). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).

## Quelle und Struktur
- **Repository:** `vuejs/docs` (offizielle Vue-3-Dokumentation), Inhalte unter `src/`.
- **Relevante Bereiche (Vorschlag für die Begrenzung):**
  - `src/guide/essentials/` — Template-Syntax, Reaktivität, Computed, Lifecycle, Watcher, Komponenten-Grundlagen (faktische + prozedurale Fragen)
  - `src/guide/components/` — Props, Events, v-model, Slots, Provide/Inject (prozedurale + konzeptuelle Fragen)
  - `src/guide/reusability/` — Composables, Custom Directives, Plugins (konzeptuelle Fragen)
  - `src/guide/best-practices/` — Performance, Security, Accessibility (anspruchsvollere Fragen)
  - optional Teile von `src/api/` für Referenz-/Faktenfragen
- **Umfang:** bewusst begrenzt auf ca. **50–100 Markdown-Dateien/Seiten**. Ziel ist eine sauber kontrollierbare Datenbasis, nicht maximale Menge.

## Korpusmanifest (`corpus_manifest.csv`)
| file_id | path | title | section | tokens | included |
|---------|------|-------|---------|-------:|----------|
| D001 | guide/essentials/reactivity-fundamentals.md | Reactivity Fundamentals | Essentials | 1700 | yes |
| D002 | guide/components/props.md | Props | Components | 1500 | yes |
