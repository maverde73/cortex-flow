# Workflow Cookbook Templates

Production-ready workflow templates organized by use case category.

## Directory Structure

```
cookbook/
├── research/           # Research & competitive analysis workflows
├── content/            # Content creation & repurposing workflows
├── data/              # Data processing & reporting workflows
└── quality/           # Quality assurance & validation workflows
```

## Available Templates

### Research & Analysis (`research/`)

#### 1. **competitive_intelligence.json**
Comprehensive competitor analysis with parallel research and SWOT.

**Parameters**:
- `company_name`: Target company
- `competitor1`, `competitor2`: Competitors to analyze

**Features**:
- Parallel research (3 companies simultaneously)
- SWOT analysis
- Strategic recommendations

**Usage**:
```python
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Analyze our competitive position")],
    "workflow_template": "competitive_intelligence",
    "workflow_params": {
        "company_name": "Acme Corp",
        "competitor1": "Competitor A",
        "competitor2": "Competitor B"
    }
})
```

---

#### 2. **market_trend_analysis.json**
Analyze market trends with forecasting capabilities.

**Parameters**:
- `industry`: Target industry
- `time_period`: Analysis timeframe
- `focus_areas`: Specific areas to focus on (array)

**Features**:
- Historical data analysis
- 12-18 month forecasting
- Strategic insights extraction

**Usage**:
```python
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Analyze AI market trends")],
    "workflow_template": "market_trend_analysis",
    "workflow_params": {
        "industry": "Artificial Intelligence",
        "time_period": "2024 Q4",
        "focus_areas": ["GenAI", "MLOps", "Edge AI"]
    }
})
```

---

### Content Creation (`content/`)

#### 3. **blog_multi_format_generator.json**
Transform blog posts into 5 social media formats simultaneously.

**Parameters**:
- `blog_url`: URL of source blog post
- `target_platforms`: Platforms to create content for (array)

**Features**:
- **Parallel content generation** (5 formats simultaneously)
- Twitter/X thread (10-15 tweets)
- LinkedIn post (professional)
- Instagram carousel (8-10 slides)
- YouTube script (5-7 minutes)
- Email newsletter snippet
- Publishing schedule suggestions

**Usage**:
```python
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Repurpose my blog post")],
    "workflow_template": "blog_multi_format_generator",
    "workflow_params": {
        "blog_url": "https://example.com/my-article",
        "target_platforms": ["twitter", "linkedin", "instagram", "youtube", "newsletter"]
    }
})
```

**Performance**: ~60s (parallel) vs ~180s (sequential) = **67% faster**

---

### Data Processing (`data/`)

#### 4. **database_report_automation.json**
Automated database reporting with MCP integration and trend analysis.

**Parameters**:
- `report_type`: Type of report (e.g., "Sales Report")
- `table_name`: Database table to query
- `time_period`: Reporting period
- `start_date`, `previous_start`, `previous_end`: Date filters

**Features**:
- **MCP tool integration** (query_database)
- Period-over-period comparison
- Statistical analysis
- Visualization specifications
- Actionable insights

**Usage**:
```python
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Generate weekly sales report")],
    "workflow_template": "database_report_automation",
    "workflow_params": {
        "report_type": "Weekly Sales Report",
        "table_name": "sales_transactions",
        "time_period": "2024-W01",
        "start_date": "2024-01-01",
        "previous_start": "2023-12-25",
        "previous_end": "2023-12-31"
    }
})
```

**Prerequisites**: Corporate MCP server running on port 8005

---

### Quality & Validation (`quality/`)

#### 5. **content_qa_loop.json**
Iterative content improvement with quality gates and conditional routing.

**Parameters**:
- `content_type`: Type of content to create (e.g., "blog post")
- `topic`: Content topic
- `quality_threshold`: Minimum quality score (0.0-1.0)
- `target_length`: Word count target

**Features**:
- **Iterative improvement loop** (max 3 iterations)
- **Conditional routing** based on quality_score
- Multi-criteria quality evaluation (7 dimensions)
- Automatic improvement suggestions
- Safety: Force publish after 3 iterations with disclaimer

**Usage**:
```python
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Create high-quality article")],
    "workflow_template": "content_quality_assurance_loop",
    "workflow_params": {
        "content_type": "blog post",
        "topic": "Benefits of AI in Healthcare",
        "quality_threshold": "0.85",
        "target_length": "1500"
    }
})
```

**Flow**:
```
Draft → Review → quality_score >= 0.85?
  ├─ Yes → Publish
  ├─ No + iteration < 3 → Improve → Review (loop)
  └─ No + iteration >= 3 → Force publish with disclaimer
```

---

## Installation

Copy templates to your workflow templates directory:

```bash
# Copy all cookbook templates
cp -r docs/workflows/examples/cookbook/* workflows/templates/

# Or copy specific category
cp docs/workflows/examples/cookbook/research/*.json workflows/templates/
```

## Testing Templates

```python
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()
registry.load_templates()

# Validate template
template = registry.get("competitive_intelligence")
errors = registry.validate_template(template)

if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Template valid")
```

## Customization

All templates are fully customizable:

1. **Modify instructions**: Adjust agent instructions for your domain
2. **Add/remove nodes**: Extend workflows with additional steps
3. **Adjust timeouts**: Based on your performance requirements
4. **Add conditional logic**: Create custom routing rules
5. **Integrate MCP tools**: Connect to your own databases/APIs

**Example**: Add sentiment analysis to blog repurposing:
```json
{
  "id": "analyze_sentiment",
  "agent": "analyst",
  "instruction": "Analyze sentiment of blog:\n{fetch_blog}\n\nReturn sentiment_score (0.0-1.0)",
  "depends_on": ["fetch_blog"]
}
```

## Performance Notes

| Template | Avg Latency | Features |
|----------|-------------|----------|
| competitive_intelligence | ~45s | Parallel research (3 agents) |
| market_trend_analysis | ~60s | Sequential analysis |
| blog_multi_format | ~60s | **Parallel content** (5 formats) |
| database_report | ~25s | **MCP integration** |
| content_qa_loop | ~90-180s | **Iterative with conditional** |

**Optimization tips**:
- Use `parallel_group` for independent tasks
- Set appropriate `timeout` values
- Cache MCP tool results when possible

## Best Practices

1. **Variable Naming**: Use descriptive names (e.g., `company_name` not `c`)
2. **Error Handling**: Always set realistic `timeout` values
3. **Documentation**: Add clear `description` to templates
4. **Testing**: Validate templates before production deployment
5. **Monitoring**: Track workflow execution times and success rates

## Troubleshooting

### Template not loading
```bash
# Check JSON syntax
python -m json.tool workflows/templates/your_template.json

# Check logs
tail -f logs/workflow.log
```

### Workflow fails
- Check MCP servers are running (for data workflows)
- Verify all required parameters provided
- Check timeout values (increase if needed)
- Enable verbose logging: `REACT_ENABLE_VERBOSE_LOGGING=true`

### Auto-match not working
- Test trigger patterns with regex:
```python
import re
pattern = ".*competitive.*analysis.*"
user_input = "Run competitive analysis"
print(bool(re.search(pattern, user_input.lower())))  # Should be True
```

## Contributing

To contribute new cookbook templates:

1. Create template in appropriate category directory
2. Follow naming convention: `{purpose}_{type}.json`
3. Include comprehensive `description` and `trigger_patterns`
4. Add usage example to this README
5. Test with `registry.validate_template()`

## Additional Resources

- [Creating Templates Guide](../../01_creating_templates.md)
- [Conditional Routing Guide](../../02_conditional_routing.md)
- [MCP Integration Guide](../../03_mcp_integration.md)
- [Visual Diagrams](../../04_visual_diagrams.md)
- [Full Cookbook](../../05_cookbook.md)
- [Migration Guide](../../06_migration_guide.md)

---

**Note**: These templates are starting points. Customize them for your specific use cases and domain requirements.
