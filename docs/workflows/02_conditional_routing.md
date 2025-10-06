# Guida al Conditional Routing Avanzato

## Indice

- [Concetti Base](#concetti-base)
- [Operatori Disponibili](#operatori-disponibili)
- [Pattern Avanzati](#pattern-avanzati)
- [Popolare Metadata](#popolare-metadata-per-routing)
- [Debug e Testing](#debug-conditional-routing)

---

## Concetti Base

### Cos'è il Conditional Routing?

Permette al workflow di **prendere decisioni** basandosi sullo stato di esecuzione:

```
      ┌─────────────┐
      │   analyze   │
      └──────┬──────┘
             │
      ┌──────▼──────┐
      │ Evaluate:   │
      │ score > 0.7?│
      └──┬─────┬────┘
         │     │
    YES  │     │ NO
         │     │
    ┌────▼─┐ ┌▼────┐
    │green │ │ red  │
    │path  │ │path  │
    └──────┘ └──────┘
```

### State Object

Durante l'esecuzione, il workflow mantiene uno **state** con:

```python
class WorkflowState:
    workflow_name: str
    current_node: str
    completed_nodes: List[str]
    node_outputs: Dict[str, str]        # Output di ogni nodo

    # Metadata per conditional routing
    sentiment_score: float              # 0.0 - 1.0
    content_length: int                 # Lunghezza output
    custom_metadata: Dict[str, Any]     # Dati personalizzati

    workflow_params: Dict[str, Any]     # Parametri utente
```

---

## Operatori Disponibili

### Operatori Numerici

```json
{
  "field": "sentiment_score",
  "operator": ">",
  "value": 0.7,
  "next_node": "positive_handling"
}
```

**Supportati**: `>`, `<`, `>=`, `<=`, `equals`

**Esempi**:

```json
// Score alto
{"field": "sentiment_score", "operator": ">=", "value": 0.8}

// Lunghezza minima
{"field": "content_length", "operator": ">", "value": 1000}

// Esatta corrispondenza
{"field": "category_id", "operator": "equals", "value": 42}

// Nested access
{"field": "custom_metadata.quality", "operator": ">=", "value": 0.75}
```

---

### Operatore `contains`

```json
{
  "field": "custom_metadata.keywords",
  "operator": "contains",
  "value": "urgent",
  "next_node": "high_priority_handler"
}
```

**Case-insensitive**: "URGENT", "urgent", "Urgent" → tutti match

**Esempi**:

```json
// Cerca keyword in testo
{"field": "node_outputs.analyze", "operator": "contains", "value": "risk"}

// Nested metadata
{"field": "custom_metadata.tags", "operator": "contains", "value": "premium"}
```

---

### Operatori `in` / `not_in`

```json
{
  "field": "custom_metadata.category",
  "operator": "in",
  "value": ["tech", "ai", "ml"],
  "next_node": "tech_specialist"
}
```

**Esempi**:

```json
// Whitelist
{"field": "language", "operator": "in", "value": ["en", "it", "es"]}

// Blacklist
{"field": "source", "operator": "not_in", "value": ["spam_site1", "spam_site2"]}
```

---

## Pattern Avanzati

### Pattern 1: Sentiment-Based Routing

```json
{
  "name": "customer_feedback_handler",
  "nodes": [
    {
      "id": "analyze_feedback",
      "agent": "analyst",
      "instruction": "Analyze customer feedback sentiment:\n\n{feedback_text}\n\nProvide sentiment_score (0=very negative, 1=very positive)"
    },
    {
      "id": "crisis_response",
      "agent": "writer",
      "instruction": "Draft urgent crisis response for negative feedback:\n{feedback_text}"
    },
    {
      "id": "thank_you_response",
      "agent": "writer",
      "instruction": "Draft thank you message for positive feedback:\n{feedback_text}"
    },
    {
      "id": "standard_response",
      "agent": "writer",
      "instruction": "Draft standard acknowledgment:\n{feedback_text}"
    }
  ],

  "conditional_edges": [
    {
      "from_node": "analyze_feedback",
      "conditions": [
        {
          "field": "sentiment_score",
          "operator": "<",
          "value": 0.3,
          "next_node": "crisis_response"
        },
        {
          "field": "sentiment_score",
          "operator": ">",
          "value": 0.7,
          "next_node": "thank_you_response"
        }
      ],
      "default": "standard_response"
    }
  ]
}
```

**Come funziona**:

1. Analyst analizza feedback e **popola `state.sentiment_score`**
2. Engine valuta condizioni in ordine:
   - Score < 0.3 → "crisis_response"
   - Score > 0.7 → "thank_you_response"
   - Altrimenti → "standard_response"

---

### Pattern 2: Content Length Gating

```json
{
  "name": "article_publisher",
  "nodes": [
    {
      "id": "draft_article",
      "agent": "writer",
      "instruction": "Write article on {topic}. Target: {target_length} words"
    },
    {
      "id": "check_length",
      "agent": "analyst",
      "instruction": "Count words in:\n{draft_article}\n\nProvide content_length (word count)"
    },
    {
      "id": "publish",
      "agent": "writer",
      "instruction": "Finalize for publication:\n{draft_article}"
    },
    {
      "id": "expand",
      "agent": "writer",
      "instruction": "Expand article to reach {target_length} words:\n{draft_article}"
    }
  ],

  "conditional_edges": [
    {
      "from_node": "check_length",
      "conditions": [
        {
          "field": "content_length",
          "operator": ">=",
          "value": 800,
          "next_node": "publish"
        }
      ],
      "default": "expand"
    }
  ]
}
```

---

### Pattern 3: Multi-Condition Decision Tree

```json
{
  "name": "content_triage",
  "nodes": [
    {
      "id": "classify",
      "agent": "analyst",
      "instruction": "Classify content:\n{content}\n\nProvide:\n- category (tech|business|lifestyle)\n- urgency_score (0-1)\n- quality_score (0-1)"
    },
    {
      "id": "tech_urgent",
      "agent": "writer",
      "instruction": "Handle urgent tech content..."
    },
    {
      "id": "tech_standard",
      "agent": "writer",
      "instruction": "Handle standard tech content..."
    },
    {
      "id": "business_handler",
      "agent": "writer",
      "instruction": "Handle business content..."
    },
    {
      "id": "reject_low_quality",
      "agent": "writer",
      "instruction": "Draft rejection notice..."
    }
  ],

  "conditional_edges": [
    {
      "from_node": "classify",
      "conditions": [
        {
          "field": "custom_metadata.quality_score",
          "operator": "<",
          "value": 0.5,
          "next_node": "reject_low_quality"
        },
        {
          "field": "custom_metadata.category",
          "operator": "equals",
          "value": "tech",
          "next_node": "tech_routing"
        },
        {
          "field": "custom_metadata.category",
          "operator": "equals",
          "value": "business",
          "next_node": "business_handler"
        }
      ],
      "default": "business_handler"
    },
    {
      "from_node": "tech_routing",
      "conditions": [
        {
          "field": "custom_metadata.urgency_score",
          "operator": ">",
          "value": 0.7,
          "next_node": "tech_urgent"
        }
      ],
      "default": "tech_standard"
    }
  ]
}
```

**Nota**: Questo crea un **decision tree** a due livelli:
1. Prima decisione: quality check → category routing
2. Seconda decisione (tech): urgency check

---

### Pattern 4: Iterative Improvement Loop

```json
{
  "name": "quality_loop",
  "nodes": [
    {
      "id": "generate",
      "agent": "writer",
      "instruction": "Generate {content_type}"
    },
    {
      "id": "review",
      "agent": "analyst",
      "instruction": "Review quality:\n{generate}\n\nProvide quality_score (0-1) and iteration_count",
      "depends_on": ["generate"]
    },
    {
      "id": "publish",
      "agent": "writer",
      "instruction": "Finalize:\n{generate}"
    },
    {
      "id": "improve",
      "agent": "writer",
      "instruction": "Improve based on feedback:\n{review}\n\nOriginal:\n{generate}",
      "depends_on": ["review"]
    },
    {
      "id": "force_publish",
      "agent": "writer",
      "instruction": "Publish with disclaimer (max iterations reached):\n{generate}"
    }
  ],

  "conditional_edges": [
    {
      "from_node": "review",
      "conditions": [
        {
          "field": "custom_metadata.iteration_count",
          "operator": ">=",
          "value": 3,
          "next_node": "force_publish"
        },
        {
          "field": "custom_metadata.quality_score",
          "operator": ">=",
          "value": 0.85,
          "next_node": "publish"
        }
      ],
      "default": "improve"
    },
    {
      "from_node": "improve",
      "next_node": "review"
    }
  ]
}
```

**⚠️ Attenzione**: Questo crea un **loop**!

```
generate → review → (score < 0.85) → improve → review → ...
```

**Safety**: La condizione `iteration_count >= 3` previene loop infiniti.

**Tracking iterations**: L'analyst deve incrementare `iteration_count` ad ogni passaggio.

---

## Popolare Metadata per Routing

### Metodo 1: Output Analyst Strutturato

L'**analyst** deve includere i valori nell'output:

```python
# Analyst instruction
"Analyze sentiment and provide sentiment_score (0-1)"

# Output analyst (esempio)
"""
Sentiment Analysis:
- Overall tone: Positive
- Key emotions: Enthusiasm, satisfaction
- Negative aspects: Minor concerns about pricing

sentiment_score: 0.78
"""
```

Engine estrae automaticamente con regex: `sentiment_score:\s*(\d+\.?\d*)`

**Pattern supportati**:
```
sentiment_score: 0.78
quality_score = 0.92
content_length: 1543
iteration_count: 2
```

---

### Metodo 2: Custom Metadata JSON

Per metadata strutturato complesso:

```json
{
  "id": "extract_metadata",
  "agent": "analyst",
  "instruction": "Extract structured metadata:\n{content}\n\nProvide JSON:\n{\n  \"category\": \"tech|business|lifestyle\",\n  \"urgency\": 0.0-1.0,\n  \"quality\": 0.0-1.0,\n  \"keywords\": [\"list\", \"of\", \"keywords\"]\n}"
}
```

**Output analyst**:
```json
{
  "category": "tech",
  "urgency": 0.85,
  "quality": 0.92,
  "keywords": ["ai", "machine learning", "automation"]
}
```

Engine parsea JSON e popola `state.custom_metadata`.

**Accesso nested**:
```json
{
  "field": "custom_metadata.category",
  "operator": "equals",
  "value": "tech"
}

{
  "field": "custom_metadata.keywords",
  "operator": "contains",
  "value": "ai"
}
```

---

### Metodo 3: Helper Function (Sentiment)

Il sistema include `extract_sentiment_score()` built-in:

```python
# In workflows/conditions.py
def extract_sentiment_score(text: str) -> float:
    """
    Extract sentiment from text using keyword analysis.

    Returns: 0.0 (very negative) to 1.0 (very positive)
    """
    positive_words = ["great", "excellent", "amazing", "love", ...]
    negative_words = ["bad", "poor", "hate", "terrible", ...]

    # Count occurrences
    pos_count = sum(1 for word in positive_words if word in text.lower())
    neg_count = sum(1 for word in negative_words if word in text.lower())

    # Calculate score
    if pos_count + neg_count == 0:
        return 0.5  # Neutral

    return pos_count / (pos_count + neg_count)
```

**Uso automatico**: Se `sentiment_score` non trovato nello state, engine chiama questa funzione sull'output del nodo precedente.

**Keyword lists**:
- Positive: great, excellent, amazing, wonderful, fantastic, love, perfect, outstanding, brilliant, superb
- Negative: bad, poor, terrible, awful, hate, horrible, worst, disappointing, useless, broken

---

## Debug Conditional Routing

### Logging Dettagliato

Abilita logging in `.env`:

```bash
WORKFLOW_ENABLE=true
REACT_ENABLE_VERBOSE_LOGGING=true  # ← Attiva logging workflow
```

**Output**:

```
[WorkflowEngine] Evaluating conditional edge from 'analyze_feedback'
[ConditionEvaluator] Field: sentiment_score = 0.82
[ConditionEvaluator] Condition 1: sentiment_score < 0.3 → FALSE
[ConditionEvaluator] Condition 2: sentiment_score > 0.7 → TRUE
[ConditionEvaluator] → Next node: thank_you_response
[WorkflowEngine] Executing node: thank_you_response
```

---

### Test Unitario

```python
import pytest
from workflows.conditions import ConditionEvaluator
from schemas.workflow_schemas import (
    WorkflowCondition,
    ConditionalEdge,
    ConditionOperator,
    WorkflowState
)

def test_sentiment_routing():
    """Test sentiment-based routing logic"""
    evaluator = ConditionEvaluator()

    # Setup state
    state = WorkflowState(sentiment_score=0.85)

    # Define conditions
    edge = ConditionalEdge(
        from_node="analyze",
        conditions=[
            WorkflowCondition(
                field="sentiment_score",
                operator=ConditionOperator.GREATER_THAN,
                value=0.7,
                next_node="positive"
            ),
            WorkflowCondition(
                field="sentiment_score",
                operator=ConditionOperator.LESS_THAN,
                value=0.3,
                next_node="negative"
            )
        ],
        default="neutral"
    )

    # Evaluate
    next_node = evaluator.evaluate_edge(edge, state)

    assert next_node == "positive"


def test_multi_condition():
    """Test multiple conditions with priority"""
    evaluator = ConditionEvaluator()

    # Quality first, then category
    state = WorkflowState()
    state.custom_metadata = {
        "quality_score": 0.3,  # Low quality
        "category": "tech"
    }

    edge = ConditionalEdge(
        from_node="classify",
        conditions=[
            # Priority 1: Reject low quality
            WorkflowCondition(
                field="custom_metadata.quality_score",
                operator=ConditionOperator.LESS_THAN,
                value=0.5,
                next_node="reject"
            ),
            # Priority 2: Route by category
            WorkflowCondition(
                field="custom_metadata.category",
                operator=ConditionOperator.EQUALS,
                value="tech",
                next_node="tech_handler"
            )
        ],
        default="general"
    )

    # Should reject due to low quality (first condition)
    next_node = evaluator.evaluate_edge(edge, state)
    assert next_node == "reject"
```

Vedi: `tests/test_workflows.py` per più esempi.

---

### Visualizzazione Decision Tree

Tool per visualizzare routing:

```python
def visualize_routing(template_name: str):
    """Print routing decision tree"""
    from workflows.registry import WorkflowRegistry

    registry = WorkflowRegistry()
    registry.load_templates()
    template = registry.get(template_name)

    print(f"\n=== Routing Decision Tree: {template_name} ===\n")

    for edge in template.conditional_edges:
        print(f"From: {edge.from_node}")

        for i, cond in enumerate(edge.conditions, 1):
            print(f"  {i}. IF {cond.field} {cond.operator} {cond.value}")
            print(f"     → {cond.next_node}")

        print(f"  ELSE")
        print(f"     → {edge.default}")
        print()

# Usage
visualize_routing("customer_feedback_handler")
```

**Output**:
```
=== Routing Decision Tree: customer_feedback_handler ===

From: analyze_feedback
  1. IF sentiment_score < 0.3
     → crisis_response
  2. IF sentiment_score > 0.7
     → thank_you_response
  ELSE
     → standard_response
```

---

## Best Practices

### ✅ DO

1. **Ordina condizioni per priorità**
```json
// ✅ GOOD: Quality check PRIMA di category routing
{
  "conditions": [
    {"field": "quality_score", "operator": "<", "value": 0.5, "next_node": "reject"},
    {"field": "category", "operator": "equals", "value": "tech", "next_node": "tech"}
  ]
}
```

2. **Sempre fornire default**
```json
// ✅ GOOD
{
  "conditions": [...],
  "default": "fallback_handler"  // ← OBBLIGATORIO
}
```

3. **Loop safety con iteration count**
```json
// ✅ GOOD: Previene loop infiniti
{
  "conditions": [
    {"field": "iteration_count", "operator": ">=", "value": 3, "next_node": "force_stop"},
    {"field": "quality_score", "operator": "<", "value": 0.8, "next_node": "retry"}
  ]
}
```

4. **Test edge cases**
```python
# Test boundary values
test_cases = [
    (0.0, "very_negative"),
    (0.29, "negative"),
    (0.30, "neutral"),
    (0.69, "neutral"),
    (0.70, "positive"),
    (1.0, "very_positive")
]
```

### ❌ DON'T

1. **Condizioni ambigue**
```json
// ❌ BAD: Cosa succede se score == 0.7?
{
  "conditions": [
    {"field": "score", "operator": "<", "value": 0.7, "next_node": "low"},
    {"field": "score", "operator": ">", "value": 0.7, "next_node": "high"}
  ]
}

// ✅ GOOD: Usa >= o <=
{
  "conditions": [
    {"field": "score", "operator": "<", "value": 0.7, "next_node": "low"},
    {"field": "score", "operator": ">=", "value": 0.7, "next_node": "high"}
  ]
}
```

2. **Loop senza exit condition**
```json
// ❌ DANGEROUS: Loop infinito possibile
{
  "from_node": "improve",
  "conditions": [
    {"field": "quality_score", "operator": "<", "value": 1.0, "next_node": "improve"}
  ]
}
// Score non sarà MAI 1.0 → loop infinito!
```

3. **Dipendere da field non popolati**
```json
// ❌ BAD: Se analyst non fornisce custom_metadata.category
{
  "field": "custom_metadata.category",
  "operator": "equals",
  "value": "tech"
}
// → Field undefined → default route (non errore)
```

---

## Prossimi Passi

- [MCP Integration →](03_mcp_integration.md) - Usa MCP tools in conditional workflows
- [Creating Templates ←](01_creating_templates.md) - Torna a template base

---

**Vedi anche**:
- `workflows/templates/sentiment_routing.json` - Esempio completo
- `workflows/conditions.py` - Implementazione evaluator
- `tests/test_workflows.py` - Test conditional routing
