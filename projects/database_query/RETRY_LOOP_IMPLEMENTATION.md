# Database Query Retry Loop - Implementation Summary

**Date**: 2025-10-07
**Status**: ✅ Implemented and Ready for Testing
**Feature**: Auto-correction retry loop with error feedback

---

## Overview

Implementato un sistema di **retry automatico con auto-correzione** per query database tramite MCP. Il workflow analizza errori e corregge la query automaticamente, senza limiti al numero di tentativi.

---

## Come Funziona

### Flusso con Loop

```
1. generate_query
   ↓ Genera JSON query da NL

2. execute_query
   ↓ Esegue via MCP json_query_sse

3. check_result
   ↓ Analizza se successo o errore

4. Conditional routing:
   - has_error = false → synthesize_results → format_output → END
   - has_error = true  → LOOP BACK to generate_query ⟲
```

### Auto-Correzione

Quando si verifica un errore, il nodo `generate_query` riceve:
- `{user_request}` - Richiesta originale dell'utente
- `{generate_query}` - Query fallita del tentativo precedente
- `{check_result}` - Messaggio di errore dettagliato

E può **analizzare l'errore** per generare query corretta.

---

## File Creati

### 1. `PROMPT_CONDENSED.md`
**Scopo**: Schema condensato (~150 linee) per primo tentativo generazione query

**Contenuto**:
- 10 tabelle essenziali (employees, projects, certifications, etc.)
- Foreign Keys principali
- Formato JSON base
- 5 esempi comuni
- Regole critiche e errori comuni

**Uso**: Incluso in workflow node instruction per generazione query.

### 2. `workflows/database_query_with_retry.json`
**Scopo**: Workflow con retry loop e auto-correzione

**Nodi** (5 totali):
1. **generate_query** (supervisor)
   - Prima volta: usa schema condensato
   - Retry: analizza errore precedente e corregge

2. **execute_query** (mcp_tool)
   - Esegue {generate_query} via json_query_sse

3. **check_result** (analyst)
   - Determina has_error: true/false
   - Estrae error_message se presente

4. **synthesize_results** (analyst)
   - Processa risultati successo

5. **format_output** (writer)
   - Formatta risposta finale per utente

**Conditional Edge**:
```json
{
  "from_node": "check_result",
  "conditions": [{
    "field": "custom_metadata.has_error",
    "operator": "equals",
    "value": false,
    "next_node": "synthesize_results"
  }],
  "default": "generate_query"
}
```

Se `has_error = true` → torna a `generate_query` (LOOP!)

### 3. `agents/factory.py` (Modificato)
**Modifiche**:
- Aggiunto `_load_mcp_detailed_prompts()` function
- Carica `/home/mverde/src/taal/json_api/PROMPT.md` completo (370 linee)
- Include nel system prompt del supervisor
- Solo se MCP enabled

**Beneficio**: Supervisor ha context completo del database schema per decisioni intelligenti.

---

## Meccanismo di Auto-Correzione

### Scenario Esempio: Query con Errori

**Tentativo 1** (typo nel nome tabella):
```
User: "Mostrami tutti i dipendenti"

generate_query output:
{"table": "employes", "select": ["*"]}  ❌

execute_query output:
ERROR: relation "employes" does not exist

check_result output:
has_error: true
error_message: relation "employes" does not exist

→ LOOP BACK to generate_query
```

**Tentativo 2** (corregge nome tabella, sbaglia colonna):
```
generate_query riceve:
- user_request: "Mostrami tutti i dipendenti"
- Previous failed query: {"table": "employes", ...}
- Error: relation "employes" does not exist

generate_query instruction include:
"PREVIOUS ATTEMPT FAILED:
Failed query: {generate_query}
Error: {check_result}
ANALYZE AND CORRECT..."

generate_query output:
{"table": "employees", "where": {"dept": "IT"}}  ❌

execute_query output:
ERROR: column "dept" does not exist

check_result output:
has_error: true
error_message: column "dept" does not exist

→ LOOP BACK again
```

**Tentativo 3** (corregge tutto):
```
generate_query riceve errore "column dept does not exist"

generate_query output:
{"table": "employees", "where": {"department_id": 5}}  ✅

execute_query output:
[... results data ...]

check_result output:
has_error: false
row_count: 15

→ Conditional routing: synthesize_results → END
```

---

## Stato del Workflow Durante Loop

```python
# Dopo 3 tentativi
state.completed_nodes = [
    "generate_query",      # Tentativo 1
    "execute_query",
    "check_result",
    "generate_query",      # Tentativo 2 (LOOP)
    "execute_query",
    "check_result",
    "generate_query",      # Tentativo 3 (LOOP)
    "execute_query",
    "check_result",
    "synthesize_results",  # Successo!
    "format_output"
]

state.node_outputs = {
    "generate_query": '{"table":"employees","where":{...}}',  # Ultima versione
    "execute_query": "[...results...]",                       # Ultimo output
    "check_result": "has_error: false\nrow_count: 15"        # Ultimo check
}
```

I nodi **sovrascrivono** il loro output ogni loop. Accessibili via `{node_id}`.

---

## Accesso alle Variabili nel Workflow

Il workflow engine supporta variable substitution in node instructions:

**Variabili Standard**:
- `{user_request}` - Input utente originale
- `{node_id}` - Output di un nodo (es: `{generate_query}`)
- `{state.custom_metadata.key}` - Metadata custom

**Esempio Instruction**:
```
Previous query failed:
Query: {generate_query}
Error: {check_result}

Analyze and correct...
```

L'engine sostituisce automaticamente con valori correnti.

---

## Test Immediato

### Test 1: Query Intenzionalmente Sbagliata

**Modificare** `database_query_with_retry.json` parameter:
```json
"parameters": {
  "user_request": "Mostra dipendenti della tabella employes"  ← typo intenzionale
}
```

**Aspettativa**:
1. Tentativo 1: Genera query con "employes" → ERROR
2. Tentativo 2: Corregge in "employees" → SUCCESS o altro errore
3. Tentativo 3+: Continua finché non funziona

### Test 2: Colonna Inesistente

```json
"parameters": {
  "user_request": "Dipendenti del dipartimento dove dept = IT"  ← "dept" non esiste
}
```

**Aspettativa**:
1. Genera query con campo "dept" → ERROR: column not found
2. Corregge in "department_id" o "department_name" → SUCCESS

---

## Vantaggi del Sistema

✅ **Auto-correzione**: LLM impara dagli errori
✅ **Loop infinito**: Riprova finché non funziona
✅ **Error feedback**: Usa messaggio errore MCP per correggere
✅ **Zero modifiche engine**: Usa conditional routing esistente
✅ **Trasparente**: completed_nodes mostra tutti i tentativi
✅ **Context completo**: Supervisor ha PROMPT.md completo (370 linee)

---

## Limitazioni Attuali

⚠️ **Loop infinito**: Se errore non recuperabile (tabella inesistente nello schema)
⚠️ **Nessun max_attempts**: Loop continua fino a timeout workflow
⚠️ **Cost**: Ogni loop = chiamata LLM
⚠️ **Timeout globale**: Workflow ha timeout (default 120s per nodo)

**NOTA**: Queste limitazioni sono intenzionali per testare il pattern. Max attempts può essere aggiunto successivamente.

---

## Prossimi Passi

1. **Test con query errate** → Verificare loop funziona
2. **Monitorare iterazioni** → Contare quanti tentativi servono in media
3. **Analizzare pattern errori** → Quali errori si auto-correggono meglio
4. **Se funziona bene** → Aggiungere max_attempts configurabile
5. **Ottimizzazione** → Condensare prompt per ridurre token

---

## Come Usare

### Via Workflow Engine

```python
from workflows.registry import get_workflow_registry
from workflows.engine import WorkflowEngine

registry = get_workflow_registry()
workflow = await registry.get_workflow("database_query_with_retry")

engine = WorkflowEngine()
result = await engine.execute_workflow(
    template=workflow,
    user_input="Mostra tutti i dipendenti con certificazioni AWS",
    params={}
)

print(result.final_output)
print(f"Tentativi: {result.node_results}")  # Mostra tutti i loop
```

### Via Supervisor

Il supervisor può decidere autonomamente di usare questo workflow se rileva una database query.

---

## Configurazione

### Timeout per Nodo
Nel JSON workflow, ogni nodo ha `"timeout": <seconds>`:
- `generate_query`: 120s (generazione query complessa)
- `execute_query`: 60s (MCP call)
- `check_result`: 30s (analisi veloce)

### Workflow Trigger Patterns
```json
"trigger_patterns": [
  "database query",
  "query database",
  "search database",
  "find in database"
]
```

Se user input matches → auto-seleziona questo workflow.

---

## Monitoraggio

### Log Output
```
🚀 Starting workflow 'database_query_with_retry'
📍 Executing node 'generate_query' (agent: supervisor)
📍 Executing node 'execute_query' (agent: mcp_tool)
📍 Executing node 'check_result' (agent: analyst)
🔀 Conditional routing: check_result → generate_query  ← LOOP!
📍 Executing node 'generate_query' (agent: supervisor)  ← Retry
...
✅ Workflow completed in 45.2s
```

### State Inspection
```python
print(result.execution_log)  # Tutti gli step
print(len([n for n in result.node_results if n.node_id == "generate_query"]))  # Conta retry
```

---

**Status**: ✅ Ready for Testing
**Implementation**: 100% Complete
**Code Changes**: 1 file modified (factory.py), 3 files created
**Next**: Test with intentionally incorrect queries
