# Plan: Allineare gate documentale, installer e contratti del runtime

ANALYSIS: COMPLETE
RETRIAGE: NO

## Agent execution header
- `PLAN_STATUS: IN_PROGRESS`
- `EXECUTION_READINESS: READY`
- `EXECUTION_SCOPE: FULL_PLAN`
- `CURRENT_REQ: REQ-2.1.1`
- `NEXT_ACTION: implement Phase 2 REQ-2.1.1 through REQ-2.1.4, verify, review, and commit`
- `COMPLETION_ALLOWED: NO`

## 1. Objective

Correggere le lacune del gate deterministico (`check`), le ambiguità dell'installer e le incongruenze tra documentazione e comportamento emerse dall'analisi del repository. Il risultato atteso è un runtime che non dichiari più garanzie che non mantiene: i documenti modificati vengono validati, la mappa e l'index non possono restare incompleti senza segnalazione, `--warn-only` è davvero non bloccante, l'installazione è transazionale e sicura rispetto ai symlink, e la documentazione descrive il comportamento reale. Il piano mantiene le dipendenze a sola standard library e non introduce nuovi provider o modalità agentiche.

## 2. Context and constraints

- **Evidenza autoritativa**: analisi del repository corrente, test suite esistente (80 test verdi), riproduzioni effettuate su: `check` con documenti modificati, cancellazione di `docs/index.md`, documenti non registrati, pattern di mappa invalidi con `--warn-only`, `package-lock.json`, symlink, runtime installato, `fnmatch` e repository senza commit.
- **Percorsi chiave già identificati**: runtime deterministico in `skill/codebase-analysis-ai/scripts/`; asset in `skill/codebase-analysis-ai/assets/`; installer in `install.py` e `project_installer.py`; contratti in `references/`; test in `tests/`.
- **Decisioni confermate** (non riaprire senza nuova evidenza o richiesta esplicita):
  1. La validazione dei link è read-only: va eseguita anche sui documenti modificati; la policy "manuale = valido" continua a impedire riscritture e aggiornamenti automatici degli hash, non la validazione.
  2. `check` segnala come errore i documenti registrati mancanti, `docs/index.md` presente ma non registrato e i documenti attivi `docs/**/*.md` non registrati. Sono esenti `docs/_meta/**` e `docs/_archive/**`; il root `README.md` non è obbligatorio nella mappa.
  3. `--warn-only` copre ogni fallimento di `check`, inclusi errori Git, mappa e I/O. Gli altri comandi mantengono il contratto di uscita attuale.
  4. Su `--json`, ogni fallimento di `check` produce un report JSON leggibile su stdout, oltre al messaggio su stderr.
  5. L'installer di progetto rifiuta target e parent directory symlink che escono dal repository.
  6. `setup-state` eseguito dal runtime installato riporta `unverified` per gli elementi di cui non ha gli asset attesi, invece di dichiararli `managed`; dal skill bundle continua il confronto completo.
  7. Il glob engine è interno, senza nuove dipendenze: `*` e `?` non attraversano `/`, `**` sì, `**/` corrisponde a zero o più directory.
  8. `auditOnlyPatterns` viene rimosso da schema, validazione e documentazione; le mappe esistenti che lo contengono continuano a caricarsi (chiave ignorata).
  9. `docs/_meta/state.json` diventa opzionale e informativo; non è più richiesto nei passi obbligatori di bootstrap/migrate.
  10. Il workflow GitHub resta non bloccante per scelta di prodotto; viene corretta l'annotation, non introdotto un gate bloccante.
  11. Versione minima Python supportata: 3.9. La CI del repository copre 3.9 e 3.12.
  12. Nessuna nuova dipendenza esterna; restano solo standard library e Git.
- **Vincoli**:
  - Non rompere la compatibilità di caricamento delle mappe esistenti.
  - Non riscrivere il contenuto dei documenti manuali.
  - Non eliminare file utente durante l'installazione.
  - Ogni cambiamento di comportamento deve avere un test di regressione.
- **Fuori scope**:
  - Formati e capacità native dei singoli host (Codex, Claude, Gemini, Copilot).
  - Nuove modalità agentiche o nuovi comandi oltre a quelli necessari al piano.
  - Refactoring estetico non richiesto dai requisiti.
  - Modifica della tassonomia dei documenti o del contratto JSON degli analyzer.

## 3. Phase 1 — Correttezza del check e semantica dell'impatto

### 3.1 Gate documentale e raccolta cambiamenti

- [x] REQ-1.1.1 Validazione dei documenti modificati: un cambiamento che tocca solo `docs/**` con un link rotto produce un errore bloccante in `check`/CI; contenuto e hash del documento restano invariati.
- [x] REQ-1.1.2 Esistenza e index: la cancellazione di un documento registrato, la cancellazione di `docs/index.md` o la presenza di `docs/index.md` non registrato producono un errore esplicito.
- [x] REQ-1.1.3 Copertura della mappa: ogni documento attivo `docs/**/*.md` non registrato produce un errore di copertura, con esenzione per `docs/_meta/**` e `docs/_archive/**`; le mappe legacy continuano a caricarsi.
- [x] REQ-1.1.4 Delete e rename: i path sorgente rimossi o rinominati non vengono più classificati come `Unmapped source`; restano soggetti a manutenzione della mappa quando erano mappati, e il nuovo path continua a essere verificato.
- [x] REQ-1.1.5 Repository senza commit: `check --mode working-tree` funziona in un repository senza HEAD; gli OID di push nulli sono riconosciuti sia a 40 sia a 64 caratteri.
- [x] REQ-1.1.6 Contratto di errore: `--warn-only` restituisce 0 per ogni fallimento di `check`, gli errori di mappa interrompono l'analisi prima dell'impact resolution, e `--json` emette sempre un report JSON valido senza traceback.

**Verifica fase**
- I test di regressione dei cinque scenari (link rotto in docs-only, index cancellato, documento non registrato, pattern invalido con `--warn-only`, repo senza commit) passano.
- La suite esistente passa senza modifiche non intenzionali.
- `check --json` su ogni failure path è deserializzabile con `json.loads`.

## 4. Phase 2 — Sicurezza e trasparenza dell'installer

### 4.1 Installazione transazionale e stato reale

- [ ] REQ-2.1.1 Installazione transazionale: `install.py` esegue il preflight di skill e componenti prima di qualunque scrittura, valida il project root, ripristina file e permessi in caso di errore e termina con un messaggio controllato anziché un traceback.
- [ ] REQ-2.1.2 Contenimento symlink: tutti i target di progetto (runtime, hook, workflow, regole agente) rifiutano target o parent symlink che risolvono fuori dal repository, con lo stesso livello di protezione già presente per la skill.
- [ ] REQ-2.1.3 `setup-state` veritiero: dal runtime installato, adapter, hook e workflow risultano `unverified` quando gli asset attesi non sono disponibili; il runtime resta `unverified` e il skill bundle mantiene il confronto completo.
- [ ] REQ-2.1.4 Proprietà dei file gestiti: il comportamento di aggiornamento di skill e runtime è documentato e testato come unità gestita dal marker; i file extra restano preservati o segnalati, e un target privo di marker non viene sovrascritto silenziosamente.

**Verifica fase**
- Un conflitto su un hook o workflow non lascia la skill installata e non produce traceback.
- Un symlink esterno su `.githooks`, `tools` o `.github` viene rifiutato senza scritture fuori dal repository.
- `setup-state` dal runtime installato non riporta mai `managed` un componente modificato privo di asset di confronto.
- I test di idempotenza e rollback esistenti continuano a passare.

## 5. Phase 3 — Matching e discovery coerenti

### 5.1 Pattern, rilevanza e perimetro

- [ ] REQ-3.1.1 Semantica glob: `ignorePatterns` e `sourcePatterns` usano lo stesso motore; `src/*.py` non corrisponde a `src/a/b.py`, `src/**` sì, `**/` corrisponde anche a zero directory; i default continuano a funzionare.
- [ ] REQ-3.1.2 Rilevanza delle sorgenti: nuovi file infrastructure, mobile, frontend e statici supportati vengono segnalati se non mappati; lockfile e output generati non vengono segnalati; i nomi tipo `Dockerfile` sono riconosciuti senza distinzione di case.
- [ ] REQ-3.1.3 Traversal limitato: `detect` e `docs-state` non discendono in `node_modules`, `.git`, `target`, `dist`, `build`, `vendor`, `coverage`, `out`, `bin`, `obj`, `.next`, `.angular` e directory equivalenti; il costo resta proporzionale ai file ispezionati, non all'intero albero.
- [ ] REQ-3.1.4 Preflight path-aware: `.html` e `.txt` contano come documentazione solo in directory documentali, alla root o con nomi canonici; un `src/index.html` non rende `docs-state` “present”.

**Verifica fase**
- I test sui glob coprono `*`, `?`, `**`, `**/` e pattern con estensione.
- Un `package-lock.json` modificato non produce `unmappedFiles`.
- Un `.tf` o `.dart` nuovo non mappato viene segnalato.
- Un albero di test con una directory esclusa molto popolata non viene attraversato.
- Un progetto con solo `src/index.html` riporta `documentationState: none`.

## 6. Phase 4 — Automazione, contratti e documentazione

### 6.1 Messaggi e workflow

- [ ] REQ-4.1.1 Messaggi accurati: il pre-push riporta la causa reale senza affermare sempre “hash stale”; il workflow emette l'annotation di warning solo quando il report contiene almeno un'incoerenza e non ne emette in caso di successo; la documentazione non chiama più il workflow “gate” bloccante.

### 6.2 Contratti e manutenzione

- [ ] REQ-4.2.1 Contratti morti rimossi: `auditOnlyPatterns` non è più validato né documentato, `state.json` è opzionale/informativo e non obbligatorio, e le mappe esistenti restano compatibili.
- [ ] REQ-4.2.2 Pulizia e unificazione: rimozione di codice morto (`_parse_name_status`, `update_managed_block` non usato in produzione, `create_empty_map`) e delle fixture non referenziate; costanti e logica del default branch condivise tra setup e installer.
- [ ] REQ-4.2.3 Documentazione allineata: README e reference descrivono fedelmente installer, `--warn-only`, `validate-docs` repository-relative, `setup-state`, supporto per tipologia di repository e versione minima Python; `validate-docs` rifiuta path assoluti e segmenti `..`.

### 6.3 CI del repository

- [ ] REQ-4.3.1 CI interna: un workflow del repository esegue la suite su Python 3.9 e 3.12 a ogni push e pull request; un test fallito blocca il workflow.

**Verifica fase**
- Un run pulito del workflow non produce annotation; un run con link rotto sì.
- `rg "auditOnlyPatterns|state.json"` non trova più riferimenti obbligatori o di validazione.
- `validate-docs` con path assoluto interno al repository fallisce con `path must be repository-relative`.
- La matrice CI 3.9/3.12 è verde.
- Le affermazioni del README sono verificabili dai test o dai comandi documentati.

## 7. Commit order

1. `fix(check): validate changed docs, enforce map coverage and robust failures`
2. `fix(installer): transactional installs, symlink containment and truthful setup state`
3. `fix(discovery): glob semantics, source relevance and bounded traversal`
4. `chore(automation,docs): accurate warnings, remove dead contracts and add repository CI`

Ogni fase produce un commit atomico solo dopo il completamento di tutti i suoi REQ-ID, delle verifiche e dell'audit finale.

## 8. Exit criteria

- [ ] Tutti i REQ-ID attivi sono `[x]` con la verifica di fase soddisfatta.
- [ ] `python3 -m unittest discover -s tests -p "test_*.py"` passa su Python 3.9 e 3.12.
- [ ] Le riproduzioni dell'analisi iniziale producono il nuovo esito atteso: docs-only con link rotto → errore; index cancellato → errore; documento non registrato → errore; pattern invalido con `--warn-only` → 0 con JSON; `package-lock.json` → ignorato; symlink esterno → rifiutato; runtime installato modificato → `unverified`.
- [ ] Nessuna scrittura fuori dal repository è possibile tramite target symlink dell'installer.
- [ ] Non restano riferimenti a contratti rimossi o fixture/codice morto.
- [ ] Le affermazioni di README e reference sono coerenti con il comportamento osservato e coperte da test.
- [ ] Nessuna nuova dipendenza esterna oltre a Git e standard library.

## 9. Risks and mitigations

- **Nuovi errori su repository esistenti con documenti non registrati**: messaggio esplicito con path e azione richiesta; `--warn-only` disponibile per rollout graduale; esenzioni per `_meta` e `_archive`.
- **Link rotti preesistenti nei documenti modificati**: il gate li segnala senza riscrivere nulla; la correzione resta manuale o delegata a `update`.
- **Cambio della semantica glob**: i pattern default vengono convertiti e testati; eventuali pattern utente che dipendevano da `*` attraverso `/` vanno resi espliciti con `**`.
- **Transazione dell'installer**: snapshot e rollback coprono skill, runtime, hook, workflow e `core.hooksPath`; test con fallimento iniettato.
- **`setup-state` più conservativo**: dal runtime installato alcune verifiche risultano `unverified`; la documentazione indica di usare il skill bundle per il setup discovery.
- **Rimozione di `auditOnlyPatterns`/`state.json`**: compatibilità in lettura garantita; nessuna migrazione dati necessaria.

## 10. Execution instructions

- Il piano è il prompt operativo e la fonte di verità durante l'esecuzione.
- Alla ricezione di un'intenzione di esecuzione, eseguire lo scope richiesto; senza scope più stretto, eseguire tutti i REQ-ID attivi residui.
- Iniziare dal primo REQ-ID attivo non completato nell'ordine del piano, dopo la validazione di lifecycle e struttura.
- Non fermarsi dopo analisi, inventario, preflight o validazione quando i prerequisiti di esecuzione sono soddisfatti.
- Non saltare un REQ-ID attivo e non marcarlo completato senza implementazione, verifica, review ed evidenza.
- Se il lavoro è bloccato, registrare blocker, evidenza, risoluzione richiesta e azione di ripresa; REQ-ID, fase e piano restano incompleti.
- Il piano è completo solo quando ogni REQ-ID attivo e ogni exit criterion sono completi ed evidenziati.
- Ogni fase deve produrre un risultato osservabile e una verifica che lo dimostri; la validazione finale deve dimostrare l'obiettivo complessivo, non solo i REQ-ID completati.
- Per operazioni rischiose o che possono fallire parzialmente (installer, migrazione della mappa), documentare una procedura di retry o recovery sicura.

## 11. Triage outcome

- Consolidation: 0 micro-task consolidati; i 19 REQ-ID erano già raggruppati per esito verificabile.
- Structure: piano single-file. Quattro fasi coese, massimo 6 REQ-ID per fase; la separazione in `spec.md`/`plan.md`/`tasks.md` non ridurrebbe il context drift.
- Reusable review pattern: nessun template creato; le verifiche di fase sono specifiche e non ripetute.
- Active REQ-ID count: 19.
- Sub-phase split: nessuno necessario.
- Final `RETRIAGE`: NO.
- Execution readiness: `READY` (`ANALYSIS: COMPLETE`, `RETRIAGE: NO`).
