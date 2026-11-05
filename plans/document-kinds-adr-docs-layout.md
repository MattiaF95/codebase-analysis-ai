# Plan: Document kind, struttura docs/ e decision record con bridge PlanVault

ANALYSIS: COMPLETE
RETRIAGE: NO

## Agent execution header
- `PLAN_STATUS: IN_PROGRESS`
- `EXECUTION_READINESS: READY`
- `EXECUTION_SCOPE: FULL_PLAN`
- `CURRENT_REQ: REQ-4.1.1`
- `NEXT_ACTION: implement Phase 4 REQ-4.1.1 through REQ-4.1.5, verify, review, and commit`
- `COMPLETION_ALLOWED: NO`

## 1. Objective

Rendere il modello documentale capace di distinguere il tipo di documento oltre all'area sorgente e al topic, così che repository diversi possano adottare strutture e sezioni adeguate senza perdere validazione e navigabilità. Il piano introduce un catalogo dei `documentKind`, una struttura `docs/` ibrida area-first/kind-first, un formato ADR immutabile e un bridge opzionale con PlanVault per collegare decisioni durevoli e piani di esecuzione. L'obiettivo è mantenere compatibilità con le mappe e i documenti esistenti, senza nuove dipendenze e senza riscrivere la documentazione manuale.

## 2. Context and constraints

- **Evidenza autoritativa**: analisi del repository corrente, 80 test verdi, schema attuale di `docs/_meta/documentation-map.json`, template in `skill/codebase-analysis-ai/assets/templates/`, reference in `skill/codebase-analysis-ai/references/` e runtime in `skill/codebase-analysis-ai/scripts/codebase_analysis_ai/`.
- **Percorsi chiave già identificati**: `documentation_map.py` per schema e validazione della mappa; `document_validator.py` per scope e finding; `assets/templates/` per i template; `references/document-style.md`, `references/bootstrap-mode.md`, `references/migrate-mode.md`, `references/update-mode.md`, `references/audit-mode.md` e `references/project-taxonomy.md` per le istruzioni; `tests/unit/` e `tests/integration/` per le regressioni.
- **Decisioni confermate** (non riaprire senza nuova evidenza o richiesta esplicita):
  1. Il modello documentale acquisisce un terzo asse: area sorgente × `documentKind` × topic.
  2. La struttura `docs/` è ibrida: directory per area sorgente per la documentazione tecnica viva, directory per kind per i documenti trasversali (`decisions/`, `reference/`, `runbooks/`, `architecture/`).
  3. `docs/index.md` resta l'entry point canonico; ogni directory attiva di primo livello espone un `index.md` linkato dall'indice.
  4. `docs/_meta/` contiene i metadati, `docs/_archive/` lo storico e `docs/_analysis/` i report datati. `_archive` e `_analysis` sono esclusi dalla mappa attiva e dall'indice.
  5. Gli ADR vivono in `docs/decisions/` con nome `ADR-NNNN-<slug>.md`, stato `proposed`/`accepted`/`rejected`/`superseded`/`deprecated` e contenuto decisionale immutabile dopo l'acceptance.
  6. PlanVault resta la fonte di verità per l'esecuzione dei piani; gli ADR sono la fonte di verità per il rationale durevole. L'integrazione è un adapter opzionale, non una copia della skill PlanVault.
  7. `schemaVersion` resta `1`; `documentKind`, `sections` e `metadata` sono campi opzionali per compatibilità, ma i nuovi documenti creati da bootstrap/migrate dichiarano sempre `documentKind`.
  8. Il catalogo dei kind ha una sola fonte runtime; la reference umana è allineata e non duplica valori macchina.
  9. `sections` contiene le etichette localizzate realmente usate come heading, così la validazione resta compatibile con la lingua scelta.
  10. Nessuna nuova dipendenza esterna: solo standard library e Git.
- **Vincoli**:
  - Non rompere il caricamento delle mappe esistenti prive dei nuovi campi.
  - Non riscrivere il contenuto dei documenti manuali né cambiare automaticamente gli hash degli ADR.
  - Non creare directory vuote per simmetria.
  - Ogni cambiamento di comportamento deve avere un test di regressione.
  - Il piano non modifica la skill PlanVault e non richiede che sia installata.
- **Fuori scope**:
  - Esecuzione del piano `plans/fix-check-installer-consistency.md`.
  - Generazione automatica di ADR da piani o da commit.
  - Migrazione massiva di documentazione esistente o rinomina automatica di ADR.
  - Nuove modalità agentiche, nuovi provider o nuovi comandi oltre a quelli necessari.
  - Refactoring estetico non richiesto dai requisiti.

## 3. Phase 1 — Modello documentale e catalogo dei kind

### 3.1 Catalogo, schema e validazione

- [x] REQ-1.1.1 Catalogo dei tipi documento: esiste una fonte runtime unica che definisce per ogni `documentKind` sezioni richieste e raccomandate, ciclo di vita, politica di indicizzazione, posizione predefinita e obbligo di `sourcePatterns`; il catalogo copre almeno README di progetto, indice documentazione, area, topic, architettura, API reference, data model, runbook, test strategy, backlog, decision record, reference e report di analisi.
- [x] REQ-1.1.2 Schema della mappa esteso: `documentation-map.json` accetta `documentKind`, `sections` e `metadata` opzionali; una mappa `schemaVersion: 1` senza questi campi continua a caricarsi e validarsi; un kind sconosciuto o una `sections` malformata produce un errore esplicito e localizzato.
- [x] REQ-1.1.3 Validazione delle sezioni: quando un documento dichiara `sections`, il validatore verifica che ogni voce sia un heading di secondo livello presente una sola volta, che le sezioni richieste dal kind siano presenti e che non esistano heading vuoti; i documenti senza `sections` restano validi come legacy.
- [x] REQ-1.1.4 Compatibilità del modello: bootstrap e migrate dichiarano sempre `documentKind` per i nuovi documenti; audit segnala i documenti legacy privi di kind senza bloccarli; i test coprono mappa legacy, kind sconosciuto, sezioni localizzate, sezione richiesta mancante e sezione duplicata.

**Verifica fase**
- Una mappa esistente senza `documentKind`/`sections` produce lo stesso esito di prima.
- Un documento con `sections` e heading localizzati validi passa; uno con una sezione richiesta mancante fallisce con il nome della sezione.
- `python3 -m unittest discover -s tests -p "test_*.py"` resta verde.

## 4. Phase 2 — Struttura `docs/` e profili per tipologia

### 4.1 Layout, navigazione e collocazione

- [x] REQ-2.1.1 Layout canonico: la documentazione attiva usa `docs/index.md`, `docs/_meta/`, directory per area e directory per kind; `_archive/` e `_analysis/` sono opzionali; non vengono create directory vuote e lo stesso contenuto non è duplicato tra area e kind.
- [x] REQ-2.1.2 Navigazione e coverage: `docs/index.md` linka ogni area index e ogni kind index attivo, oltre a `_meta/coverage.md`; la coverage riporta conteggi per kind e per stato ADR; `_analysis/` non è indicizzato e `_archive/` resta escluso dalla documentazione attiva.
- [x] REQ-2.1.3 Collocazione e naming: le regole distinguono documenti area-first e kind-first, usano `kebab-case`, mantengono ID stabili e numerazione ADR a quattro cifre; path e ID esistenti non vengono rinominati automaticamente; `docs/adr/` è riconosciuto come alias legacy di `docs/decisions/`.
- [x] REQ-2.1.4 Profili per tipologia di repository: la guida di tassonomia mappa library, service, monorepo, CLI e applicazione full-stack ai kind e alle directory consigliate, senza imporre la stessa struttura a ogni repository.
- [x] REQ-2.1.5 Template e reference allineati: i template di indice, area e topic supportano le sezioni per kind; esiste un template per i report di analisi; le reference di bootstrap, migrate, update, audit e document-style descrivono layout, kind, collocazione e cicli di vita.

**Verifica fase**
- Un repository piccolo con una sola area produce solo `docs/index.md`, `_meta/` e l'area index, senza directory vuote.
- Un monorepo con più aree e un ADR produce area index, `decisions/index.md` e coverage coerente.
- Un report in `docs/_analysis/` non compare nell'indice e non è richiesto nella mappa attiva.
- I link di `docs/index.md` verso index di area, index di kind e coverage sono validi.

## 5. Phase 3 — Decision record (ADR)

### 5.1 Formato, indice e ciclo di vita

- [x] REQ-3.1.1 Template ADR: esiste un template con titolo `ADR-NNNN: <decisione>`, blocco stato/data/sostituzioni/piano e sezioni per contesto, decisione, alternative considerate, conseguenze, evidenza e collegamenti; il template è localizzabile senza cambiare i nomi canonici dei file.
- [x] REQ-3.1.2 Indice ADR: esiste un template per `docs/decisions/index.md` che elenca gli ADR raggruppati per stato, con una sintesi di una riga e link a ogni decisione; `docs/index.md` linka l'indice ADR.
- [x] REQ-3.1.3 Registrazione nella mappa: ogni ADR è registrato con `documentKind: decision-record`, `sections` localizzate, `sourcePatterns: []`, `sourceHashes: {}` e `metadata` con stato, data, `supersedes`, `supersededBy` e piani correlati opzionali.
- [x] REQ-3.1.4 Validazione ADR: il gate verifica numero univoco e coerente con il filename, stato ammesso, sezioni obbligatorie, catena `supersedes`/`supersededBy` coerente, presenza nell'indice e link validi verso documenti e piani; non aggiorna prosa né hash degli ADR.
- [x] REQ-3.1.5 Ciclo di vita e migrazione: un ADR `accepted` è immutabile salvo cambio di stato; una decisione nuova che sostituisce la precedente crea un nuovo ADR e marca il vecchio `superseded`; gli ADR esistenti in `docs/adr/` o `docs/decisions/` vengono riconosciuti e registrati senza rinomina o rinumerazione automatica.

**Verifica fase**
- Un ADR valido compare nell'indice e nella coverage; un numero duplicato o un filename incoerente fallisce.
- `accepted → superseded` con nuovo ADR mantiene la catena e non riscrive il rationale del vecchio.
- Un ADR con `sourceHashes` non vuoti viene segnalato; un ADR esistente in `docs/adr/` viene riconosciuto senza rinomina.
- La modifica manuale del solo stato non produce un errore di documento stale.

## 6. Phase 4 — Bridge PlanVault

### 6.1 Rilevamento, promozione e link

- [ ] REQ-4.1.1 Rilevamento opzionale: il sistema riconosce piani PlanVault single-file e 3-core-file quando presenti nel repository, ma non li richiede, non li modifica e non fallisce se PlanVault non è installato.
- [ ] REQ-4.1.2 Regola di promozione: una decisione resta nel `Decision Log` del piano finché è tattica o locale; diventa ADR quando è architetturale, durevole, vincola piani futuri o richiede una migrazione; la regola è documentata e verificabile.
- [ ] REQ-4.1.3 Link bidirezionali: un ADR può linkare il piano che lo ha confermato e un piano può linkare l'ADR; i link sono repo-relative, validati quando entrambi gli artefatti esistono e non duplicano contenuto tra piano e ADR.
- [ ] REQ-4.1.4 Comportamento di update e audit: update e audit segnalano le decisioni architetturali non ancora promosse ad ADR, ma non creano ADR e non modificano piani senza conferma esplicita; un piano completato non cambia lo stato dell'ADR.
- [ ] REQ-4.1.5 Documentazione e guardrail: la skill espone una reference dedicata al rapporto ADR/PlanVault, il router delle modalità e i guardrail distinguono esecuzione, rationale e proprietà dei file.

**Verifica fase**
- Un repository senza PlanVault produce documentazione e ADR validi senza errori.
- Un piano con un ADR collegato produce link validi in entrambe le direzioni.
- Audit segnala una decisione architetturale non promossa ma non crea file.
- Un piano completato non altera un ADR `accepted`.

## 7. Phase 5 — Validazione end-to-end e rollout

### 7.1 Gate, test e compatibilità

- [ ] REQ-5.1.1 Integrazione nel gate: `check`/`validate-docs` validano kind, sezioni, ADR e coverage senza modificare i documenti; `--warn-only` resta non bloccante su tutti i nuovi errori e `--json` produce sempre un report deserializzabile.
- [ ] REQ-5.1.2 Suite di regressione: i test coprono catalogo, schema legacy, sezioni localizzate, layout e index, ADR e supersession, link ADR/piano, esclusione di `_analysis`/`_archive` e assenza di aggiornamenti automatici degli hash ADR.
- [ ] REQ-5.1.3 Documentazione pubblica: README, reference e template descrivono la struttura `docs/`, i kind, gli ADR e il bridge PlanVault in modo coerente con il comportamento osservato, senza contratti morti o duplicati.
- [ ] REQ-5.1.4 Rollout e compatibilità: i repository esistenti mantengono mappe, path e documenti attuali; le nuove directory vengono create solo quando servono; `schemaVersion` resta `1`; non vengono introdotte dipendenze esterne.

**Verifica fase**
- `check --warn-only` restituisce 0 per un ADR invalido e `--json` resta valido.
- `check` su un repository con mappa legacy non produce nuovi errori bloccanti.
- La suite completa passa su Python 3.9 e 3.12.
- `rg` non trova riferimenti a un secondo catalogo dei kind o a contratti ADR duplicati.

## 8. Commit order

1. `feat(docs): add document kind catalog and section-aware validation`
2. `docs(structure): define canonical docs layout, indexes and repository profiles`
3. `feat(adr): add decision records, lifecycle and validation`
4. `feat(planvault): add optional decision bridge and guardrails`
5. `test(docs): cover kinds, ADR, coverage and legacy compatibility`

Ogni fase produce un commit atomico solo dopo il completamento di tutti i suoi REQ-ID, delle verifiche e dell'audit finale.

## 9. Exit criteria

- [ ] Tutti i REQ-ID attivi sono `[x]` con la verifica di fase soddisfatta.
- [ ] `python3 -m unittest discover -s tests -p "test_*.py"` passa su Python 3.9 e 3.12.
- [ ] Una mappa legacy senza `documentKind`/`sections` continua a caricarsi e a validarsi.
- [ ] Un nuovo documento creato da bootstrap/migrate dichiara `documentKind` e le sezioni richieste.
- [ ] `docs/index.md` linka ogni area index, ogni kind index attivo e `_meta/coverage.md`.
- [ ] `docs/_analysis/` non è indicizzato e `docs/_archive/` resta escluso.
- [ ] Un ADR valido è registrato, indicizzato e validato; una supersession non riscrive il rationale del vecchio ADR.
- [ ] Il bridge PlanVault è opzionale: senza PlanVault non ci sono errori, con PlanVault i link bidirezionali sono validati.
- [ ] Nessuna nuova dipendenza esterna oltre a Git e standard library.
- [ ] Nessun documento manuale viene riscritto o rimosso dal solo fatto di adottare il nuovo modello.

## 10. Risks and mitigations

- **Rigidità residua dei template**: il catalogo definisce sezioni richieste e raccomandate, non un unico testo; i profili per tipologia di repository evitano strutture identiche per contesti diversi.
- **Falsi positivi nella validazione delle sezioni**: la validazione si attiva solo quando `sections` è dichiarato; le etichette sono localizzate e memorizzate nella mappa, non dedotte da quelle inglesi.
- **Rottura delle mappe esistenti**: i nuovi campi sono opzionali, `schemaVersion` resta `1` e i test coprono mappe legacy.
- **ADR trattati come documenti living**: `sourceHashes` resta vuoto e il ciclo di vita è `status-only`; update e audit non riscrivono il rationale.
- **Accoppiamento con PlanVault**: il bridge è un adapter opzionale; PlanVault non viene copiato né modificato e la sua assenza non è un errore.
- **Migrazione di ADR esistenti**: `docs/adr/` è riconosciuto come alias; nessuna rinomina o rinumerazione automatica.
- **Report di analisi dispersi**: `docs/_analysis/` è escluso dall'indice e dalla mappa attiva, ma resta linkabile dai finding e dalla coverage come materiale datato.

## 11. Execution instructions

- Il piano è il prompt operativo e la fonte di verità durante l'esecuzione.
- Alla ricezione di un'intenzione di esecuzione, eseguire lo scope richiesto; senza scope più stretto, eseguire tutti i REQ-ID attivi residui.
- Iniziare dal primo REQ-ID attivo non completato nell'ordine del piano, dopo la validazione di lifecycle e struttura.
- Non fermarsi dopo analisi, inventario, preflight o validazione quando i prerequisiti di esecuzione sono soddisfatti.
- Non saltare un REQ-ID attivo e non marcarlo completato senza implementazione, verifica, review ed evidenza.
- Se il lavoro è bloccato, registrare blocker, evidenza, risoluzione richiesta e azione di ripresa; REQ-ID, fase e piano restano incompleti.
- Il piano è completo solo quando ogni REQ-ID attivo e ogni exit criterion sono completi ed evidenziati.
- Ogni fase deve produrre un risultato osservabile e una verifica che lo dimostri; la validazione finale deve dimostrare l'obiettivo complessivo, non solo i REQ-ID completati.
- Per operazioni rischiose o che possono fallire parzialmente (migrazione della mappa, registrazione ADR), documentare una procedura di retry o recovery sicura.

## 12. Triage outcome

- **Consolidation**: 0 micro-task consolidati; i 23 REQ-ID erano già raggruppati per esito verificabile. Le verifiche di fase coprono i test senza introdurre REQ-ID duplicati.
- **Structure**: piano single-file. Cinque fasi coese, massimo 5 REQ-ID per fase; la separazione in `spec.md`/`plan.md`/`tasks.md` non ridurrebbe il context drift.
- **Reusable review pattern**: nessun `review-audit-template.md` creato; le verifiche di fase sono specifiche e non ripetute.
- **Final `RETRIAGE` state**: `NO`.
- **Execution readiness**: `READY`; `PLAN_STATUS: OPEN`, `COMPLETION_ALLOWED: NO` perché tutti i REQ-ID e gli exit criteria restano aperti.
