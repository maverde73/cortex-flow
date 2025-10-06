# Diagrammi Visuali del Sistema Workflow

Diagrammi Mermaid per comprendere visivamente l'architettura e i flussi del sistema workflow.

## Indice

- [Architettura Sistema](#architettura-sistema)
- [Routing Logic](#routing-logic)
- [Esecuzione Workflow](#esecuzione-workflow)
- [MCP Integration](#mcp-integration)
- [Esempi Workflow Popolari](#esempi-workflow-popolari)

---

## Architettura Sistema

### Dual-Mode Supervisor

```mermaid
graph TB
    User[User Input] --> Supervisor[Workflow Supervisor]

    Supervisor --> Router{Router<br/>Decision}

    Router -->|workflow_template<br/>specified| WorkflowMode[Workflow Mode]
    Router -->|auto-match<br/>success| WorkflowMode
    Router -->|no match| ReActMode[ReAct Mode]

    WorkflowMode --> WE[Workflow Engine]
    WE --> Registry[Template Registry]
    Registry --> Execute[Execute Nodes]
    Execute --> Result[Final Output]

    ReActMode --> LLM[LLM Reasoning]
    LLM --> Tools[Tool Selection]
    Tools --> Agent[Agent Delegation]
    Agent --> LLM
    LLM --> Result

    style WorkflowMode fill:#90EE90
    style ReActMode fill:#FFB6C1
    style Router fill:#FFD700
```

**Legenda**:
- 🟢 Verde: Workflow mode (predefinito)
- 🔴 Rosa: ReAct mode (autonomo)
- 🟡 Giallo: Decision point

---

### Componenti Sistema

```mermaid
graph LR
    subgraph "Workflow System"
        Registry[WorkflowRegistry<br/>Template Manager]
        Engine[WorkflowEngine<br/>Execution Core]
        Conditions[ConditionEvaluator<br/>Routing Logic]
    end

    subgraph "Templates"
        JSON1[report_generation.json]
        JSON2[competitive_analysis.json]
        JSON3[data_analysis_report.json]
        JSON4[sentiment_routing.json]
    end

    subgraph "Integration"
        Agents[Researcher<br/>Analyst<br/>Writer]
        MCP[MCP Tools<br/>Database/API/Files]
    end

    Registry --> JSON1
    Registry --> JSON2
    Registry --> JSON3
    Registry --> JSON4

    Engine --> Registry
    Engine --> Conditions
    Engine --> Agents
    Engine --> MCP

    style Registry fill:#87CEEB
    style Engine fill:#98FB98
    style Conditions fill:#DDA0DD
```

---

## Routing Logic

### Router Decision Flow

```mermaid
flowchart TD
    Start([User Request]) --> CheckExplicit{workflow_template<br/>specified?}

    CheckExplicit -->|Yes| LoadTemplate[Load Template]
    CheckExplicit -->|No| CheckMode{workflow_mode?}

    CheckMode -->|template| Error[Error: Template<br/>not specified]
    CheckMode -->|react| ReAct[Use ReAct Mode]
    CheckMode -->|hybrid/auto| AutoMatch{Auto-match<br/>template?}

    AutoMatch -->|Match Found| LoadTemplate
    AutoMatch -->|No Match| ReAct

    LoadTemplate --> Validate{Template<br/>Valid?}
    Validate -->|Yes| Execute[Execute Workflow]
    Validate -->|No| CheckFallback{Fallback<br/>Enabled?}

    CheckFallback -->|Yes| ReAct
    CheckFallback -->|No| Error

    Execute --> Success{Execution<br/>Success?}
    Success -->|Yes| Output([Final Output])
    Success -->|No| CheckFallback

    ReAct --> Output

    style LoadTemplate fill:#90EE90
    style ReAct fill:#FFB6C1
    style Execute fill:#87CEEB
    style Output fill:#FFD700
```

---

### Auto-Match Logic

```mermaid
sequenceDiagram
    participant User
    participant Router
    participant Registry
    participant Templates

    User->>Router: "Create weekly report"
    Router->>Registry: match_template("Create weekly report")

    loop For each template
        Registry->>Templates: Get trigger_patterns
        Templates-->>Registry: [".*report.*", ".*weekly.*"]
        Registry->>Registry: regex.search(pattern, input.lower())
    end

    alt Match Found
        Registry-->>Router: Template: "report_generation"
        Router->>Router: Set workflow_template
        Router-->>User: Execute Workflow Mode
    else No Match
        Registry-->>Router: None
        Router-->>User: Fallback to ReAct Mode
    end
```

---

## Esecuzione Workflow

### Sequential Workflow

```mermaid
graph LR
    Start([Start]) --> N1[Node 1<br/>researcher]
    N1 --> N2[Node 2<br/>analyst]
    N2 --> N3[Node 3<br/>writer]
    N3 --> End([Output])

    N1 -.->|output| S1[(State)]
    S1 -.->|{node1}| N2
    N2 -.->|output| S2[(State)]
    S2 -.->|{node2}| N3

    style N1 fill:#FFB6C1
    style N2 fill:#87CEEB
    style N3 fill:#98FB98
```

**Esempio**: `report_generation.json`
- Node 1: Research topic
- Node 2: Analyze findings
- Node 3: Write report

---

### Parallel Workflow

```mermaid
graph TB
    Start([Start]) --> Analyze[Analyze Blog<br/>analyst]

    Analyze --> Parallel{Parallel Group:<br/>'social_content'}

    Parallel --> N1[Create Tweet<br/>writer]
    Parallel --> N2[Create LinkedIn<br/>writer]
    Parallel --> N3[Create Summary<br/>writer]

    N1 --> Sync((Sync Point))
    N2 --> Sync
    N3 --> Sync

    Sync --> Compile[Compile Report<br/>writer]
    Compile --> End([Output])

    style Parallel fill:#FFD700
    style Sync fill:#FF6347
    style N1 fill:#98FB98
    style N2 fill:#98FB98
    style N3 fill:#98FB98
```

**Esempio**: `content_repurposing.json`
- Parallel: 3 writer nodes execute simultaneously
- Sync: Wait for all completions
- Time: max(tweet, linkedin, summary) instead of sum

---

### Conditional Workflow

```mermaid
graph TB
    Start([User Feedback]) --> Analyze[Analyze Sentiment<br/>analyst]

    Analyze --> Extract{Extract<br/>sentiment_score}

    Extract --> Check1{score < 0.3?}
    Check1 -->|Yes| Crisis[Crisis Response<br/>writer]
    Check1 -->|No| Check2{score > 0.7?}

    Check2 -->|Yes| Thanks[Thank You<br/>writer]
    Check2 -->|No| Standard[Standard Response<br/>writer]

    Crisis --> End([Output])
    Thanks --> End
    Standard --> End

    style Extract fill:#FFD700
    style Check1 fill:#FFA500
    style Check2 fill:#FFA500
    style Crisis fill:#FF6347
    style Thanks fill:#90EE90
    style Standard fill:#87CEEB
```

**Esempio**: `sentiment_routing.json`
- Conditional edges based on sentiment_score
- 3 possible paths depending on sentiment

---

### Iterative Loop Workflow

```mermaid
graph TB
    Start([Start]) --> Generate[Generate Content<br/>writer]

    Generate --> Review[Review Quality<br/>analyst]

    Review --> Check1{iteration >= 3?}
    Check1 -->|Yes| Force[Force Publish<br/>with disclaimer]
    Check1 -->|No| Check2{quality >= 0.85?}

    Check2 -->|Yes| Publish[Publish<br/>writer]
    Check2 -->|No| Improve[Improve Content<br/>writer]

    Improve --> Review

    Force --> End([Output])
    Publish --> End

    style Check1 fill:#FF6347
    style Check2 fill:#FFD700
    style Improve fill:#FFA500
    style Review fill:#87CEEB
```

**Safety**: `iteration_count >= 3` prevents infinite loops

---

## MCP Integration

### MCP Tool Execution Flow

```mermaid
sequenceDiagram
    participant Engine as Workflow Engine
    participant Client as MCP Client
    participant Registry as MCP Registry
    participant Server as MCP Server
    participant DB as External Resource

    Engine->>Engine: Resolve parameters<br/>{table_name} → "users"
    Engine->>Client: call_tool("query_database", params)

    Client->>Registry: get_tool("query_database")
    Registry-->>Client: Tool metadata + server info

    Client->>Registry: get_server_config("corporate")
    Registry-->>Client: URL, status, transport

    Client->>Server: POST /mcp<br/>{"tool": "query_database", "args": {...}}
    Server->>DB: Execute query
    DB-->>Server: Result data
    Server-->>Client: JSON response

    Client-->>Engine: Parsed output
    Engine->>Engine: Save to state.node_outputs["query_data"]
```

---

### Database Query Workflow with MCP

```mermaid
graph TB
    Start([User Request]) --> Params[Extract Params<br/>time_period, table_name]

    Params --> Query[MCP Tool Node<br/>query_database]
    Query --> MCP[MCP Client]

    MCP --> Corp[(Corporate Server<br/>:8005/mcp)]
    Corp --> DB[(Sales DB)]

    DB --> Data[Query Results<br/>JSON array]
    Data --> Analyze[Analyze Trends<br/>analyst]

    Analyze --> Report[Create Report<br/>writer]
    Report --> End([Executive Report])

    style Query fill:#DDA0DD
    style MCP fill:#FF69B4
    style Corp fill:#8B4513
    style DB fill:#4682B4
```

**Esempio**: `data_analysis_report.json`

---

### Parallel MCP + Web Research

```mermaid
graph TB
    Start([User Query]) --> Parallel{Parallel Group:<br/>'sources'}

    Parallel --> Web[Web Research<br/>researcher]
    Parallel --> DB[Database Query<br/>mcp_tool]
    Parallel --> API[Weather API<br/>mcp_tool]

    Web --> Sync((Sync))
    DB --> Sync
    API --> Sync

    Sync --> Synthesize[Synthesize Data<br/>analyst]
    Synthesize --> Summary[Create Summary<br/>writer]
    Summary --> End([Multi-Source Report])

    style Parallel fill:#FFD700
    style DB fill:#DDA0DD
    style API fill:#DDA0DD
    style Sync fill:#FF6347
```

**Esempio**: `multi_source_research.json`

---

## Esempi Workflow Popolari

### Competitive Analysis

```mermaid
graph LR
    Start([Compare A vs B]) --> P{Parallel:<br/>'research'}

    P --> R1[Research<br/>Competitor A]
    P --> R2[Research<br/>Competitor B]

    R1 --> Sync((Wait))
    R2 --> Sync

    Sync --> Compare[Compare Results<br/>analyst]
    Compare --> Report[Generate Report<br/>writer]
    Report --> End([Comparison Report])

    style P fill:#FFD700
    style R1 fill:#FFB6C1
    style R2 fill:#FFB6C1
    style Compare fill:#87CEEB
    style Report fill:#98FB98
```

**Template**: `competitive_analysis.json`

**Trigger patterns**:
- "compare .* with .*"
- ".* vs .*"
- ".*competitive.*analysis.*"

---

### Email Newsletter Pipeline

```mermaid
graph TB
    Start([Weekly Newsletter Request]) --> Research[Research Trends<br/>researcher<br/>timeout: 300s]

    Research --> Analyze[Analyze Relevance<br/>analyst<br/>rank by importance]

    Analyze --> Write[Write Newsletter<br/>writer<br/>format: email HTML]

    Write --> End([Newsletter<br/>+ subject line])

    Research -.->|{topic}| State[(Workflow State)]
    State -.->|{research_trends}| Analyze
    State -.->|{analyze_relevance}| Write

    style Research fill:#FFB6C1
    style Analyze fill:#87CEEB
    style Write fill:#98FB98
```

**Template**: `newsletter_workflow.json` (docs/workflows/examples/)

**Variables**:
- `{topic}`: AI trends
- `{audience}`: tech professionals
- `{tone}`: professional
- `{length}`: 500 words

---

### Quality Assurance Loop

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review

    Review --> Check_Quality
    Check_Quality --> High_Quality: score >= 0.85
    Check_Quality --> Max_Iterations: iteration >= 3
    Check_Quality --> Needs_Improvement: else

    Needs_Improvement --> Improve
    Improve --> Review

    High_Quality --> Publish
    Max_Iterations --> Force_Publish

    Publish --> [*]
    Force_Publish --> [*]
```

**Safety mechanisms**:
1. Quality threshold (0.85)
2. Max iterations (3)
3. Force publish with disclaimer

---

## State Management

### Workflow State Lifecycle

```mermaid
graph TB
    Init[Initialize State] --> Params[Set workflow_params]
    Params --> Node1[Execute Node 1]

    Node1 --> Update1[Update state:<br/>- completed_nodes<br/>- node_outputs<br/>- current_node]

    Update1 --> Conditional{Conditional<br/>Edge?}

    Conditional -->|Yes| Evaluate[Evaluate Conditions]
    Conditional -->|No| Next{More<br/>Nodes?}

    Evaluate --> Extract[Extract metadata:<br/>- sentiment_score<br/>- custom_metadata]
    Extract --> Route[Determine next_node]
    Route --> Next

    Next -->|Yes| Node2[Execute Next Node]
    Next -->|No| Finalize[Finalize Result]

    Node2 --> Update1
    Finalize --> Return([Return WorkflowResult])

    style Init fill:#90EE90
    style Update1 fill:#87CEEB
    style Evaluate fill:#FFD700
    style Return fill:#98FB98
```

---

## Dependency Resolution

### DAG Construction

```mermaid
graph TB
    subgraph "Template Nodes"
        N1[Node A<br/>depends_on: []]
        N2[Node B<br/>depends_on: [A]]
        N3[Node C<br/>depends_on: [A]]
        N4[Node D<br/>depends_on: [B, C]]
    end

    subgraph "Execution Plan (DAG)"
        Step1[Step 1: Sequential<br/>Execute A]
        Step2[Step 2: Parallel<br/>Execute B || C]
        Step3[Step 3: Sequential<br/>Execute D]
    end

    N1 --> Step1
    N2 --> Step2
    N3 --> Step2
    N4 --> Step3

    Step1 --> Step2
    Step2 --> Step3

    style Step2 fill:#FFD700
```

**Algorithm**: Topological sort with parallel group detection

---

## Variable Substitution

### Substitution Flow

```mermaid
graph LR
    Template["Instruction:<br/>'Analyze {research} for {topic}'"] --> Parse[Parse Variables]

    Parse --> V1{"{research}"}
    Parse --> V2{"{topic}"}

    V1 --> Check1{In node_outputs?}
    Check1 -->|Yes| Sub1["node_outputs['research']"]
    Check1 -->|No| Check2{In workflow_params?}
    Check2 -->|Yes| Sub2["workflow_params['research']"]
    Check2 -->|No| Error[Error: Variable not found]

    V2 --> Check3{In workflow_params?}
    Check3 -->|Yes| Sub3["workflow_params['topic']"]

    Sub1 --> Result["Analyze 'AI is growing...' for 'AI trends'"]
    Sub2 --> Result
    Sub3 --> Result

    style V1 fill:#FFD700
    style V2 fill:#FFD700
    style Result fill:#90EE90
```

**Priority**:
1. `node_outputs[var]` (output nodi precedenti)
2. `workflow_params[var]` (parametri utente)
3. Error if not found

---

## Performance Comparison

### Sequential vs Parallel Execution

```mermaid
gantt
    title Execution Time Comparison
    dateFormat X
    axisFormat %s

    section Sequential
    Node A (60s) :0, 60s
    Node B (40s) :60s, 100s
    Node C (30s) :100s, 130s

    section Parallel
    Node A (60s) :0, 60s
    Node B (40s) :crit, 0, 40s
    Node C (30s) :crit, 0, 30s
```

**Sequential**: 60s + 40s + 30s = **130s**
**Parallel**: max(60s, 40s, 30s) = **60s**
**Risparmio**: **54%**

---

## Legend

### Simboli Comuni

```mermaid
graph LR
    S([Start/End]) --> D{Decision}
    D --> P[Process]
    P --> DB[(Database)]
    DB --> E[End]

    P1[Parallel 1] -.->|async| Sync((Sync))
    P2[Parallel 2] -.->|async| Sync

    style S fill:#90EE90
    style D fill:#FFD700
    style P fill:#87CEEB
    style DB fill:#4682B4
    style Sync fill:#FF6347
```

**Colori**:
- 🟢 Verde: Start/Success
- 🔵 Blu: Processing
- 🟡 Giallo: Decision/Conditional
- 🔴 Rosso: Sync/Critical
- 🟣 Viola: MCP Tools
- 🌸 Rosa: Research/External

---

## Prossimi Passi

- [Cookbook →](05_cookbook.md) - Esempi pratici pronti all'uso
- [Migration Guide →](06_migration_guide.md) - Strategia migrazione ibrida
- [Creating Templates ←](01_creating_templates.md) - Crea i tuoi workflow

---

**Tip**: Usa [Mermaid Live Editor](https://mermaid.live/) per modificare/testare diagrammi.
