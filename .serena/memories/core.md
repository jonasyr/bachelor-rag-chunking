# bachelor-rag-chunking — Core

## Identity
Bachelor's thesis (B.Sc. Informatik, IU Internationale Hochschule).  
Author: Jonas Weirauch (Matrikelnummer 10237021).  
Supervisor: Prof. Klaus Quibeldey-Cirkel.  
Submission deadline: **31.12.2026**. Work period: **July–December 2026**.

## Title
**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines Retrieval-Augmented-Generation-Systems für technische Projektdokumentation**

## Research Question
*How do different chunking strategies influence retrieval and answer quality of a RAG system when answering project-specific questions based on technical open-source documentation?*

## Goal in One Sentence
Design, implement, and evaluate a RAG pipeline on Vue.js documentation where **only the chunking strategy varies** — all other pipeline components held constant — to isolate chunking's effect and derive actionable recommendations.

## Repository State (as of June 2026)
Pre-implementation. Only `docs/` exists:
- `docs/Exposee.md` / `docs/Exposee.pdf` — approved thesis exposé
- `docs/Ground_Truth_Projektleitfaden.md` — **master reference document** (verbindlich); contains all binding decisions, full repo plan, data formats, evaluation rubric, timeline

## Sub-memories (read when relevant)
- Architecture, repo layout, data formats: `mem:pipeline`
- Three chunking strategies (C1/C2/C3) + parameters: `mem:chunking`
- Research hypotheses H1–H3, literature, research gap: `mem:research`
- Evaluation metrics, rubric, triangulation: `mem:evaluation`
- Binding decision log D1–D18: `mem:decisions`
- Tech stack and tool versions: `mem:tech_stack`
- Code style, naming, file conventions: `mem:conventions`
- Commands to run: `mem:suggested_commands`
- When a coding task is complete: `mem:task_completion`

## Priority Rule (conflicts)
1. Finales Exposé + later chat clarifications (highest)
2. Confirmed decisions from chat
3. `docs/Ground_Truth_Projektleitfaden.md` baseline
4. General best practices
