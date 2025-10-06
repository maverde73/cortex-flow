# Workflow Cookbook - Ricettario Esempi Pratici

Collezione di 15+ template workflow pronti all'uso per scenari comuni. Ogni ricetta include template JSON completo, parametri, esempio di utilizzo e output atteso.

## Indice

- [Research & Analysis](#research--analysis)
- [Content Creation](#content-creation)
- [Data Processing](#data-processing)
- [Quality & Validation](#quality--validation)

---

# Research & Analysis

## 1. Competitive Intelligence Report

### Caso d'uso
Analisi approfondita di competitor con dati da multiple fonti (web + database aziendale).

### Template JSON
Vedi: [`examples/cookbook/research/competitive_intelligence.json`](examples/cookbook/research/competitive_intelligence.json)

### Parametri
```python
{
    "competitor_name": "OpenAI",           # Nome competitor
    "focus_areas": "pricing,features,market_position",  # Aree focus
    "time_frame": "last_6_months",        # Periodo analisi
    "include_financials": "true"          # Include dati finanziari (se disponibili)
}
```

### Utilizzo
```python
from langchain_core.messages import HumanMessage

await supervisor.ainvoke({
    "messages": [HumanMessage(content="Analyze OpenAI competitive landscape")],
    "workflow_template": "competitive_intelligence",
    "workflow_params": {
        "competitor_name": "OpenAI",
        "focus_areas": "pricing,features,market_position",
        "time_frame": "last_6_months",
        "include_financials": "true"
    }
})
```

### Output Atteso
```markdown
# Competitive Intelligence Report: OpenAI

## Executive Summary
- Market position: Leader in LLM space
- Key strengths: ChatGPT brand recognition, API ecosystem
- Vulnerabilities: Pricing pressure from competitors

## Pricing Analysis
...

## Feature Comparison
...

## Strategic Recommendations
...
```

### Features
- ✅ Parallel web + database research
- ✅ SWOT analysis automatica
- ✅ Timeline eventi competitor
- ✅ Raccomandazioni strategiche

---

## 2. Market Trend Analysis

### Caso d'uso
Analisi trend di mercato multi-source con forecasting.

### Template JSON
Vedi: [`examples/cookbook/research/market_trends.json`](examples/cookbook/research/market_trends.json)

### Parametri
```python
{
    "industry": "AI/ML",
    "geography": "North America",
    "time_horizon": "12_months",
    "data_sources": "web,database,reports"
}
```

### Workflow
```mermaid
graph LR
    A[Research Trends] --> B[Collect Data]
    B --> C[Analyze Patterns]
    C --> D[Generate Forecast]
    D --> E[Create Report]
```

### Output Components
1. **Trend Identification** (Top 5 trends con score)
2. **Pattern Analysis** (Correlazioni, seasonality)
3. **Forecast** (6-12 month projection)
4. **Investment Recommendations**

---

## 3. Customer Feedback Analysis

### Caso d'uso
Analisi sentiment e temi ricorrenti da feedback clienti (database + social media).

### Template JSON
Vedi: [`examples/cookbook/research/customer_feedback.json`](examples/cookbook/research/customer_feedback.json)

### Parametri
```python
{
    "product_name": "Product X",
    "time_period": "Q1_2024",
    "sources": "database,twitter,reddit",
    "min_feedback_count": 100
}
```

### Workflow Steps
1. **Collect Feedback** (MCP database + web scraping)
2. **Sentiment Analysis** (positive/negative/neutral classification)
3. **Theme Extraction** (topic modeling)
4. **Priority Ranking** (by volume + sentiment)
5. **Action Plan** (recommended improvements)

### Output
```json
{
  "overall_sentiment": 0.72,
  "total_feedbacks": 1543,
  "top_themes": [
    {"theme": "UI/UX", "count": 423, "sentiment": 0.45, "priority": "high"},
    {"theme": "Performance", "count": 312, "sentiment": 0.81, "priority": "medium"},
    {"theme": "Pricing", "count": 289, "sentiment": 0.62, "priority": "high"}
  ],
  "action_items": [...]
}
```

---

## 4. SWOT Analysis Generator

### Caso d'uso
Genera analisi SWOT completa per prodotto/azienda.

### Template JSON
Vedi: [`examples/cookbook/research/swot_analysis.json`](examples/cookbook/research/swot_analysis.json)

### Parametri
```python
{
    "subject": "Our new AI product",
    "context": "entering enterprise market",
    "competitors": "OpenAI,Anthropic,Google",
    "internal_data_source": "company_database"
}
```

### Workflow
- **Parallel Research**: Internal data (MCP) + External market (web)
- **SWOT Matrix Construction**: Analyst categorizes findings
- **Strategic Implications**: Writer creates action plan

### Output Format
```markdown
# SWOT Analysis: [Subject]

## Strengths
1. Strong technical team
2. Innovative features
3. ...

## Weaknesses
1. Limited brand recognition
2. ...

## Opportunities
1. Growing enterprise demand
2. ...

## Threats
1. Established competitors
2. ...

## Strategic Action Plan
- Short-term (0-6 months): ...
- Medium-term (6-12 months): ...
- Long-term (12+ months): ...
```

---

# Content Creation

## 5. Blog Post Multi-Format Generator

### Caso d'uso
Trasforma ricerca in blog post + versioni per social media + newsletter.

### Template JSON
Vedi: [`examples/cookbook/content/blog_multi_format.json`](examples/cookbook/content/blog_multi_format.json)

### Parametri
```python
{
    "topic": "Future of AI in Healthcare",
    "target_audience": "healthcare professionals",
    "tone": "professional yet accessible",
    "blog_length": "1500",
    "include_formats": "twitter,linkedin,newsletter"
}
```

### Workflow
```
Research Topic
      ↓
  Outline Blog
      ↓
  Write Blog Post
      ↓
 ┌────┴────┬────────┐
 ↓         ↓        ↓
Tweet    LinkedIn  Newsletter
Thread    Post     Summary
 └────┬────┴────────┘
      ↓
Final Package
```

### Output Package
```
outputs/
├── blog_post.md           (1500 words, SEO optimized)
├── twitter_thread.txt     (12 tweets, with hashtags)
├── linkedin_post.md       (800 words, professional)
└── newsletter_summary.md  (300 words, CTA included)
```

---

## 6. Product Description Generator

### Caso d'uso
Genera descrizioni prodotto ottimizzate per e-commerce (multiple varianti).

### Template JSON
Vedi: [`examples/cookbook/content/product_description.json`](examples/cookbook/content/product_description.json)

### Parametri
```python
{
    "product_name": "Smart Watch Pro",
    "category": "Wearable Tech",
    "key_features": "heart rate,GPS,waterproof,7-day battery",
    "target_market": "fitness enthusiasts",
    "variants": "short,medium,long,seo"
}
```

### Output Variants
1. **Short** (50 words): Product listing
2. **Medium** (150 words): Product page main
3. **Long** (300 words): Detailed specifications
4. **SEO** (200 words): Search engine optimized

---

## 7. Email Campaign Creator

### Caso d'uso
Crea serie di email per campagne marketing (welcome, nurture, promo).

### Template JSON
Vedi: [`examples/cookbook/content/email_campaign.json`](examples/cookbook/content/email_campaign.json)

### Parametri
```python
{
    "campaign_type": "welcome_series",
    "brand_voice": "friendly and helpful",
    "num_emails": 5,
    "call_to_action": "start_free_trial",
    "personalization_fields": "first_name,signup_date,interest"
}
```

### Email Series Structure
```
Email 1 (Day 0):  Welcome + value proposition
Email 2 (Day 2):  Feature highlight #1
Email 3 (Day 5):  Feature highlight #2
Email 4 (Day 7):  Success story / testimonial
Email 5 (Day 10): Special offer + CTA
```

### Features
- ✅ A/B test subject lines (2 variants per email)
- ✅ Personalization placeholders
- ✅ CTA button copy optimization
- ✅ Preview text generation

---

## 8. Documentation Generator

### Caso d'uso
Genera documentazione tecnica da codebase/API specs.

### Template JSON
Vedi: [`examples/cookbook/content/documentation_gen.json`](examples/cookbook/content/documentation_gen.json)

### Parametri
```python
{
    "source_type": "api_spec",           # api_spec | codebase | database_schema
    "input_file": "api/openapi.yaml",
    "doc_format": "markdown",
    "include_examples": "true",
    "target_audience": "developers"
}
```

### Workflow
1. **Parse Input** (MCP file reader)
2. **Extract Entities** (endpoints/functions/tables)
3. **Generate Docs** (descriptions + examples)
4. **Create Index** (navigation structure)

### Output
- API reference with code examples
- Getting started guide
- Authentication guide
- Error handling reference
- Changelog template

---

# Data Processing

## 9. Database Report Automation

### Caso d'uso
Report automatici da query database con scheduling.

### Template JSON
Vedi: [`examples/cookbook/data/database_report.json`](examples/cookbook/data/database_report.json)

### Parametri
```python
{
    "report_type": "weekly_sales",
    "database": "sales_db",
    "date_range": "last_7_days",
    "grouping": "by_product_category",
    "include_charts": "true",
    "recipients": "management_team"
}
```

### Workflow
```mermaid
graph LR
    A[Query Database<br/>MCP Tool] --> B[Aggregate Data<br/>analyst]
    B --> C[Generate Charts<br/>analyst]
    C --> D[Write Report<br/>writer]
    D --> E[Format Email<br/>writer]
```

### Output
- Executive summary (PDF)
- Detailed analysis (Excel/CSV)
- Trend charts (PNG)
- Email-ready HTML

---

## 10. CSV to Insights Workflow

### Caso d'uso
Carica CSV, analizza dati, genera insights automatici.

### Template JSON
Vedi: [`examples/cookbook/data/csv_insights.json`](examples/cookbook/data/csv_insights.json)

### Parametri
```python
{
    "csv_file": "data/sales_2024_q1.csv",
    "analysis_type": "descriptive_stats",  # descriptive_stats | trend_analysis | anomaly_detection
    "target_columns": "revenue,units_sold,customer_id",
    "generate_visualizations": "true"
}
```

### Analysis Types

**Descriptive Stats**:
- Mean, median, mode
- Standard deviation
- Quartiles, outliers
- Correlation matrix

**Trend Analysis**:
- Time series decomposition
- Seasonality detection
- Growth rate calculation
- Forecasting (simple moving average)

**Anomaly Detection**:
- Statistical outliers (Z-score)
- Sudden spikes/drops
- Pattern breaks

---

## 11. Multi-Source Data Aggregation

### Caso d'uso
Combina dati da database + API + file per report unificato.

### Template JSON
Vedi: [`examples/cookbook/data/multi_source_aggregation.json`](examples/cookbook/data/multi_source_aggregation.json)

### Parametri
```python
{
    "sources": [
        {"type": "database", "name": "sales_db", "query": "..."},
        {"type": "api", "name": "weather_api", "endpoint": "..."},
        {"type": "file", "name": "inventory.csv", "path": "..."}
    ],
    "join_key": "date",
    "output_format": "json"
}
```

### Workflow (Parallel Fetching)
```
┌─────────────┐
│ Database    │ ──┐
│ (MCP Tool)  │   │
└─────────────┘   │
                  ├──→ Merge Data → Analyze → Report
┌─────────────┐   │
│ API Call    │ ──┤
│ (MCP Tool)  │   │
└─────────────┘   │
                  │
┌─────────────┐   │
│ File Read   │ ──┘
│ (MCP Tool)  │
└─────────────┘
```

**Time Savings**: Parallel fetch instead of sequential

---

## 12. ETL Pipeline with MCP

### Caso d'uso
Extract-Transform-Load workflow orchestration.

### Template JSON
Vedi: [`examples/cookbook/data/etl_pipeline.json`](examples/cookbook/data/etl_pipeline.json)

### Parametri
```python
{
    "extract": {
        "source_type": "api",
        "endpoint": "https://api.example.com/data",
        "auth": "bearer_token"
    },
    "transform": {
        "operations": ["normalize", "deduplicate", "enrich"],
        "validation_rules": "schema.json"
    },
    "load": {
        "target_database": "warehouse_db",
        "table": "processed_data",
        "mode": "append"
    }
}
```

### Pipeline Steps
1. **Extract** (MCP API call)
2. **Validate** (check schema compliance)
3. **Transform** (normalize + enrich)
4. **Quality Check** (data quality rules)
5. **Load** (MCP database write)
6. **Verify** (row count, integrity check)

---

# Quality & Validation

## 13. Content Quality Assurance Loop

### Caso d'uso
Iterative content improvement con quality gates.

### Template JSON
Vedi: [`examples/cookbook/quality/qa_loop.json`](examples/cookbook/quality/qa_loop.json)

### Parametri
```python
{
    "content_type": "blog_post",
    "quality_threshold": 0.85,         # 0.0 - 1.0
    "max_iterations": 3,
    "quality_criteria": "readability,accuracy,engagement,seo"
}
```

### Workflow (Iterative)
```
Draft Content
     ↓
Review Quality (analyst)
     ↓
┌────┴────┐
│ score?  │
└────┬────┘
     ├─ >= 0.85 ──→ Publish
     ├─ < 0.85 & iter < 3 ──→ Improve ──┐
     └─ iter >= 3 ──→ Force Publish      │
                                         │
         ┌───────────────────────────────┘
         └──→ Review Quality (loop)
```

### Quality Metrics
- **Readability**: Flesch-Kincaid score
- **Accuracy**: Fact-checking flagged claims
- **Engagement**: Hook strength, CTA clarity
- **SEO**: Keyword density, meta tags

---

## 14. Fact-Checking Workflow

### Caso d'uso
Verifica claims in contenuto con sources citati.

### Template JSON
Vedi: [`examples/cookbook/quality/fact_checking.json`](examples/cookbook/quality/fact_checking.json)

### Parametri
```python
{
    "content": "article_text.md",
    "claim_threshold": 0.7,            # Confidence threshold for claims
    "require_sources": "true",
    "fallback_to_web": "true"
}
```

### Workflow
1. **Extract Claims** (analyst identifies factual statements)
2. **Parallel Verification**:
   - Database lookup (MCP internal knowledge base)
   - Web search (researcher for recent facts)
3. **Score Confidence** (0.0-1.0 per claim)
4. **Flag Disputes** (claims below threshold)
5. **Generate Report** (verified/disputed/unverifiable)

### Output
```json
{
  "claims_checked": 23,
  "verified": 18,
  "disputed": 3,
  "unverifiable": 2,
  "flagged_claims": [
    {
      "claim": "AI market will reach $500B by 2025",
      "confidence": 0.45,
      "sources": ["Forbes", "Gartner"],
      "recommendation": "Update with latest forecast"
    }
  ]
}
```

---

## 15. Translation + Review Workflow

### Caso d'uso
Traduci contenuto con quality review da native speaker (human-in-loop).

### Template JSON
Vedi: [`examples/cookbook/quality/translation_review.json`](examples/cookbook/quality/translation_review.json)

### Parametri
```python
{
    "source_language": "en",
    "target_languages": ["it", "es", "fr"],
    "content_file": "blog_post.md",
    "preserve_formatting": "true",
    "review_required": "true",          # Conditional: if quality < threshold
    "quality_threshold": 0.8
}
```

### Workflow (per language)
```
Translate Content
     ↓
Quality Check (analyst)
     ↓
┌────┴────┐
│quality? │
└────┬────┘
     ├─ >= 0.8 ──→ Approve
     └─ < 0.8 ──→ Flag for Human Review
```

### Quality Checks
- Grammar correctness
- Cultural appropriateness
- Terminology consistency
- Formatting preservation

---

## 16. A/B Test Result Analyzer

### Caso d'uso
Analisi risultati A/B test con statistical significance.

### Template JSON
Vedi: [`examples/cookbook/quality/ab_test_analyzer.json`](examples/cookbook/quality/ab_test_analyzer.json)

### Parametri
```python
{
    "test_id": "email_subject_test_001",
    "variant_a": {"name": "Control", "metric_value": 0.045},
    "variant_b": {"name": "Treatment", "metric_value": 0.052},
    "sample_size_a": 10000,
    "sample_size_b": 10000,
    "confidence_level": 0.95
}
```

### Analysis
1. **Calculate Metrics**:
   - Conversion rate difference
   - Relative lift
   - Statistical significance (chi-square test)
   - Confidence interval

2. **Decision Recommendation**:
   - Winner declared if p-value < 0.05
   - Suggest longer test if inconclusive
   - Estimate sample size needed

3. **Report Generation**:
   - Executive summary
   - Statistical details
   - Visualization suggestions
   - Next steps

---

## Utilizzo Rapido

### Template Lookup

```python
# Lista tutti i template cookbook
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()
registry.load_templates()

cookbook_templates = [
    t for t in registry.list_templates()
    if t.startswith("cookbook_")
]

print(cookbook_templates)
```

### Auto-Match con Trigger Patterns

Ogni template cookbook ha trigger patterns specifici:

```python
# User dice: "Analyze competitor pricing"
# → Auto-match: cookbook_competitive_intelligence

# User dice: "Generate product description"
# → Auto-match: cookbook_product_description

# User dice: "Check facts in this article"
# → Auto-match: cookbook_fact_checking
```

---

## Personalizzazione

Ogni template può essere personalizzato:

1. **Copia template**:
```bash
cp examples/cookbook/research/market_trends.json \
   workflows/templates/my_custom_analysis.json
```

2. **Modifica**:
   - Cambia `name`
   - Aggiungi/rimuovi nodi
   - Personalizza istruzioni
   - Adjust timeouts

3. **Valida**:
```python
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()
template = registry.get("my_custom_analysis")
errors = registry.validate_template(template)
```

---

## Best Practices Cookbook

### 1. Parametri Sensibili
```python
# ✅ GOOD: Usa .env per credentials
{
    "database": "sales_db",  # Config gestisce connection
}

# ❌ BAD: Hardcode credentials
{
    "database_url": "postgres://user:password@..."
}
```

### 2. Error Handling
Aggiungi fallback per MCP tools:
```json
{
  "nodes": [
    {"id": "primary_data", "agent": "mcp_tool", "tool_name": "database"},
    {"id": "check_data", "agent": "analyst", "instruction": "Check if data returned"},
    {"id": "use_data", "agent": "writer"},
    {"id": "fallback", "agent": "researcher"}
  ],
  "conditional_edges": [{
    "from_node": "check_data",
    "conditions": [{"field": "has_data", "operator": "equals", "value": true, "next_node": "use_data"}],
    "default": "fallback"
  }]
}
```

### 3. Caching
Per report ricorrenti, considera caching risultati intermedi:
```python
# Pseudo-code per future enhancement
if state.node_outputs.get("research_cache"):
    skip_research = True
```

---

## Contribuire Nuove Ricette

Hai un workflow utile? Contribuisci al cookbook:

1. Crea template in `examples/cookbook/[categoria]/`
2. Documenta parametri e output
3. Testa con dati reali
4. Aggiungi sezione in questo documento
5. Submit PR!

---

## Prossimi Passi

- [Migration Guide →](06_migration_guide.md) - Strategia migrazione ibrida
- [Visual Diagrams ←](04_visual_diagrams.md) - Diagrammi workflow
- [Creating Templates ←](01_creating_templates.md) - Crea template custom

---

**Template completi disponibili in**: `docs/workflows/examples/cookbook/`