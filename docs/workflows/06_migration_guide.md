# Migration Guide: ReAct → Workflow System

Guida strategica per migrare da ReAct autonomo a Workflow template-based, con focus su **modalità ibride** e **migrazioni parziali**.

## Indice

- [Perché Migrare?](#perché-migrare)
- [Modalità Ibride](#modalità-ibride)
- [Identificare Candidati per Workflow](#identificare-candidati-per-workflow)
- [Migrazione Graduale](#migrazione-graduale)
- [Coesistenza ReAct + Workflow](#coesistenza-react--workflow)
- [Case Studies](#case-studies)
- [Testing della Migrazione](#testing-della-migrazione)
- [Troubleshooting](#troubleshooting)

---

## Perché Migrare?

### Quando ReAct è Meglio

**Rimani con ReAct se**:
- Task unici, non ripetibili
- Esplorazione aperta (ricerca, brainstorming)
- Richieste imprevedibili
- Flessibilità > Consistenza

**Esempio**: "Tell me about the latest AI news" → ReAct decide autonomamente come esplorare.

---

### Quando Workflow è Meglio

**Migra a Workflow se**:
- Task ripetitivi con pattern chiari
- Bisogno di consistenza (report, audit)
- Performance critiche (parallel execution)
- Controllabilità > Creatività
- Integrazione con sistemi esterni (MCP)

**Esempio**: "Generate weekly sales report" → Workflow predefinito: query_db → analyze → report.

---

### Vantaggi Workflow

| Vantaggio | ReAct | Workflow |
|-----------|-------|----------|
| **Consistenza** | ⚠️ Variabile | ✅ Garantita |
| **Performance** | ⏱️ Sequenziale | 🚀 Parallel |
| **Costo LLM** | 💸 Alto (multi-step reasoning) | 💰 Basso (solo exec) |
| **Debugging** | 🔍 Difficile (black box) | ✅ Tracciabile |
| **Controllabilità** | ⚠️ Limitata | ✅ Completa |
| **Creatività** | ✅ Alta | ⚠️ Limitata |

**Conclusione**: **Hybrid mode** combina i vantaggi di entrambi.

---

## Modalità Ibride

Il sistema supporta **4 strategie ibride** per migrazioni parziali.

### 1. Full Hybrid (Auto-detect + Fallback)

**Configurazione**:
```bash
# .env
WORKFLOW_MODE=hybrid
WORKFLOW_AUTO_CLASSIFY=true
WORKFLOW_FALLBACK_TO_REACT=true
```

**Comportamento**:
1. User input → Tentativo auto-match con `trigger_patterns`
2. Match trovato → Esegue workflow template
3. No match → Fallback automatico a ReAct
4. Workflow fallisce → Fallback automatico a ReAct

**Quando usare**:
- Migrazione iniziale
- Testing dei template in produzione
- Massima robustezza

**Pro**:
- ✅ Zero rischio: ReAct è sempre disponibile
- ✅ Graduale: aggiungi template senza modificare codice
- ✅ Safe: errori workflow non bloccano l'utente

**Contro**:
- ⚠️ Overhead: auto-matching su ogni richiesta
- ⚠️ Imprevedibilità: user non sa quale mode verrà usato

**Esempio**:
```python
# User: "Create a report on AI trends"
# → Auto-match: trigger_patterns [".*report.*"]
# → Esegue: report_generation.json

# User: "Tell me a joke"
# → No match
# → Fallback: ReAct mode
```

---

### 2. Selective Hybrid (Whitelist Esplicita)

**Configurazione**:
```bash
WORKFLOW_MODE=template  # Solo template espliciti
WORKFLOW_AUTO_CLASSIFY=false
WORKFLOW_FALLBACK_TO_REACT=true  # Fallback se manca template
```

**Comportamento**:
- Solo task con `workflow_template` esplicito usano workflow
- Altri task → ReAct
- Fallback attivo se template fallisce

**Quando usare**:
- Migrazione controllata
- Workflow critici (compliance, audit)
- A/B testing

**Implementazione**:
```python
# Route layer: decide quale mode usare
@app.post("/invoke")
async def invoke(request: InvokeRequest):
    workflow_tasks = ["generate_report", "analyze_sentiment", "query_database"]

    if request.task_type in workflow_tasks:
        # Use workflow mode
        result = await supervisor.ainvoke({
            "messages": [HumanMessage(content=request.text)],
            "workflow_template": get_template_for_task(request.task_type),
            "workflow_params": request.params
        })
    else:
        # Use ReAct mode
        result = await supervisor.ainvoke({
            "messages": [HumanMessage(content=request.text)]
        })

    return result
```

**Pro**:
- ✅ Controllo totale su cosa usa workflow
- ✅ Facile auditing
- ✅ Graduale: aggiungi task uno alla volta

**Contro**:
- ⚠️ Richiede codice router custom
- ⚠️ Non beneficia di auto-matching

---

### 3. Progressive Hybrid (Task-by-Task)

**Strategia**: Migra task dalla frequenza più alta alla più bassa.

**Steps**:

#### Step 1: Identificare Top 5 Task Frequenti
```bash
# Analizza logs produzione
grep "User request" supervisor.log | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -nr | head -5

# Output:
# 1523 "generate report"
# 876 "analyze sentiment"
# 654 "create newsletter"
# 432 "query database"
# 289 "compare competitors"
```

#### Step 2: Migrare Task #1
```bash
# Crea template per task più frequente
cp workflows/templates/report_generation.json \
   workflows/templates/custom_report.json

# Abilita auto-matching
WORKFLOW_AUTO_CLASSIFY=true

# Aggiungi trigger patterns
{
  "trigger_patterns": [
    ".*generate.*report.*",
    ".*create.*document.*",
    ".*weekly.*summary.*"
  ]
}
```

#### Step 3: Testing A/B (1 settimana)
```python
# Configura split 50/50
import random

if random.random() < 0.5:
    mode = "workflow"
else:
    mode = "react"

result = await supervisor.ainvoke({
    "messages": [...],
    "workflow_mode": mode
})

# Log per confronto
logger.info(f"Mode: {mode}, Latency: {latency}, Cost: {cost}")
```

#### Step 4: Valutare Metriche
```
Metric          | Workflow | ReAct  | Improvement
----------------|----------|--------|------------
Latency         | 12.3s    | 18.7s  | +34%
LLM Cost        | $0.08    | $0.15  | +47%
Consistency     | 95%      | 78%    | +22%
User Satisfaction| 4.6/5   | 4.3/5  | +7%
```

#### Step 5: Rollout 100% Task #1
```bash
# Rimuovi A/B testing, usa workflow per task #1
WORKFLOW_MODE=hybrid
WORKFLOW_AUTO_CLASSIFY=true
```

#### Step 6: Ripetere per Task #2, #3, #4, #5

**Timeline**:
- Week 1-2: Migra task #1 (most frequent)
- Week 3-4: Migra task #2
- Week 5-6: Migra task #3
- Month 2: Migra task #4, #5
- Month 3+: Long tail tasks

**Pro**:
- ✅ Riduzione rischio graduale
- ✅ Validazione incrementale
- ✅ ROI immediato (high-frequency tasks first)

**Contro**:
- ⏱️ Tempo lungo per completare migrazione

---

### 4. A/B Hybrid (Test Comparison)

**Configurazione**:
```python
# services/ab_testing.py
class ABTestingService:
    def __init__(self, split_ratio: float = 0.5):
        self.split_ratio = split_ratio
        self.results = {"workflow": [], "react": []}

    def assign_mode(self, user_id: str) -> str:
        """Consistent assignment based on user_id hash"""
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return "workflow" if hash_val % 100 < self.split_ratio * 100 else "react"

    def log_result(self, mode: str, metrics: dict):
        self.results[mode].append(metrics)

    def compare(self):
        """Statistical comparison of workflow vs react"""
        workflow_latency = np.mean([r["latency"] for r in self.results["workflow"]])
        react_latency = np.mean([r["latency"] for r in self.results["react"]])

        # T-test
        t_stat, p_value = stats.ttest_ind(
            [r["latency"] for r in self.results["workflow"]],
            [r["latency"] for r in self.results["react"]]
        )

        return {
            "workflow_mean": workflow_latency,
            "react_mean": react_latency,
            "improvement": (react_latency - workflow_latency) / react_latency * 100,
            "p_value": p_value,
            "significant": p_value < 0.05
        }
```

**Implementazione**:
```python
ab_service = ABTestingService(split_ratio=0.5)

@app.post("/invoke")
async def invoke(request: InvokeRequest):
    mode = ab_service.assign_mode(request.user_id)

    start = time.time()

    if mode == "workflow":
        result = await supervisor.ainvoke({
            "messages": [...],
            "workflow_template": "report_generation"
        })
    else:
        result = await supervisor.ainvoke({
            "messages": [...]
        })

    latency = time.time() - start

    ab_service.log_result(mode, {
        "latency": latency,
        "cost": calculate_cost(result),
        "user_satisfaction": request.feedback_score
    })

    return result
```

**Dashboard Metriche**:
```python
# Dopo 1000 richieste per group
results = ab_service.compare()

print(f"""
A/B Test Results (n=1000 per group):

Latency:
  Workflow: {results['workflow_mean']:.2f}s
  ReAct:    {results['react_mean']:.2f}s
  Improvement: {results['improvement']:.1f}%
  P-value: {results['p_value']:.4f} {'✅ Significant' if results['significant'] else '⚠️ Not significant'}

Cost:
  Workflow: ${results['workflow_cost']:.2f}
  ReAct:    ${results['react_cost']:.2f}
  Savings: {results['cost_savings']:.1f}%
""")
```

**Pro**:
- ✅ Validazione statistica
- ✅ Consistent assignment (same user → same mode)
- ✅ Dati oggettivi per decisione

**Contro**:
- ⚠️ Richiede volume traffico sufficiente
- ⚠️ Complessità infrastruttura

---

## Identificare Candidati per Workflow

### Checklist: Task è Candidato?

**✅ Migra a Workflow se:**

1. **Ripetitività**: Task si ripete con pattern simili
   - ✅ "Generate weekly sales report"
   - ❌ "Explore new market opportunities"

2. **Struttura Chiara**: Steps prevedibili
   - ✅ Research → Analyze → Write
   - ❌ "Help me brainstorm ideas"

3. **Consistenza Richiesta**: Output deve essere uniforme
   - ✅ Compliance reports, audit logs
   - ❌ Creative writing

4. **Performance Critica**: Latenza importante
   - ✅ Real-time dashboards
   - ❌ Background batch jobs

5. **Integrazione Dati**: Richiede DB/API esterni
   - ✅ Query database + analyze
   - ❌ Solo LLM reasoning

6. **Parallelizzabile**: Steps indipendenti
   - ✅ Compare 3 competitors (parallel)
   - ❌ Sequential storytelling

7. **Volume Alto**: Eseguito frequentemente
   - ✅ >50 volte/settimana
   - ❌ Rare ad-hoc requests

**Scoring System**:
```
Score = (Ripetitività × 3) + (Struttura × 2) + (Consistenza × 3) +
        (Performance × 2) + (Integrazione × 2) + (Parallelismo × 1) + (Volume × 3)

Migra se Score >= 12
```

---

### Esempi Scoring

#### Task 1: "Generate Weekly Sales Report"

| Criterio | Score (0-2) | Ragionamento |
|----------|-------------|--------------|
| Ripetitività | 2 | Eseguito ogni settimana |
| Struttura | 2 | Query DB → Analyze → Report |
| Consistenza | 2 | Format uniforme richiesto |
| Performance | 1 | Non critico (weekly batch) |
| Integrazione | 2 | Richiede DB query (MCP) |
| Parallelismo | 0 | Sequential |
| Volume | 1 | ~52/anno (basso) |

**Total**: (2×3) + (2×2) + (2×3) + (1×2) + (2×2) + (0×1) + (1×3) = **25** → ✅ **Migra**

---

#### Task 2: "Analyze Customer Sentiment"

| Criterio | Score (0-2) | Ragionamento |
|----------|-------------|--------------|
| Ripetitività | 2 | Ogni feedback ricevuto |
| Struttura | 2 | Analyze → Route → Respond |
| Consistenza | 2 | Risposte devono seguire policy |
| Performance | 2 | Real-time (customer waiting) |
| Integrazione | 1 | Può salvare in DB |
| Parallelismo | 0 | Sequential |
| Volume | 2 | 100+ al giorno |

**Total**: (2×3) + (2×2) + (2×3) + (2×2) + (1×2) + (0×1) + (2×3) = **28** → ✅ **Migra**

---

#### Task 3: "Brainstorm Marketing Ideas"

| Criterio | Score (0-2) | Ragionamento |
|----------|-------------|--------------|
| Ripetitività | 0 | Sempre diverso |
| Struttura | 0 | Open-ended exploration |
| Consistenza | 0 | Creatività richiesta |
| Performance | 0 | Non critico |
| Integrazione | 0 | No dati esterni |
| Parallelismo | 0 | Single LLM call |
| Volume | 0 | Rare ad-hoc |

**Total**: **0** → ❌ **Rimani ReAct**

---

## Migrazione Graduale

### Phase 1: Audit (Week 1-2)

**Obiettivo**: Capire come viene usato il sistema.

**Steps**:

1. **Abilita logging**:
```python
# agents/supervisor.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def supervisor_node(state: SupervisorState):
    user_input = state["messages"][0].content

    logger.info(f"[AUDIT] User request: {user_input}")
    logger.info(f"[AUDIT] Timestamp: {datetime.now()}")
    logger.info(f"[AUDIT] Mode: react")

    # ... existing logic ...
```

2. **Colleziona 2 settimane di logs**:
```bash
# Estrai task patterns
cat supervisor.log | grep "\[AUDIT\]" > audit_data.log

# Analyze patterns
python scripts/analyze_audit.py audit_data.log
```

3. **Script analisi**:
```python
# scripts/analyze_audit.py
import re
from collections import Counter

def extract_task_intent(text):
    """Extract task type from user request"""
    patterns = {
        "report": r".*report.*|.*summary.*",
        "analysis": r".*analy[sz]e.*|.*compare.*",
        "query": r".*query.*|.*search.*|.*find.*",
        "content": r".*write.*|.*create.*|.*generate.*"
    }

    for task_type, pattern in patterns.items():
        if re.search(pattern, text.lower()):
            return task_type

    return "other"

with open("audit_data.log") as f:
    tasks = [extract_task_intent(line) for line in f]

counter = Counter(tasks)
print("Task Distribution:")
for task, count in counter.most_common():
    print(f"  {task}: {count} ({count/len(tasks)*100:.1f}%)")
```

**Output**:
```
Task Distribution:
  report: 523 (34.2%)
  analysis: 387 (25.3%)
  content: 298 (19.5%)
  query: 187 (12.2%)
  other: 135 (8.8%)
```

**Decisione**: Migra top 3 task types (report, analysis, content).

---

### Phase 2: Pilot (Week 3-4)

**Obiettivo**: Testare 1 workflow con utenti reali.

**Steps**:

1. **Scegli task pilota**: "report" (34.2% traffico)

2. **Crea template**:
```bash
cp workflows/templates/report_generation.json \
   workflows/templates/pilot_report.json
```

3. **Abilita per subset utenti** (10% beta users):
```python
BETA_USERS = ["user123", "user456", "user789"]

@app.post("/invoke")
async def invoke(request: InvokeRequest):
    if request.user_id in BETA_USERS:
        mode = "hybrid"  # Use workflow if matched
    else:
        mode = "react"  # Keep existing behavior

    result = await supervisor.ainvoke({
        "messages": [...],
        "workflow_mode": mode
    })
```

4. **Colleziona feedback**:
```python
@app.post("/feedback")
async def feedback(user_id: str, rating: int, comment: str):
    await db.save_feedback({
        "user_id": user_id,
        "rating": rating,
        "comment": comment,
        "mode": get_user_mode(user_id)  # "workflow" or "react"
    })
```

5. **Valuta dopo 2 settimane**:
```sql
SELECT
  mode,
  AVG(rating) as avg_rating,
  COUNT(*) as n_feedback
FROM feedback
WHERE timestamp > NOW() - INTERVAL '2 weeks'
GROUP BY mode;
```

**Risultati**:
```
mode      | avg_rating | n_feedback
----------|------------|------------
workflow  | 4.7        | 47
react     | 4.4        | 412
```

**Decisione**: ✅ Workflow performa meglio → Rollout 100%.

---

### Phase 3: Rollout (Week 5-8)

**Obiettivo**: Migrare task pilota a 100% utenti.

**Steps**:

1. **Week 5**: 25% traffico
```python
if random.random() < 0.25:
    mode = "hybrid"
```

2. **Week 6**: 50% traffico
3. **Week 7**: 75% traffico
4. **Week 8**: 100% traffico

5. **Monitor metriche**:
```python
# services/monitoring.py
from prometheus_client import Counter, Histogram

workflow_requests = Counter("workflow_requests_total", "Total workflow requests")
workflow_latency = Histogram("workflow_latency_seconds", "Workflow latency")
workflow_errors = Counter("workflow_errors_total", "Total workflow errors")

async def workflow_executor(state):
    workflow_requests.inc()

    start = time.time()
    try:
        result = await engine.execute_workflow(...)
        workflow_latency.observe(time.time() - start)
        return result
    except Exception as e:
        workflow_errors.inc()
        raise
```

6. **Alerting**:
```yaml
# prometheus/alerts.yml
groups:
  - name: workflow_alerts
    rules:
      - alert: WorkflowErrorRateHigh
        expr: rate(workflow_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Workflow error rate > 5%"

      - alert: WorkflowLatencyHigh
        expr: histogram_quantile(0.95, workflow_latency_seconds) > 30
        for: 10m
        annotations:
          summary: "P95 latency > 30s"
```

---

### Phase 4: Iterate (Month 2-3)

**Obiettivo**: Migrare task #2, #3, #4.

**Steps**:
- Ripeti Phase 2-3 per ogni task type
- Aggiungi template gradualmente
- Monitor aggregate metrics

**Timeline**:
```
Month 1: Task #1 (report) → 34% traffico migrato
Month 2: Task #2 (analysis) → 59% traffico migrato
Month 3: Task #3 (content) → 79% traffico migrato
Month 4+: Long tail tasks → 90%+ traffico migrato
```

---

## Coesistenza ReAct + Workflow

### Best Practices

#### 1. Separare Logs per Mode

```python
# utils/logging.py
import logging

def get_logger(mode: str):
    logger = logging.getLogger(f"cortex.{mode}")
    handler = logging.FileHandler(f"logs/{mode}.log")
    logger.addHandler(handler)
    return logger

# Usage
workflow_logger = get_logger("workflow")
react_logger = get_logger("react")

workflow_logger.info("Executing template: report_generation")
react_logger.info("ReAct decision: call researcher agent")
```

#### 2. Metriche Separate

```python
# services/metrics.py
from prometheus_client import Counter, Histogram

# Workflow metrics
workflow_requests = Counter("workflow_requests_total", ["template_name"])
workflow_latency = Histogram("workflow_latency_seconds", ["template_name"])

# ReAct metrics
react_requests = Counter("react_requests_total")
react_steps = Histogram("react_reasoning_steps", "Number of ReAct steps")

# Comparative metrics
mode_comparison = Counter("mode_comparison_total", ["mode", "outcome"])
```

#### 3. Tracing Differenziato

```python
# LangSmith tracing
from langsmith import traceable

@traceable(name="workflow_execution", metadata={"mode": "workflow"})
async def execute_workflow(...):
    ...

@traceable(name="react_execution", metadata={"mode": "react"})
async def execute_react(...):
    ...
```

#### 4. Fallback Graceful

```python
async def workflow_executor(state: SupervisorState):
    try:
        result = await engine.execute_workflow(...)

        if not result.success:
            logger.warning(f"Workflow failed: {result.error}")

            if settings.workflow_fallback_to_react:
                logger.info("Falling back to ReAct mode")
                return {"workflow_template": None}  # Trigger ReAct
            else:
                raise ValueError(f"Workflow failed: {result.error}")

        return {"messages": [AIMessage(content=result.final_output)]}

    except Exception as e:
        logger.error(f"Workflow exception: {e}")

        if settings.workflow_fallback_to_react:
            return {"workflow_template": None}
        else:
            raise
```

---

## Case Studies

### Case Study 1: E-commerce Weekly Reports

**Scenario**: E-commerce company generava 52 report settimanali (sales, inventory, customer behavior).

**Before (ReAct)**:
- Latency: 25-40s (variable)
- Cost: $0.18/report (multiple LLM calls)
- Consistency: 70% (format varied)
- Human review: 30% reports required edits

**Migration**:
1. Week 1-2: Created `weekly_sales_report.json` template
2. Week 3-4: Pilot con 3 report types
3. Week 5-8: Rollout graduale

**After (Workflow)**:
- Latency: 14s (consistent)
- Cost: $0.07/report (fixed path)
- Consistency: 98%
- Human review: 5%

**ROI**:
```
Annual savings = 52 reports × ($0.18 - $0.07) = $5.72
Time savings = 52 × (30s) × (30% review rate) = 468 minutes/year
```

**Lesson**: Workflow ideale per report strutturati ripetitivi.

---

### Case Study 2: Customer Support Sentiment Routing

**Scenario**: Analyze customer feedback e route a team appropriato.

**Before (ReAct)**:
- Latency: 8-15s
- Misrouting: 12% (wrong team)
- Escalation rate: 8%

**Migration**:
1. Created `sentiment_routing.json` con conditional edges
2. Pilot con 10% traffico (A/B test)
3. Validazione accuracy: 94% correct routing

**After (Workflow)**:
- Latency: 4s (parallel analysis)
- Misrouting: 3%
- Escalation rate: 3%
- Customer satisfaction: +0.4 points

**Lesson**: Conditional routing riduce errori in task classification.

---

### Case Study 3: Content Repurposing (Blog → Social)

**Scenario**: Convertire blog posts in Twitter thread + LinkedIn + Summary.

**Before (ReAct, Sequential)**:
- Latency: 60s (sequential: analyze → tweet → linkedin → summary)
- Cost: $0.22/conversion

**Migration**:
1. Created `content_repurposing.json` con parallel_group
2. Pilot con 5 blog posts

**After (Workflow, Parallel)**:
- Latency: 18s (parallel execution)
- Cost: $0.19/conversion
- Speedup: **70%**

**Lesson**: Parallel execution ideal per task indipendenti.

---

## Testing della Migrazione

### Test Checklist

#### Unit Tests

```python
# tests/test_migration.py
import pytest
from agents.workflow_supervisor import create_workflow_supervisor

class TestMigration:
    @pytest.mark.asyncio
    async def test_react_mode_still_works(self):
        """Ensure ReAct mode unchanged"""
        supervisor = create_workflow_supervisor()

        result = await supervisor.ainvoke({
            "messages": [HumanMessage(content="Tell me about AI")],
            "workflow_mode": "react"  # Force ReAct
        })

        assert result["messages"][-1].content

    @pytest.mark.asyncio
    async def test_hybrid_mode_auto_detect(self):
        """Test auto-matching workflow"""
        supervisor = create_workflow_supervisor()

        result = await supervisor.ainvoke({
            "messages": [HumanMessage(content="Generate sales report")],
            "workflow_mode": "hybrid"
        })

        # Should use workflow mode
        assert "workflow_name" in result

    @pytest.mark.asyncio
    async def test_fallback_to_react(self):
        """Test fallback quando workflow non match"""
        supervisor = create_workflow_supervisor()

        result = await supervisor.ainvoke({
            "messages": [HumanMessage(content="Random unstructured query")],
            "workflow_mode": "hybrid"
        })

        # Should fallback to ReAct
        assert result["messages"][-1].content
```

#### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_migration(self):
    """Simulate real migration scenario"""

    # Step 1: ReAct baseline
    result_react = await supervisor.ainvoke({
        "messages": [HumanMessage(content="Create report")],
        "workflow_mode": "react"
    })

    # Step 2: Workflow mode
    result_workflow = await supervisor.ainvoke({
        "messages": [HumanMessage(content="Create report")],
        "workflow_template": "report_generation"
    })

    # Both should succeed
    assert result_react["messages"]
    assert result_workflow["messages"]

    # Workflow should be faster (mock timing)
    assert result_workflow["execution_time"] < result_react["execution_time"]
```

#### Load Tests

```python
# tests/load_test_migration.py
import asyncio
from locust import HttpUser, task, between

class MigrationLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def react_mode(self):
        """70% traffico ReAct (pre-migration)"""
        self.client.post("/invoke", json={
            "user_input": "Analyze market trends",
            "workflow_mode": "react"
        })

    @task(1)
    def workflow_mode(self):
        """30% traffico Workflow (post-migration)"""
        self.client.post("/invoke", json={
            "user_input": "Generate weekly report",
            "workflow_mode": "hybrid"
        })
```

Run:
```bash
locust -f tests/load_test_migration.py --host http://localhost:8000
```

---

## Troubleshooting

### Issue 1: Auto-match Non Funziona

**Sintomo**: Template esiste ma viene usato ReAct.

**Debug**:
```python
# Test trigger pattern
import re

pattern = ".*report.*"
user_input = "Please generate a sales report"

match = re.search(pattern, user_input.lower())
print(f"Match: {match}")  # Should be <re.Match object>

# If None, pattern è sbagliato
```

**Soluzioni**:
1. Verifica `trigger_patterns` in JSON template
2. Test pattern su [regex101.com](https://regex101.com/)
3. Aggiungi logging:
```python
# workflows/registry.py
async def match_template(self, user_input: str):
    logger.debug(f"Matching input: '{user_input}'")

    for template in self._templates.values():
        for pattern in template.trigger_patterns:
            logger.debug(f"Testing pattern: '{pattern}'")
            if re.search(pattern, user_input.lower()):
                logger.info(f"✅ Matched: {template.name}")
                return template

    logger.warning("❌ No template matched")
    return None
```

---

### Issue 2: Fallback Loop Infinito

**Sintomo**: Workflow fallisce → fallback ReAct → fallisce → loop.

**Debug**:
```python
# Check fallback count
if state.get("fallback_count", 0) >= 3:
    logger.error("Max fallback attempts reached")
    raise ValueError("Both workflow and ReAct failed")
```

**Soluzione**:
```python
async def workflow_executor(state: SupervisorState):
    fallback_count = state.get("fallback_count", 0)

    try:
        result = await engine.execute_workflow(...)

        if not result.success and settings.workflow_fallback_to_react:
            return {
                "workflow_template": None,
                "fallback_count": fallback_count + 1
            }
    except Exception:
        return {
            "workflow_template": None,
            "fallback_count": fallback_count + 1
        }
```

---

### Issue 3: Performance Degradation Post-Migration

**Sintomo**: Latency aumenta dopo migrazione.

**Debug**:
```bash
# Compare latency distributions
python scripts/compare_latency.py --before react.log --after workflow.log
```

**Possibili cause**:
1. **Auto-matching overhead**: Regex check su ogni richiesta
   - **Fix**: Cache compiled regex patterns
   ```python
   self._compiled_patterns = {
       name: [re.compile(p) for p in t.trigger_patterns]
       for name, t in self._templates.items()
   }
   ```

2. **Template loading**: Carica JSON ogni volta
   - **Fix**: Singleton registry
   ```python
   _registry_instance = None

   def get_workflow_registry():
       global _registry_instance
       if _registry_instance is None:
           _registry_instance = WorkflowRegistry()
           _registry_instance.load_templates()
       return _registry_instance
   ```

3. **Network latency (MCP tools)**:
   - **Fix**: Connection pooling
   ```python
   # utils/mcp_client.py
   class MCPClient:
       def __init__(self):
           self._session = httpx.AsyncClient(
               limits=httpx.Limits(max_connections=10),
               timeout=30.0
           )
   ```

---

### Issue 4: Inconsistent Results Workflow vs ReAct

**Sintomo**: Workflow produce output diverso da ReAct per stesso task.

**Debug**:
```python
# Run side-by-side comparison
results = await asyncio.gather(
    supervisor.ainvoke({"messages": [...], "workflow_mode": "react"}),
    supervisor.ainvoke({"messages": [...], "workflow_template": "report_generation"})
)

compare_outputs(results[0], results[1])
```

**Soluzioni**:
1. **Adjust instructions**: Workflow instructions troppo rigide
   - Aggiungi flexibility nel prompt

2. **Agent selection**: Workflow usa agent diverso
   - Verifica template `"agent": "writer"` vs ReAct choice

3. **Context loss**: Workflow perde context tra nodi
   - Usa `{previous_output}` in instructions

---

## Prossimi Passi

- [← MCP Integration](03_mcp_integration.md) - Integra database e API
- [← Visual Diagrams](04_visual_diagrams.md) - Diagrammi architettura
- [← Cookbook](05_cookbook.md) - 15+ esempi pratici
- [← Creating Templates](01_creating_templates.md) - Crea workflow custom

---

**Best Practice Finale**: Inizia con **hybrid mode** + **fallback abilitato**. Migra gradualmente task ad alto volume. Monitor sempre.

---

**Documentazione aggiornata**: 2025-01-06
