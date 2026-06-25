Exposé

IU Internationale Hochschule

Studiengang: B.Sc. Informatik

Einfluss von Chunking-Strategien auf die Retrieval- und
Antwortqualität eines Retrieval-Augmented-Generation-Systems
für technische Projektdokumentation

Jonas Weirauch

Matrikelnummer: 10237021

Betreuer/in: Prof. Klaus Quibeldey-Cirkel

Abgabedatum: 31.12.2026

Inhaltsverzeichnis

Abkürzungsverzeichnis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

III

1 Einleitung . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

2 Theoretische Fundierung . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

2.1 Grundlagen von Retrieval-Augmented Generation . . . . . . . . . . . . . . . . . . . .

2.2 Chunking und Evaluation von RAG-Systemen . . . . . . . . . . . . . . . . . . . . . . .

3 Methodik / Forschungsdesign . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

4 Geplante Gliederung . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

5 Zeitplan . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

Literaturverzeichnis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

1

2

2

2

4

5

5

6

II

Abkürzungsverzeichnis

API

DPR

LLM

MRR

NLG

RAG

Application Programming Interface

Dense Passage Retrieval

Large Language Model

Mean Reciprocal Rank

Natural Language Generation

Retrieval-Augmented Generation

RAGAS Retrieval-Augmented Generation Assessment

III

1 Einleitung

Technische Dokumentationen von Softwareprojekten bündeln umfangreiches projektspezifisches

Wissen, das für Entwicklung, Wartung und Einarbeitung von zentraler Bedeutung ist. Dieses Wissen

ist häufig über zahlreiche Dateien und Abstraktionsebenen verteilt, sodass die gezielte Beantwortung

konkreter Fragen einen erheblichen manuellen Suchaufwand erfordert. Große Sprachmodelle (Large

Language Models, LLM) können natürlichsprachliche Fragen beantworten, verfügen jedoch ohne

zusätzlichen Kontext nicht zuverlässig über aktuelles oder projektspezifisches Wissen und neigen zur

Generierung inhaltlich nicht gedeckter Aussagen (Ji et al., 2023).

Retrieval-Augmented Generation (RAG) adressiert diese Einschränkung, indem relevante Dokument-

stellen zur Laufzeit abgerufen und dem Sprachmodell als Kontext bereitgestellt werden (Lewis et al.,

2020). Die Qualität eines solchen Systems hängt maßgeblich davon ab, wie die zugrunde liegenden

Dokumente aufbereitet und in abrufbare Textsegmente zerlegt werden (Gao et al., 2023). Dieser als

Chunking bezeichnete Verarbeitungsschritt bestimmt, welche Informationen überhaupt indexiert und

im Retrieval gefunden werden können.

Die Problemstellung ergibt sich aus den gegenläufigen Anforderungen an die Segmentierung: Zu

kleine Segmente können den notwendigen Kontext verlieren, zu große Segmente erhöhen den Anteil

irrelevanter Information, und eine an der Dokumentstruktur unausgerichtete Zerlegung kann semantisch

zusammengehörige Inhalte trennen (Jimeno Yepes et al., 2024). Trotz der praktischen Relevanz

dieser Entscheidung liegt für technische Projektdokumentation bislang wenig systematische Evidenz

dazu vor, wie sich einzelne Chunking-Strategien auf die Retrieval- und Antwortqualität auswirken.

Die wissenschaftliche Relevanz liegt in der Notwendigkeit, RAG-Systeme komponentenweise zu

bewerten (Yu et al., 2025). Die praktische Relevanz besteht in der zunehmenden Verbreitung do-

kumentenbasierter Assistenzsysteme, deren Wirksamkeit unmittelbar von der Wahl der Chunking-

Strategie abhängt. Kontrollierte Vergleiche liegen bislang überwiegend für spezialisierte Fachdomänen

vor, etwa für unternehmensinterne technische Dokumente (Taiwo & Yusoff, 2026) oder die klinische

Entscheidungsunterstützung (Gomez-Cabello et al., 2025), während für entwicklerorientierte Open-

Source-Softwaredokumentation systematische Evidenz fehlt. Aus dieser Ausgangslage leitet sich die

folgende Forschungsfrage ab:

Wie beeinflussen unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität eines

Retrieval-Augmented-Generation-Systems bei der Beantwortung projektspezifischer Fragen auf Basis

technischer Open-Source-Dokumentation?

Ziel der Arbeit ist die Konzeption, Implementierung und Evaluation einer RAG-Pipeline zur fragebasier-

ten Erschließung technischer Open-Source-Dokumentation am Beispiel der Vue.js-Dokumentation. Im

Mittelpunkt steht der kontrollierte Vergleich mehrerer Chunking-Strategien, wobei sämtliche übrigen

Komponenten der Pipeline konstant gehalten werden, um den Einfluss der Segmentierung isoliert

messbar zu machen. Auf Basis der Ergebnisse werden begründete Handlungsempfehlungen für die

Gestaltung dokumentenbasierter RAG-Systeme abgeleitet.

Der Aufbau der Arbeit folgt dieser Zielsetzung: Nach der Einleitung werden die theoretischen Grundla-

gen dargestellt, gefolgt vom Forschungsdesign und dem Evaluationsverfahren. Es folgen die Ergeb-

nisse sowie deren Diskussion. Die Arbeit schließt mit Fazit und Limitationen.

1

2 Theoretische Fundierung

2.1 Grundlagen von Retrieval-Augmented Generation

Große Sprachmodelle sind auf umfangreichen Textkorpora vortrainierte neuronale Modelle, die auf

Basis von Wahrscheinlichkeitsverteilungen natürlichsprachliche Texte verarbeiten und erzeugen. Mit

der Einführung kontextsensitiver Repräsentationen durch transformerbasierte Architekturen wurde

die semantische Verarbeitung von Sprache deutlich verbessert (Devlin et al., 2019). Für die Suche

in Dokumentbeständen ist insbesondere die Abbildung von Texten auf numerische Vektoren, soge-

nannte Embeddings, relevant. Embeddings repräsentieren Bedeutung in einem hochdimensionalen

Vektorraum, in dem semantisch ähnliche Texte räumlich benachbart liegen, sodass Ähnlichkeit über

Distanz- oder Winkelmaße bestimmbar wird (Reimers & Gurevych, 2019). Diese Eigenschaft bildet

die technische Grundlage der vektorbasierten Suche, bei der eine Anfrage und Dokumentsegmente

im selben Vektorraum verglichen werden. Die Qualität der erzeugten Vektoren hängt dabei vom

eingesetzten Embedding-Modell ab; satzbasierte Modelle, die speziell für die Abbildung semantischer

Ähnlichkeit trainiert wurden, haben sich für Retrieval-Aufgaben als besonders geeignet erwiesen.

Retrieval-Augmented Generation verbindet ein generatives Sprachmodell mit einer externen Wissens-

quelle. Zur Laufzeit werden für eine Anfrage relevante Dokumentstellen abgerufen und gemeinsam

mit der Anfrage an das Sprachmodell übergeben, das die Antwort auf Basis dieses Kontextes erzeugt

(Lewis et al., 2020). Ein RAG-System lässt sich in die Teilschritte Dokumentvorverarbeitung, Segmen-

tierung, Einbettung, Indexierung, Abruf, Kontextzusammenstellung und Antwortgenerierung gliedern

(Gao et al., 2023). Jeder dieser Teilschritte stellt einen potenziellen Einflussfaktor auf die Gesamtquali-

tät dar, weshalb eine isolierte Untersuchung einzelner Komponenten für ein differenziertes Verständnis

notwendig ist. Der Abruf erfolgt häufig über dichte Vektorrepräsentationen (Dense Retrieval), bei

den Anfragen und Passagen durch gelernte Embeddings verglichen werden; dieses Verfahren

hat sich gegenüber rein lexikalischer Suche bei der Beantwortung offener Fragen als leistungsfähig

erwiesen (Karpukhin et al., 2020). Der Ansatz adressiert insbesondere die Probleme fehlender Aktuali-

tät, mangelnder Domänenspezifik und nicht belegter Aussagen, die bei der alleinigen Nutzung des

Modellwissens auftreten. Eine Halluzination liegt dabei vor, wenn die generierte Antwort Informationen

enthält, die weder durch die bereitgestellten Kontextpassagen noch durch die Referenzantwort gedeckt

sind oder diesen widersprechen (Ji et al., 2023). Für die geplante Arbeit wird Dense Retrieval als

Abrufverfahren gewählt, da es sich für die vektorbasiert Such in strukturierten Dokumentbeständen

bewährt hat und eine konsistente Vergleichsbasis über alle Chunking-Strategien hinweg gewähr-

leistet. Dabei werden die abgerufenen Textsegmente gemeinsam mit der ursprünglichen Anfrage in

einem strukturierten Prompt zusammengeführt, sodass das Sprachmodell die Antwort ausschließ-

lich auf Basis des bereitgestellten Kontextes erzeugt. Durch die Konstanthaltung des Prompts, des

Sprachmodells und der Abrufparameter über alle Versuchsbedingungen hinweg wird sichergestellt,

dass beobachtete Unterschiede in der Antwortqualität auf die Segmentierung und nicht auf andere

Pipeline-Komponenten zurückzuführen sind.

2

2.2 Chunking und Evaluation von RAG-Systemen

Chunking bezeichnet die Zerlegung von Dokumenten in abrufbare Textsegmente. Die Segmentierung

bestimmt die Granularität der indexierten Einheiten und beeinflusst damit unmittelbar, welche Infor-

mationen im Retrieval auffindbar sind. In der Literatur werden im Wesentlichen größenbasierte und

strukturbasierte Verfahren unterschieden. Größenbasierte Strategien zerlegen Texte in Segmente

fester Länge, optional mit Überlappung benachbarter Segmente, um den Verlust von Information an

Segmentgrenzen zu verringern. Strukturbasierte Strategien orientieren sich an der Dokumentstruk-

tur, etwa an Überschriftenebenen, und erhalten dadurch semantisch zusammenhängende Einheiten

(Jimeno Yepes et al., 2024). Empirische Untersuchungen zeigen, dass die Wahl der Segmentgröße

einen messbaren Einfluss auf die Leistungsfähigkeit von RAG-Systemen hat (Hladěna et al., 2025),

und dass Retriever, Segmentierung und Generierung als zusammenhängende Einflussgrößen zu

betrachten sind (Finardi et al., 2024). Der Vorteil aufwändigerer Segmentierung ist allerdings nicht

gesichert: Vergleichende Untersuchungen zeigen, dass semantisch oder strukturell motivierte Ver-

fahren größenbasiertes Chunking nicht konsistent übertreffen und der zusätzliche Aufwand häufig

nicht durch entsprechende Qualitätsgewinne gerechtfertigt wird (Qu et al., 2025). Größenbasiertes

Chunking mit Überlappung stellt somit keine triviale Ausgangsbasis, sondern einen leistungsfähigen

Vergleichsmaßstab dar. Der eigentliche Erkenntnisgewinn eines kontrollierten Vergleichs liegt daher

nicht in der Frage, welche Strategie pauschal überlegen ist, sondern in der differenzierten Betrachtung

von Effektgröße, Kosten, Metrik-Abhängigkeit und der Interaktion mit unterschiedlichen Fragetypen.

Für technische Projektdokumentation, die typischerweise klar strukturierte und überschriftenbasierte

Inhalte aufweist, ist die vergleichende Untersuchung dieser Strategien von besonderer Bedeutung.

Die Bewertung von RAG-Systemen erfolgt auf zwei Ebenen. Auf der Retrieval-Ebene wird geprüft,

ob die für eine Anfrage relevanten Dokumentstellen abgerufen werden; hierfür werden etablierte

Maße der Informationsbeschaffung verwendet, insbesondere Precision und Recall sowie der Mean

Reciprocal Rank, der die Position des ersten relevanten Treffers bewertet (Manning et al., 2008). Auf

der Antwortebene wird die generierte Antwort hinsichtlich Korrektheit, Vollständigkeit, Quellenbezug

und Halluzinationsfreiheit beurteilt. Aktuelle Übersichtsarbeiten betonen, dass eine aussagekräftige

Bewertung beide Ebenen sowie die Qualität des bereitgestellten Kontextes berücksichtigen muss (Yu

et al., 2025). Ergänzend wurden automatisierte Evaluationsverfahren vorgeschlagen, die Aspekte

wie Faithfulness und Kontextrelevanz mithilfe von Sprachmodellen schätzen (Es et al., 2024); solche

Verfahren gelten als hilfreiche Ergänzung, ersetzen eine referenzbasierte Bewertung mit definier-

der Ground Truth jedoch nicht vollständig, da modellgestützte Bewertungen methodisch angreifbar

bleiben (Yu et al., 2025). Der dargestellte Forschungsstand zeigt, dass Chunking als eigenständi-

ger Einflussfaktor anerkannt ist. Kontrolliert erhobene Vergleiche einzelner Strategien liegen jedoch

überwiegend für spezialisierte Fachdomänen vor, etwa für unternehmensinterne technische Doku-

mente (Taiwo & Yusoff, 2026) oder die klinische Entscheidungsunterstützung (Gomez-Cabello et al.,

2025). Die Dokumentmerkmale dieser Domänen unterscheiden sich von entwicklerorientierter Open-

Source-Softwaredokumentation, die typischerweise strukturierte Markdown-Inhalte, eine Mischung

aus konzeptuellen und prozeduralen Abschnitten sowie eingebettete Codebeispiele aufweist. Für

diesen Dokumenttyp liegt bislang wenig systematische, vergleichende Evidenz vor. An dieser For-

schungslücke setzt die geplante Arbeit an, indem sie mehrere Chunking-Strategien unter konstanten

Rahmenbedingungen auf einem ausgezeichnet dokumentierten Softwareprojekt vergleicht und die

Antwortqualität primär referenzbasiert bewertet.

3

3 Methodik / Forschungsdesign

Zur Beantwortung der Forschungsfrage wird ein experimenteller Vergleich dreier Chunking-Strategien

gewählt, und zwar größenbasiertes Chunking ohne Überlappung, größenbasiertes Chunking mit Über-

lappung sowie strukturbasiertes Chunking entlang der Markdown-Überschriften. Dabei wird ausschließ-

lich die Segmentierung als unabhängige Variable variiert und alle übrigen Pipeline-Komponenten

konstant gehalten, insbesondere der Dokumentkorpus, das Embedding-Modell, das Sprachmodell, die

Temperatur, die Anzahl abgerufener Segmente, der verwendete Prompt, der Fragenkatalog, die Bewer-

tungsrubrik sowie der Vektorindex. Durch diese Isolierung lassen sich beobachtete Unterschiede in der

Retrieval- und Antwortqualität auf die Chunking-Strategie zurückführen. Ein experimenteller Vergleich

ist zur Beantwortung der Forschungsfrage geeignet, weil diese auf einen kausal interpretierbaren

Einfluss der Segmentierung abzielt.

Aus dem dargestellten Forschungsstand werden drei explorative Hypothesen abgeleitet, die im Rahmen

der Auswertung überprüft werden: (H1) Strukturbasiertes Chunking übertrifft größenbasiertes ohne

Überlappung hinsichtlich der Retrieval-Qualität, nicht aber durchgängig größenbasiertes mit Überlap-

pung, da diese den Informationsverlust an Segmentgrenzen weitgehend kompensiert. (H2) Retrieval-

Unterschiede übertragen sich nur teilweise auf die Antwortqualität, da das Sprachmodell moderate

Defizite ausgleichen kann. (H3) Die relative Eignung der Strategien variiert nach Fragetyp, wobei

strukturbasiertes Chunking insbesondere konzeptuelle, abschnittsübergreifende Fragen begünstigt,

während größenbasierte Verfahren für eng umgrenzte faktische Fragen ausreichen. Die Hypothe-

sen werden nicht inferenzstatistisch bestätigt, sondern dienen als explorative Leitannahmen für die

deskriptive Auswertung.

Als Datengrundlage dient ein fixierter, über einen konkreten Commit reproduzierbarer Snapshot der

englischsprachigen Dokumentation des JavaScript-Frameworks Vue.js, die als entwicklerorientiert

und didaktisch hochwertig gilt, technisch differenzierte konzeptuelle und prozedurale Inhalte umfasst

und durchgängig in Markdown vorliegt. Der Korpus wird bewusst auf ausgewählte Bereiche begrenzt

und in einem Korpusmanifest dokumentiert. Die Datenerhebung umfasst einen manuell kuratierten

Fragenkatalog von etwa 40 Fragen unterschiedlicher Typen (faktisch, prozedural, konzeptuell, ver-

gleichend, Fehler-/Randfälle) mit vorab festgelegten Referenzantworten und annotierten Quellen als

Ground Truth. Die vorherige Festlegung der Referenzdaten dient der Vermeidung einer nachträglichen,

ergebnisorientierten Anpassung der Bewertungsgrundlage.

Die Retrieval-Evaluation verwendet Recall@k, Precision@k und Mean Reciprocal Rank (Manning

et al., 2008); die Antwortqualität wird anhand einer gleich gewichteten Rubrik (Skala 0 bis 2) mit

den Kriterien Korrektheit, Vollständigkeit, Quellenbezug, Halluzinationsfreiheit und Verständlichkeit

beurteilt. Zur Triangulation dient die referenzbasierte manuelle Bewertung als primäres Verfahren,

da sie auf einer vorab definierten Ground Truth beruht und nicht zirkulär ist. Ergänzend wird ein

automatisiertes Evaluationsframework (Es et al., 2024) als sekundäres Verfahren eingesetzt; die

Übereinstimmung beider Verfahren wird als zusätzlicher Validitätsindikator herangezogen (Yu et al.,

2025). Ergänzend werden Effizienzkennzahlen (Chunk-Anzahl, Indexgröße, Token-Verbrauch) erfasst,

um die Qualitätsunterschiede den jeweiligen Kosten der Strategien gegenüberzustellen. Die interne

Validität wird durch Konstanthaltung der Parameter und eine Temperatur von null gestützt; die externe

Validität ist durch den einzelnen Korpus begrenzt. Diese Limitationen werden in der Arbeit offengelegt

und bei der Interpretation der Ergebnisse berücksichtigt.

4

4 Geplante Gliederung

1 Einleitung

1.1 Problemstellung und Ausgangslage
1.2 Zielsetzung und Forschungsfrage
1.3 Aufbau der Arbeit

2 Theoretische Fundierung

2.1 Sprachmodelle und vektorbasierte Textrepräsentation
2.2 Retrieval-Augmented Generation
2.3 Chunking technischer Dokumentation
2.4 Evaluation von RAG-Systemen
2.5 Forschungsstand und Forschungslücke

3 Methodik und Forschungsdesign

3.1 Forschungsdesign
3.2 Dokumentkorpus und Snapshot
3.3 Fragenkatalog und Referenzdaten
3.4 Evaluationsverfahren
3.5 Implementierung

4 Präsentation und Analyse der Forschungsergebnisse

4.1 Ergebnisse der Retrieval-Evaluation
4.2 Ergebnisse der Antwortbewertung
4.3 Zusammenhang von Retrieval- und Antwortqualität
4.4 Effizienzbetrachtung

5 Diskussion und Handlungsempfehlungen

5.1 Interpretation der Ergebnisse
5.2 Handlungsempfehlungen
5.3 Validitätsbetrachtung

6 Fazit und Limitationen

6.1 Beantwortung der Forschungsfrage
6.2 Ausblick auf weiterführende Forschung

5 Zeitplan

Oktober

November

Dezember

W 1–2 W 3–4 W 5–6 W 7–8 W 9–10 W 11–12

Vorbereitung & Literatur

Korpus & Fragenkatalog

Implementierung

Experimente & Auswertung

Analyse & Visualisierung

Schreibphase

Überarbeitung & Korrektur

Abgabe

Abb. 1: Geplanter Zeitplan der Bachelorarbeit (Oktober bis Dezember 2026)

Eigene Darstellung.

5

Literaturverzeichnis

Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep Bidirection-

al Transformers for Language Understanding. Proceedings of the 2019 Conference of the

North American Chapter of the Association for Computational Linguistics: Human Language

Technologies, Volume 1 (Long and Short Papers), 4171–4186. DOI: 10.18653/v1/N19-1423.

Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAs: Automated Evaluation of

Retrieval Augmented Generation. Proceedings of the 18th Conference of the European Chapter

of the Association for Computational Linguistics: System Demonstrations, 150–158. DOI:

10.18653/v1/2024.eacl-demo.16.

Finardi, P., Avila, L., Castaldoni, R., Gengo, P., Larcher, C., Piau, M., Costa, P., & Caridá, V. (2024).

The Chronicles of RAG: The Retriever, the Chunk and the Generator [arXiv-Preprint ar-

Xiv:2401.07883]. DOI: 10.48550/arXiv.2401.07883.

Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., Guo, Q., Wang, M., & Wang, H.

(2023). Retrieval-Augmented Generation for Large Language Models: A Survey [arXiv-Preprint

arXiv:2312.10997]. DOI: 10.48550/arXiv.2312.10997.

Gomez-Cabello, C. A., Prabha, S., Haider, S. A., Genovese, A., Collaco, B. G., Wood, N. G., Bagaria, S.,

& Forte, A. J. (2025). Comparative Evaluation of Advanced Chunking for Retrieval-Augmented

Generation in Large Language Models for Clinical Decision Support. Bioengineering, 12(11),

1194. DOI: 10.3390/bioengineering12111194.

Hladěna, J., Šteflovič, K., Čech, P., Štekerová, K., & Žváčková, A. (2025). The Effect of Chunk Size

on the RAG Performance. Software Engineering: Emerging Trends and Practices in System

Development (CSOC 2025), 1559, 317–326. DOI: 10.1007/978-3-032-00712-4_21.

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Madotto, A., & Fung, P. (2023).

Survey of Hallucination in Natural Language Generation. ACM Computing Surveys, 55(12),

1–38. DOI: 10.1145/3571730.

Jimeno Yepes, A., You, Y., Milczek, J., Laverde, S., & Li, R. (2024). Financial Report Chunking for

Effective Retrieval Augmented Generation [arXiv-Preprint arXiv:2402.05131]. DOI: 10.48550/

arXiv.2402.05131.

Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W.-t. (2020). Dense

Passage Retrieval for Open-Domain Question Answering. Proceedings of the 2020 Conference

on Empirical Methods in Natural Language Processing (EMNLP), 6769–6781. DOI: 10.18653/

v1/2020.emnlp-main.550.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih,

W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for

6

Knowledge-Intensive NLP Tasks. In H. Larochelle, M. Ranzato, R. Hadsell, M. F. Balcan

& H. Lin (Hrsg.), Advances in Neural Information Processing Systems 33 (NeurIPS 2020)

(S. 9459–9474). Curran Associates, Inc.

Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval. Cambridge

University Press.

Qu, R., Bao, F., & Tu, R. (2025). Is Semantic Chunking Worth the Computational Cost? Findings of

the Association for Computational Linguistics: NAACL 2025. DOI: 10.18653/v1/2025.findings-

naacl.114.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-

Networks. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Pro-

cessing and the 9th International Joint Conference on Natural Language Processing (EMNLP-

IJCNLP), 3982–3992. DOI: 10.18653/v1/D19-1410.

Taiwo, S., & Yusoff, M. A. (2026). Evaluating Chunking Strategies for Retrieval-Augmented Generation

in Oil and Gas Enterprise Documents [arXiv-Preprint arXiv:2603.24556].

Yu, H., Gan, A., Zhang, K., Tong, S., Liu, Q., & Liu, Z. (2025). Evaluation of Retrieval-Augmented

Generation: A Survey. Big Data (BigData 2024), 2301, 102–120. DOI: 10.1007/978-981-96-

1024-2_8.

7
Exposé

IU Internationale Hochschule

Studiengang: B.Sc. Informatik

Einfluss von Chunking-Strategien auf die Retrieval- und
Antwortqualität eines Retrieval-Augmented-Generation-Systems
für technische Projektdokumentation

Jonas Weirauch

Matrikelnummer: 10237021

Im Wiesengrund 19, 55286 Sulzheim

Betreuer/in: Prof. Klaus Quibeldey-Cirkel

Abgabedatum: 31.12.2026

Inhaltsverzeichnis

Abkürzungsverzeichnis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

III

1 Einleitung . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

2 Theoretische Fundierung . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

2.1 Grundlagen von Retrieval-Augmented Generation . . . . . . . . . . . . . . . . . . . .

2.2 Chunking und Evaluation von RAG-Systemen . . . . . . . . . . . . . . . . . . . . . . .

3 Methodik / Forschungsdesign . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

4 Geplante Gliederung . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

5 Zeitplan . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

Literaturverzeichnis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

1

2

2

2

4

5

5

6

II

Abkürzungsverzeichnis

API

DPR

LLM

MRR

NLG

RAG

Application Programming Interface

Dense Passage Retrieval

Large Language Model

Mean Reciprocal Rank

Natural Language Generation

Retrieval-Augmented Generation

RAGAS Retrieval-Augmented Generation Assessment

III

1 Einleitung

Technische Dokumentationen von Softwareprojekten bündeln umfangreiches projektspezifisches

Wissen, das für Entwicklung, Wartung und Einarbeitung von zentraler Bedeutung ist. Dieses Wissen

ist häufig über zahlreiche Dateien und Abstraktionsebenen verteilt, sodass die gezielte Beantwortung

konkreter Fragen einen erheblichen manuellen Suchaufwand erfordert. Große Sprachmodelle (Large

Language Models, LLM) können natürlichsprachliche Fragen beantworten, verfügen jedoch ohne

zusätzlichen Kontext nicht zuverlässig über aktuelles oder projektspezifisches Wissen und neigen zur

Generierung inhaltlich nicht gedeckter Aussagen (Ji et al., 2023).

Retrieval-Augmented Generation (RAG) adressiert diese Einschränkung, indem relevante Dokument-

stellen zur Laufzeit abgerufen und dem Sprachmodell als Kontext bereitgestellt werden (Lewis et al.,

2020). Die Qualität eines solchen Systems hängt maßgeblich davon ab, wie die zugrunde liegenden

Dokumente aufbereitet und in abrufbare Textsegmente zerlegt werden (Gao et al., 2023). Dieser als

Chunking bezeichnete Verarbeitungsschritt bestimmt, welche Informationen überhaupt indexiert und

im Retrieval gefunden werden können.

Die Problemstellung ergibt sich aus den gegenläufigen Anforderungen an die Segmentierung: Zu

kleine Segmente können den notwendigen Kontext verlieren, zu große Segmente erhöhen den Anteil

irrelevanter Information, und eine an der Dokumentstruktur unausgerichtete Zerlegung kann semantisch

zusammengehörige Inhalte trennen (Jimeno Yepes et al., 2024). Trotz der praktischen Relevanz

dieser Entscheidung liegt für technische Projektdokumentation bislang wenig systematische Evidenz

dazu vor, wie sich einzelne Chunking-Strategien auf die Retrieval- und Antwortqualität auswirken.

Die wissenschaftliche Relevanz liegt in der Notwendigkeit, RAG-Systeme komponentenweise zu

bewerten (Yu et al., 2025). Die praktische Relevanz besteht in der zunehmenden Verbreitung do-

kumentenbasierter Assistenzsysteme, deren Wirksamkeit unmittelbar von der Wahl der Chunking-

Strategie abhängt. Kontrollierte Vergleiche liegen bislang überwiegend für spezialisierte Fachdomänen

vor, etwa für unternehmensinterne technische Dokumente (Taiwo & Yusoff, 2026) oder die klinische

Entscheidungsunterstützung (Gomez-Cabello et al., 2025), während für entwicklerorientierte Open-

Source-Softwaredokumentation systematische Evidenz fehlt. Aus dieser Ausgangslage leitet sich die

folgende Forschungsfrage ab:

Wie beeinflussen unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität eines

Retrieval-Augmented-Generation-Systems bei der Beantwortung projektspezifischer Fragen auf Basis

technischer Open-Source-Dokumentation?

Ziel der Arbeit ist die Konzeption, Implementierung und Evaluation einer RAG-Pipeline zur fragebasier-

ten Erschließung technischer Open-Source-Dokumentation am Beispiel der Vue.js-Dokumentation. Im

Mittelpunkt steht der kontrollierte Vergleich mehrerer Chunking-Strategien, wobei sämtliche übrigen

Komponenten der Pipeline konstant gehalten werden, um den Einfluss der Segmentierung isoliert

messbar zu machen. Auf Basis der Ergebnisse werden begründete Handlungsempfehlungen für die

Gestaltung dokumentenbasierter RAG-Systeme abgeleitet.

Der Aufbau der Arbeit folgt dieser Zielsetzung: Nach der Einleitung werden die theoretischen Grundla-

gen dargestellt, gefolgt vom Forschungsdesign und dem Evaluationsverfahren. Es folgen die Ergeb-

nisse sowie deren Diskussion. Die Arbeit schließt mit Fazit und Limitationen.

1

2 Theoretische Fundierung

2.1 Grundlagen von Retrieval-Augmented Generation

Große Sprachmodelle sind auf umfangreichen Textkorpora vortrainierte neuronale Modelle, die auf

Basis von Wahrscheinlichkeitsverteilungen natürlichsprachliche Texte verarbeiten und erzeugen. Mit

der Einführung kontextsensitiver Repräsentationen durch transformerbasierte Architekturen wurde

die semantische Verarbeitung von Sprache deutlich verbessert (Devlin et al., 2019). Für die Suche

in Dokumentbeständen ist insbesondere die Abbildung von Texten auf numerische Vektoren, soge-

nannte Embeddings, relevant. Embeddings repräsentieren Bedeutung in einem hochdimensionalen

Vektorraum, in dem semantisch ähnliche Texte räumlich benachbart liegen, sodass Ähnlichkeit über

Distanz- oder Winkelmaße bestimmbar wird (Reimers & Gurevych, 2019). Diese Eigenschaft bildet

die technische Grundlage der vektorbasierten Suche, bei der eine Anfrage und Dokumentsegmente

im selben Vektorraum verglichen werden. Die Qualität der erzeugten Vektoren hängt dabei vom

eingesetzten Embedding-Modell ab; satzbasierte Modelle, die speziell für die Abbildung semantischer

Ähnlichkeit trainiert wurden, haben sich für Retrieval-Aufgaben als besonders geeignet erwiesen.

Retrieval-Augmented Generation verbindet ein generatives Sprachmodell mit einer externen Wissens-

quelle. Zur Laufzeit werden für eine Anfrage relevante Dokumentstellen abgerufen und gemeinsam

mit der Anfrage an das Sprachmodell übergeben, das die Antwort auf Basis dieses Kontextes erzeugt

(Lewis et al., 2020). Ein RAG-System lässt sich in die Teilschritte Dokumentvorverarbeitung, Segmen-

tierung, Einbettung, Indexierung, Abruf, Kontextzusammenstellung und Antwortgenerierung gliedern

(Gao et al., 2023). Jeder dieser Teilschritte stellt einen potenziellen Einflussfaktor auf die Gesamtquali-

tät dar, weshalb eine isolierte Untersuchung einzelner Komponenten für ein differenziertes Verständnis

notwendig ist. Der Abruf erfolgt häufig über dichte Vektorrepräsentationen (Dense Retrieval), bei

denem Anfragen und Passagen durch gelernte Embeddings verglichen werden; dieses Verfahren

hat sich gegenüber rein lexikalischer Suche bei der Beantwortung offener Fragen als leistungsfähig

erwiesen (Karpukhin et al., 2020). Der Ansatz adressiert insbesondere die Probleme fehlender Aktuali-

tät, mangelnder Domänenspezifik und nicht belegter Aussagen, die bei der alleinigen Nutzung des

Modellwissens auftreten. Eine Halluzination liegt dabei vor, wenn die generierte Antwort Informationen

enthält, die weder durch die bereitgestellten Kontextpassagen noch durch die Referenzantwort gedeckt

sind oder diesen widersprechen (Ji et al., 2023). Für die geplante Arbeit wird Dense Retrieval als

Abrufverfahren gewählt, da es sich für die vektorbasierte Suche in strukturierten Dokumentbeständen

bewährt hat und eine konsistente Vergleichsbasis über alle Chunking-Strategien hinweg gewähr-

leistet. Dabei werden die abgerufenen Textsegmente gemeinsam mit der ursprünglichen Anfrage in

einem strukturierten Prompt zusammengeführt, sodass das Sprachmodell die Antwort ausschließ-

lich auf Basis des bereitgestellten Kontextes erzeugt. Durch die Konstanthaltung des Prompts, des

Sprachmodells und der Abrufparameter über alle Versuchsbedingungen hinweg wird sichergestellt,

dass beobachtete Unterschiede in der Antwortqualität auf die Segmentierung und nicht auf andere

Pipeline-Komponenten zurückzuführen sind.

2

2.2 Chunking und Evaluation von RAG-Systemen

Chunking bezeichnet die Zerlegung von Dokumenten in abrufbare Textsegmente. Die Segmentierung

bestimmt die Granularität der indexierten Einheiten und beeinflusst damit unmittelbar, welche Infor-

mationen im Retrieval auffindbar sind. In der Literatur werden im Wesentlichen größenbasierte und

strukturbasierte Verfahren unterschieden. Größenbasierte Strategien zerlegen Texte in Segmente

fester Länge, optional mit Überlappung benachbarter Segmente, um den Verlust von Information an

Segmentgrenzen zu verringern. Strukturbasierte Strategien orientieren sich an der Dokumentstruk-

tur, etwa an Überschriftenebenen, und erhalten dadurch semantisch zusammenhängende Einheiten

(Jimeno Yepes et al., 2024). Empirische Untersuchungen zeigen, dass die Wahl der Segmentgröße

einen messbaren Einfluss auf die Leistungsfähigkeit von RAG-Systemen hat (Hladěna et al., 2025),

und dass Retriever, Segmentierung und Generierung als zusammenhängende Einflussgrößen zu

betrachten sind (Finardi et al., 2024). Der Vorteil aufwändigerer Segmentierung ist allerdings nicht

gesichert: Vergleichende Untersuchungen zeigen, dass semantisch oder strukturell motivierte Ver-

fahren größenbasiertes Chunking nicht konsistent übertreffen und der zusätzliche Aufwand häufig

nicht durch entsprechende Qualitätsgewinne gerechtfertigt wird (Qu et al., 2025). Größenbasiertes

Chunking mit Überlappung stellt somit keine triviale Ausgangsbasis, sondern einen leistungsfähigen

Vergleichsmaßstab dar. Der eigentliche Erkenntnisgewinn eines kontrollierten Vergleichs liegt daher

nicht in der Frage, welche Strategie pauschal überlegen ist, sondern in der differenzierten Betrachtung

von Effektgröße, Kosten, Metrik-Abhängigkeit und der Interaktion mit unterschiedlichen Fragetypen.

Für technische Projektdokumentation, die typischerweise klar strukturierte und überschriftenbasierte

Inhalte aufweist, ist die vergleichende Untersuchung dieser Strategien von besonderer Bedeutung.

Die Bewertung von RAG-Systemen erfolgt auf zwei Ebenen. Auf der Retrieval-Ebene wird geprüft,

ob die für eine Anfrage relevanten Dokumentstellen abgerufen werden; hierfür werden etablierte

Maße der Informationsbeschaffung verwendet, insbesondere Precision und Recall sowie der Mean

Reciprocal Rank, der die Position des ersten relevanten Treffers bewertet (Manning et al., 2008). Auf

der Antwortebene wird die generierte Antwort hinsichtlich Korrektheit, Vollständigkeit, Quellenbezug,

und Halluzinationsfreiheit beurteilt. Aktuelle Übersichtsarbeiten betonen, dass eine aussagekräftige

Bewertung beide Ebenen sowie die Qualität des bereitgestellten Kontextes berücksichtigen muss (Yu

et al., 2025). Ergänzend wurden automatisierte Evaluationsverfahren vorgeschlagen, die Aspekte

wie Faithfulness und Kontextrelevanz mithilfe von Sprachmodellen schätzen (Es et al., 2024); solche

Verfahren gelten als hilfreiche Ergänzung, ersetzen eine referenzbasierte Bewertung mit definier-
	er Ground Truth jedoch nicht vollständig, da modellgestützte Bewertungen methodisch angreifbar

bleiben (Yu et al., 2025). Der dargestellte Forschungsstand zeigt, dass Chunking als eigenständi-

ger Einflussfaktor anerkannt ist. Kontrolliert erhobene Vergleiche einzelner Strategien liegen jedoch

overwiegend für spezialisierte Fachdomänen vor, etwa für unternehmensinterne technische Doku-

mente (Taiwo & Yusoff, 2026) oder die klinische Entscheidungsunterstützung (Gomez-Cabello et al.,

2025). Die Dokumentmerkmale dieser Domänen unterscheiden sich von entwicklerorientierter Open-

Source-Softwaredokumentation, die typischerweise strukturierte Markdown-Inhalte, eine Mischung

aus konzeptuellen und prozeduralen Abschnitten sowie eingebettete Codebeispiele aufweist. Für

diesen Dokumenttyp liegt bislang wenig systematische, vergleichende Evidenz vor. An dieser For-

schungslücke setzt die geplante Arbeit an, indem sie mehrere Chunking-Strategien unter konstanten

Rahmenbedingungen auf einem ausgezeichnet dokumentierten Softwareprojekt vergleicht und die

Antwortqualität primär referenzbasiert bewertet.

3

3 Methodik / Forschungsdesign

Zur Beantwortung der Forschungsfrage wird ein experimenteller Vergleich dreier Chunking-Strategien

gewählt, und zwar größenbasiertes Chunking ohne Überlappung, größenbasiertes Chunking mit Über-

lappung sowie strukturbasiertes Chunking entlang der Markdown-Überschriften. Dabei wird ausschließ-

lich die Segmentierung als unabhängige Variable variiert und alle übrigen Pipeline-Komponenten

konstant gehalten, insbesondere der Dokumentkorpus, das Embedding-Modell, das Sprachmodell,

die Temperatur, die Anzahl abgerufener Segmente, der verwendete Prompt, der Fragenkatalog, die Bewer-

tungsrubrik sowie der Vektorindex. Durch diese Isolierung lassen sich beobachtete Unterschiede in der

Retrieval- und Antwortqualität auf die Chunking-Strategie zurückführen. Ein experimenteller Vergleich

ist zur Beantwortung der Forschungsfrage geeignet, weil diese auf einen kausal interpretierbaren

Einfluss der Segmentierung abzielt.

Aus dem dargestellten Forschungsstand werden drei explorative Hypothesen abgeleitet, die im Rahmen

der Auswertung überprüft werden: (H1) Strukturbasiertes Chunking übertrifft größenbasiertes ohne

Überlappung hinsichtlich der Retrieval-Qualität, nicht aber durchgängig größenbasiertes mit Überlap-

pung, da diese den Informationsverlust an Segmentgrenzen weitgehend kompensiert. (H2) Retrieval-

Unterschiede übertragen sich nur teilweise auf die Antwortqualität, da das Sprachmodell moderate

Defizite ausgleichen kann. (H3) Die relative Eignung der Strategien variiert nach Fragetyp, wobei

strukturbasiertes Chunking insbesondere konzeptuelle, abschnittsübergreifende Fragen begünstigt,

während größenbasierte Verfahren für eng umgrenzte faktische Fragen ausreichen. Die Hypothe-

sen werden nicht inferenzstatistisch bestätigt, sondern dienen als explorative Leitannahmen für die

deskriptive Auswertung.

Als Datengrundlage dient ein fixierter, über einen konkreten Commit reproduzierbarer Snapshot der

englischsprachigen Dokumentation des JavaScript-Frameworks Vue.js, die als entwicklerorientiert

und didaktisch hochwertig gilt, technisch differenzierte konzeptuelle und prozedurale Inhalte umfasst

und durchgängig in Markdown vorliegt. Der Korpus wird bewusst auf ausgewählte Bereiche begrenzt

und in einem Korpusmanifest dokumentiert. Die Datenerhebung umfasst einen manuell kuratierten

Fragenkatalog von etwa 40 Fragen unterschiedlicher Typen (faktisch, prozedural, konzeptuell, ver-

gleichend, Fehler-/Randfälle) mit vorab festgelegten Referenzantworten und annotierten Quellen als

Ground Truth. Die vorherige Festlegung der Referenzdaten dient der Vermeidung einer nachträglichen,

ergebnisorientierten Anpassung der Bewertungsgrundlage.

Die Retrieval-Evaluation verwendet Recall@k, Precision@k und Mean Reciprocal Rank (Manning

et al., 2008); die Antwortqualität wird anhand einer gleich gewichteten Rubrik (Skala 0 bis 2) mit

den Kriterien Korrektheit, Vollständigkeit, Quellenbezug, Halluzinationsfreiheit und Verständlichkeit

beurteilt. Zur Triangulation dient die referenzbasierte manuelle Bewertung als primäres Verfahren,

da sie auf einer vorab definierten Ground Truth beruht und nicht zirkulär ist. Ergänzend wird ein

automatisiertes Evaluationsframework (Es et al., 2024) als sekundäres Verfahren eingesetzt; die

Übereinstimmung beider Verfahren wird als zusätzlicher Validitätsindikator herangezogen (Yu et al.,

2025). Ergänzend werden Effizienzkennzahlen (Chunk-Anzahl, Indexgröße, Token-Verbrauch) erfasst,

um die Qualitätsunterschiede den jeweiligen Kosten der Strategien gegenüberzustellen. Die interne

Validität wird durch Konstanthaltung der Parameter und eine Temperatur von null gestützt; die externe

Validität ist durch den einzelnen Korpus begrenzt. Diese Limitationen werden in der Arbeit offengelegt

und bei der Interpretation der Ergebnisse berücksichtigt.

4

4 Geplante Gliederung

1 Einleitung

1.1 Problemstellung und Ausgangslage
1.2 Zielsetzung und Forschungsfrage
1.3 Aufbau der Arbeit

2 Theoretische Fundierung

2.1 Sprachmodelle und vektorbasierte Textrepräsentation
2.2 Retrieval-Augmented Generation
2.3 Chunking technischer Dokumentation
2.4 Evaluation von RAG-Systemen
2.5 Forschungsstand und Forschungslücke

3 Methodik und Forschungsdesign

3.1 Forschungsdesign
3.2 Dokumentkorpus und Snapshot
3.3 Fragenkatalog und Referenzdaten
3.4 Evaluationsverfahren
3.5 Implementierung

4 Präsentation und Analyse der Forschungsergebnisse

4.1 Ergebnisse der Retrieval-Evaluation
4.2 Ergebnisse der Antwortbewertung
4.3 Zusammenhang von Retrieval- und Antwortqualität
4.4 Effizienzbetrachtung

5 Diskussion und Handlungsempfehlungen

5.1 Interpretation der Ergebnisse
5.2 Handlungsempfehlungen
5.3 Validitätsbetrachtung

6 Fazit und Limitationen

6.1 Beantwortung der Forschungsfrage
6.2 Ausblick auf weiterführende Forschung

5 Zeitplan

Oktober

November

Dezember

W 1–2 W 3–4 W 5–6 W 7–8 W 9–10 W 11–12

Vorbereitung & Literatur

Korpus & Fragenkatalog

Implementierung

Experimente & Auswertung

Analyse & Visualisierung

Schreibphase

Überarbeitung & Korrektur

Abgabe

Abb. 1: Geplanter Zeitplan der Bachelorarbeit (Oktober bis Dezember 2026)

Eigene Darstellung.

5

Literaturverzeichnis

Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep Bidirection-

al Transformers for Language Understanding. Proceedings of the 2019 Conference of the

North American Chapter of the Association for Computational Linguistics: Human Language

Technologies, Volume 1 (Long and Short Papers), 4171–4186. DOI: 10.18653/v1/N19-1423.

Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAs: Automated Evaluation of

Retrieval Augmented Generation. Proceedings of the 18th Conference of the European Chapter

of the Association for Computational Linguistics: System Demonstrations, 150–158. DOI:

10.18653/v1/2024.eacl-demo.16.

Finardi, P., Avila, L., Castaldoni, R., Gengo, P., Larcher, C., Piau, M., Costa, P., & Caridá, V. (2024).

The Chronicles of RAG: The Retriever, the Chunk and the Generator [arXiv-Preprint ar-

Xiv:2401.07883]. DOI: 10.48550/arXiv.2401.07883.

Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., Guo, Q., Wang, M., & Wang, H.

(2023). Retrieval-Augmented Generation for Large Language Models: A Survey [arXiv-Preprint

arXiv:2312.10997]. DOI: 10.48550/arXiv.2312.10997.

Gomez-Cabello, C. A., Prabha, S., Haider, S. A., Genovese, A., Collaco, B. G., Wood, N. G., Bagaria, S.,

& Forte, A. J. (2025). Comparative Evaluation of Advanced Chunking for Retrieval-Augmented

Generation in Large Language Models for Clinical Decision Support. Bioengineering, 12(11),

1194. DOI: 10.3390/bioengineering12111194.

Hladěna, J., Šteflovič, K., Čech, P., Štekerová, K., & Žváčková, A. (2025). The Effect of Chunk Size

on the RAG Performance. Software Engineering: Emerging Trends and Practices in System

Development (CSOC 2025), 1559, 317–326. DOI: 10.1007/978-3-032-00712-4_21.

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Madotto, A., & Fung, P. (2023).

Survey of Hallucination in Natural Language Generation. ACM Computing Surveys, 55(12),

1–38. DOI: 10.1145/3571730.

Jimeno Yepes, A., You, Y., Milczek, J., Laverde, S., & Li, R. (2024). Financial Report Chunking for

Effective Retrieval Augmented Generation [arXiv-Preprint arXiv:2402.05131]. DOI: 10.48550/

arXiv.2402.05131.

Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W.-t. (2020). Dense

Passage Retrieval for Open-Domain Question Answering. Proceedings of the 2020 Conference

on Empirical Methods in Natural Language Processing (EMNLP), 6769–6781. DOI: 10.18653/

v1/2020.emnlp-main.550.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih,

W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for

6

Knowledge-Intensive NLP Tasks. In H. Larochelle, M. Ranzato, R. Hadsell, M. F. Balcan

& H. Lin (Hrsg.), Advances in Neural Information Processing Systems 33 (NeurIPS 2020)

(S. 9459–9474). Curran Associates, Inc.

Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval. Cambridge

University Press.

Qu, R., Bao, F., & Tu, R. (2025). Is Semantic Chunking Worth the Computational Cost? Findings of

the Association for Computational Linguistics: NAACL 2025. DOI: 10.18653/v1/2025.findings-

naacl.114.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-

Networks. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Pro-

cessing and the 9th International Joint Conference on Natural Language Processing (EMNLP-

IJCNLP), 3982–3992. DOI: 10.18653/v1/D19-1410.

Taiwo, S., & Yusoff, M. A. (2026). Evaluating Chunking Strategies for Retrieval-Augmented Generation

in Oil and Gas Enterprise Documents [arXiv-Preprint arXiv:2603.24556].

Yu, H., Gan, A., Zhang, K., Tong, S., Liu, Q., & Liu, Z. (2025). Evaluation of Retrieval-Augmented

Generation: A Survey. Big Data (BigData 2024), 2301, 102–120. DOI: 10.1007/978-981-96-

1024-2_8.

7
