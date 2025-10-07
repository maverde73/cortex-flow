# Cortex Flow Web Editor - Stato del Progetto

**Ultimo aggiornamento**: 7 Ottobre 2025

---

## 📊 Panoramica Generale

### ✅ Completato (Fasi 1-2)
- **Backend API**: 100% completo (35+ endpoints)
- **Frontend Base**: 100% completo (routing, layout, integrazione API)
- **Tempo impiegato**: ~2 settimane (come da piano)

### 🚧 In Sviluppo
Nessuna fase attualmente in sviluppo

### ⏳ Da Completare (Fasi 3-9)
- **Fase 3**: Prompt Management (Settimana 3)
- **Fase 4**: Workflow Code Editor (Settimana 4)
- **Fase 5**: AI Workflow Generation (Settimana 5)
- **Fase 6**: Workflow Visual Editor (Settimane 6-7)
- **Fase 7**: MCP Integration (Settimana 8)
- **Fase 8**: Testing & Execution (Settimana 9)
- **Fase 9**: User Documentation (Settimana 10)

---

## ✅ Fase 1: Backend API - COMPLETATO

### Implementato

#### 1. **Projects API** (6 endpoints)
- `GET /api/projects` - Lista progetti
- `GET /api/projects/{name}` - Dettagli progetto
- `POST /api/projects` - Crea progetto
- `PUT /api/projects/{name}` - Aggiorna progetto
- `DELETE /api/projects/{name}` - Elimina progetto
- `POST /api/projects/{name}/activate` - Attiva progetto

#### 2. **Agents & ReAct API** (4 endpoints)
- `GET /api/projects/{name}/agents` - Config agenti
- `PUT /api/projects/{name}/agents` - Aggiorna agenti
- `GET /api/projects/{name}/react` - Config ReAct
- `PUT /api/projects/{name}/react` - Aggiorna ReAct

#### 3. **Prompts API** (7 endpoints)
- `GET /api/projects/{name}/prompts` - Lista prompt
- `GET/PUT /api/projects/{name}/prompts/system` - System prompt
- `GET/PUT /api/projects/{name}/prompts/agents/{agent}` - Agent prompts
- `GET/PUT /api/projects/{name}/prompts/mcp/{server}` - MCP prompts

#### 4. **Workflows API** (7 endpoints)
- `GET /api/projects/{name}/workflows` - Lista workflow
- `GET/POST/PUT/DELETE /api/projects/{name}/workflows/{workflow}` - CRUD
- `POST /api/projects/{name}/workflows/validate` - Validazione
- `POST /api/projects/{name}/workflows/{workflow}/preview` - Anteprima

#### 5. **MCP API** (8 endpoints)
- `GET /api/mcp/registry` - Registry MCP
- `GET /api/mcp/registry/{id}` - Dettagli server
- `GET/PUT /api/projects/{name}/mcp` - Config MCP progetto
- `POST /api/projects/{name}/mcp/test/{server}` - Test connessione
- `GET/POST/DELETE /api/mcp/library` - Libreria comune

#### 6. **AI Generation API** (1 endpoint)
- `POST /api/workflows/generate` - Genera workflow da descrizione

### File Creati
- `servers/editor_server.py` (1023 righe)
- `docs/editor/IMPLEMENTATION_GUIDE.md` (49KB)
- `docs/editor/README.md`
- `docs/editor/PHASE1_COMPLETED.md`

---

## ✅ Fase 2: Frontend Base - COMPLETATO

### Implementato

#### 1. **Setup Progetto**
- ⚡ Vite 7.1.9
- ⚛️ React 19.1 + TypeScript 5.9
- 🎨 Tailwind CSS 3.4

#### 2. **Routing & Navigation**
- React Router 7.9 con 6 route
- Layout con sidebar collassabile
- Navigazione SPA completa

#### 3. **API Integration**
- Axios client typed (35+ metodi)
- React Query per data fetching
- TypeScript types completi

#### 4. **State Management**
- Zustand store globale
- Current project tracking
- UI state (sidebar, loading, errors)

#### 5. **Pages**
- ✅ Dashboard (placeholder metriche)
- ✅ Projects (connesso al backend - mostra dati reali)
- 🚧 Workflows (placeholder - Fase 4)
- 🚧 Agents (placeholder)
- 🚧 Prompts (placeholder - Fase 3)
- 🚧 MCP (placeholder - Fase 7)

### File Creati (15 file)
```
frontend/
├── src/
│   ├── components/Layout.tsx
│   ├── pages/ (6 pages)
│   ├── services/api.ts
│   ├── store/useStore.ts
│   ├── types/api.ts
│   ├── App.tsx (modificato)
│   └── index.css (modificato)
├── .env
├── tailwind.config.js
├── postcss.config.js
└── package.json (modificato)
```

**Totale**: ~860 righe di codice

---

## 🚧 Cosa Manca - Roadmap Dettagliata

### Fase 3: Prompt Management (Settimana 3) ⏳

**Backend**: ✅ Già implementato (Fase 1)
- API prompts già disponibili

**Frontend da implementare**:

#### 1. Componente PromptEditor
```typescript
// src/components/PromptEditor.tsx
// - Monaco Editor per editing prompt
// - Syntax highlighting
// - Save/Cancel buttons
// - Character count
// - Template variables support
```

#### 2. Pagina Prompts
```typescript
// src/pages/PromptsPage.tsx (sostituire placeholder)
// - Tabs: System | Agents | MCP
// - Lista agent prompts (researcher, analyst, writer)
// - Lista MCP server prompts
// - Form per editing
// - Save/Load da API
```

#### 3. Features
- ✅ API già disponibile
- ⏳ Monaco Editor integration
- ⏳ Form handling con React Hook Form
- ⏳ Template variables ({{variable}})
- ⏳ Prompt versioning (opzionale)

**Stima**: 2-3 giorni

---

### Fase 4: Workflow Code Editor (Settimana 4) ⏳

**Backend**: ✅ Già implementato (Fase 1)
- API workflows già disponibili

**Frontend da implementare**:

#### 1. Workflow List Component
```typescript
// src/components/WorkflowList.tsx
// - Card per ogni workflow
// - Info: name, description, agents count
// - Actions: Edit, Delete, Duplicate, Preview
```

#### 2. Workflow Code Editor
```typescript
// src/components/WorkflowCodeEditor.tsx
// - Monaco Editor per JSON
// - JSON schema validation
// - Error highlighting
// - Auto-complete per agent types
// - Format button
```

#### 3. Workflow Preview
```typescript
// src/components/WorkflowPreview.tsx
// - Visualizza structure workflow
// - Agent steps breakdown
// - Routing diagram (text-based)
// - Estimated execution time
```

#### 4. Pagina Workflows
```typescript
// src/pages/WorkflowsPage.tsx (sostituire placeholder)
// - Lista workflow (da API)
// - Create new workflow button
// - Edit workflow (modal o page)
// - Validate button
// - Preview execution button
```

**Dipendenze da installare**:
```bash
npm install @monaco-editor/react
npm install react-hook-form @hookform/resolvers zod
```

**Stima**: 3-4 giorni

---

### Fase 5: AI Workflow Generation (Settimana 5) ⏳

**Backend**: 🚧 Parzialmente implementato
- ✅ Endpoint `/api/workflows/generate` esiste
- ⏳ OpenAI integration da implementare (attualmente mock)

**Backend da completare**:

#### 1. OpenAI Integration
```python
# servers/editor_server.py - generate_workflow()
# - Implementare chiamata OpenAI API
# - Prompt engineering per generazione workflow
# - Parsing JSON response
# - Validazione workflow generato
```

**Frontend da implementare**:

#### 1. AI Generation Modal
```typescript
// src/components/AIGenerationModal.tsx
// - Form: descrizione task (textarea)
// - Optional: agent types selection
// - Optional: MCP servers selection
// - Generate button
// - Progress indicator
// - Preview generated workflow
// - Accept/Edit/Regenerate buttons
```

#### 2. Integration con WorkflowsPage
- Button "Generate with AI" nella toolbar
- Modal per input descrizione
- Preview prima di salvare
- Save to project

**Stima**: 2-3 giorni (backend + frontend)

---

### Fase 6: Workflow Visual Editor (Settimane 6-7) ⏳

**Questa è la fase più complessa**

**Dipendenze da installare**:
```bash
npm install reactflow
npm install dagre  # Per auto-layout
```

**Frontend da implementare**:

#### 1. React Flow Integration
```typescript
// src/components/WorkflowVisualEditor.tsx
// - Canvas drag & drop
// - Custom node types (Agent, Condition, MCP, etc.)
// - Connection edges (routing)
// - Sidebar con palette nodi
// - Properties panel per nodo selezionato
```

#### 2. Custom Node Types
- **AgentNode**: Tipo agent, steps, config
- **ConditionNode**: If/else routing logic
- **MCPNode**: MCP tool call
- **StartNode**: Entry point
- **EndNode**: Exit point

#### 3. Features
- Drag & drop dalla palette
- Connect nodes (routing)
- Edit node properties
- Auto-layout button
- Zoom in/out, pan
- Minimap
- Export to JSON
- Import from JSON

#### 4. Sync con Code Editor
- Switch: Visual ⟺ Code
- Bi-directional sync
- Validation errors overlay

**Stima**: 5-7 giorni (feature complessa)

---

### Fase 7: MCP Integration (Settimana 8) ⏳

**Backend**: ✅ API base già implementata
- ⏳ MCP Registry real (attualmente mock)
- ⏳ MCP connection test real

**Backend da completare**:

#### 1. MCP Registry Real
```python
# Connessione a registry MCP ufficiale
# O scraping GitHub modelcontextprotocol/servers
```

#### 2. MCP Connection Test Real
```python
# Usare MCP client per test connessione reale
# Return tools disponibili
```

**Frontend da implementare**:

#### 1. MCP Registry Browser
```typescript
// src/pages/MCPPage.tsx (sostituire placeholder)
// - Lista server MCP da registry
// - Search/Filter
// - Card per ogni server con:
//   - Nome, descrizione
//   - Tools disponibili
//   - Repository link
//   - "Add to Project" button
```

#### 2. MCP Configuration
```typescript
// src/components/MCPConfig.tsx
// - Form per config server:
//   - Command
//   - Args
//   - Env variables
// - Test connection button
// - Status indicator
// - Tools list (dopo connessione)
```

#### 3. MCP Library
```typescript
// src/components/MCPLibrary.tsx
// - Server salvati nella libreria comune
// - Quick add to project
// - Edit/Delete
```

**Stima**: 3-4 giorni

---

### Fase 8: Testing & Execution (Settimana 9) ⏳

**Backend da implementare**:

#### 1. Workflow Execution API
```python
POST /api/projects/{name}/workflows/{workflow}/execute
# - Esegue workflow con LangGraph
# - Streaming logs
# - Return result
```

#### 2. Execution History API
```python
GET /api/projects/{name}/executions
GET /api/projects/{name}/executions/{id}
# - Storia esecuzioni
# - Logs, input, output
```

**Frontend da implementare**:

#### 1. Execution Panel
```typescript
// src/components/ExecutionPanel.tsx
// - Input form per workflow
// - Execute button
// - Real-time logs (streaming)
// - Result display
// - Error handling
```

#### 2. Execution History
```typescript
// src/components/ExecutionHistory.tsx
// - Lista esecuzioni passate
// - Timestamp, status, duration
// - View logs/results
```

#### 3. Integration
- Tab "Test" nel workflow editor
- Run button nella toolbar
- Real-time streaming

**Stima**: 4-5 giorni

---

### Fase 9: User Documentation (Settimana 10) ⏳

**Da creare**:

#### 1. User Guide
```markdown
docs/user/
├── getting-started.md
├── projects.md
├── workflows.md
├── prompts.md
├── mcp.md
├── agents.md
└── faq.md
```

#### 2. In-App Help
```typescript
// src/components/HelpPanel.tsx
// - Tooltips
// - Guided tours (react-joyride?)
// - Context-sensitive help
```

#### 3. Video Tutorials (opzionale)
- Quick start
- Create first workflow
- AI generation demo

**Stima**: 2-3 giorni

---

## 📦 Dipendenze Ancora da Installare

### Frontend (Fase 3+)
```bash
# Phase 3-4
npm install @monaco-editor/react
npm install react-hook-form @hookform/resolvers zod

# Phase 6
npm install reactflow
npm install dagre

# Optional (UI enhancement)
npm install @headlessui/react  # Modals, Dropdowns
npm install react-hot-toast     # Notifications
npm install react-joyride       # Guided tours
```

### Backend (Fase 5, 8)
```python
# Phase 5
pip install openai

# Phase 8
# Già disponibile: langgraph, langchain
```

---

## 🎯 Priorità Suggerite

### Essenziali (MVP)
1. ✅ **Fase 1**: Backend API
2. ✅ **Fase 2**: Frontend Base
3. ⏳ **Fase 4**: Workflow Code Editor (prima della visual)
4. ⏳ **Fase 5**: AI Generation (differenziatore chiave)
5. ⏳ **Fase 8**: Testing & Execution (must-have)

### Importanti
6. ⏳ **Fase 3**: Prompt Management
7. ⏳ **Fase 7**: MCP Integration

### Nice-to-Have
8. ⏳ **Fase 6**: Workflow Visual Editor (complesso, può essere v2.0)
9. ⏳ **Fase 9**: Documentation

---

## 🔧 Miglioramenti Opzionali

### Backend
- [ ] Authentication (JWT)
- [ ] Database per projects (PostgreSQL invece di file JSON)
- [ ] Workflow versioning
- [ ] Collaboration features (multi-user)
- [ ] Webhook notifications
- [ ] Metrics & analytics

### Frontend
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Command palette (Cmd+K)
- [ ] Undo/Redo per editor
- [ ] Diff viewer per versioning
- [ ] Mobile responsive
- [ ] Offline mode (PWA)

---

## 📊 Riepilogo Numerico

### Completato
- **Backend endpoints**: 35/35 (100%)
- **Frontend pages**: 2/6 funzionali (33%)
- **Fasi completate**: 2/9 (22%)
- **Tempo speso**: ~2 settimane
- **Righe codice**: ~1900

### Rimanente
- **Fasi da completare**: 7/9 (78%)
- **Tempo stimato**: ~8 settimane
- **Features principali**: 5 grandi features

---

## 🚀 Next Steps Consigliati

### Opzione A: Continuare in Sequenza
**Fase 3 → Fase 4 → Fase 5 → ...**
- Pro: Sviluppo ordinato
- Contro: Features chiave arrivano tardi

### Opzione B: Prioritizzare MVP
**Fase 4 → Fase 5 → Fase 8 → Fase 3 → Fase 7 → Fase 6 → Fase 9**
- Pro: Demo funzionante prima
- Contro: Salta alcuni step

### Opzione C: Focus AI-First
**Fase 5 → Fase 4 → Fase 8 → ...**
- Pro: Differenziatore principale subito
- Contro: Richiede OpenAI API key

---

## 💡 Conclusioni

### Stato Attuale: BUONO ✅
- Fondamenta solide (backend + frontend)
- API completa e funzionante
- Architettura scalabile
- TypeScript type-safe

### Cosa Funziona Ora
✅ Vedere lista progetti
✅ Creare/modificare progetti
✅ API completa per tutte le features
✅ Frontend responsive con routing

### Cosa Serve per MVP
⏳ Editor workflow (code)
⏳ AI generation workflow
⏳ Execution engine
⏳ Prompt management

### Tempo Stimato per MVP
**4-5 settimane** (Fasi 3, 4, 5, 8)

---

**Pronto per continuare con la Fase 3 (Prompt Management)?**
