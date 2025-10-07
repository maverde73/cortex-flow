"""
AI Service for Workflow Natural Language Conversion

Handles bidirectional conversion between workflow JSON and natural language descriptions
using OpenAI or Anthropic APIs.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered workflow conversions"""

    def __init__(self, project_name: str = "default", use_web_app_model: bool = False):
        self.project_name = project_name
        self.use_web_app_model = use_web_app_model
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        # Load project configuration
        self.agents_config = self._load_agents_config()

        # Determine which provider and model to use
        self.provider, self.model = self._get_configured_model()

        if self.provider:
            model_type = "web app" if use_web_app_model else "default"
            logger.info(f"AI Service initialized with {self.provider}/{self.model} ({model_type} model)")
        else:
            logger.warning("No AI API keys configured - AI features will use mock responses")

    def _load_agents_config(self) -> Optional[Dict[str, Any]]:
        """Load agents configuration from project"""
        try:
            projects_dir = Path(__file__).parent.parent / "projects"
            config_file = projects_dir / self.project_name / "agents.json"

            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load agents config for project {self.project_name}: {e}")

        return None

    def _get_configured_model(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get configured model from project settings or use fallback.

        Returns:
            Tuple of (provider, model_id)
        """
        # Try to get web_app_model or default_model from project config
        if self.agents_config:
            # Use web_app_model if requested and configured, otherwise use default_model
            model_key = "web_app_model" if self.use_web_app_model else "default_model"
            configured_model = self.agents_config.get(model_key)

            # Fallback to default_model if web_app_model not configured
            if not configured_model and self.use_web_app_model:
                configured_model = self.agents_config.get("default_model")

            if configured_model and "/" in configured_model:
                provider, model_id = configured_model.split("/", 1)

                # Check if we have API key for this provider
                if self._has_api_key(provider):
                    return provider, model_id

        # Fallback to first available provider
        if self.openai_api_key:
            return "openai", "gpt-4-turbo-preview"
        elif self.anthropic_api_key:
            return "anthropic", "claude-3-5-sonnet-20241022"
        elif self.google_api_key:
            return "google", "gemini-1.5-pro"
        elif self.groq_api_key:
            return "groq", "llama-3.3-70b-versatile"
        elif self.openrouter_api_key:
            return "openrouter", "meta-llama/llama-3.3-70b-instruct"

        return None, None

    def _has_api_key(self, provider: str) -> bool:
        """Check if API key is configured for provider"""
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
            "groq": self.groq_api_key,
            "openrouter": self.openrouter_api_key
        }
        return bool(key_map.get(provider))

    async def workflow_to_natural_language(
        self,
        workflow: Dict[str, Any],
        language: str = "it"
    ) -> str:
        """
        Convert workflow JSON to natural language description.

        Args:
            workflow: Workflow JSON object
            language: Target language (default: "it" for Italian)

        Returns:
            Natural language description
        """
        if not self.provider:
            return self._mock_workflow_to_nl(workflow, language)

        system_prompt = self._get_to_nl_system_prompt(language)
        user_prompt = f"Converti questo workflow in una descrizione dettagliata:\n\n{json.dumps(workflow, indent=2, ensure_ascii=False)}"

        if self.provider == "openai":
            return await self._call_openai(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, user_prompt)
        elif self.provider == "openrouter":
            return await self._call_openrouter(system_prompt, user_prompt)
        elif self.provider == "google":
            return await self._call_google(system_prompt, user_prompt)
        elif self.provider == "groq":
            return await self._call_groq(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def natural_language_to_workflow(
        self,
        description: str,
        language: str = "it"
    ) -> Dict[str, Any]:
        """
        Convert natural language description to workflow JSON.

        Args:
            description: Natural language workflow description
            language: Source language (default: "it" for Italian)

        Returns:
            Workflow JSON object
        """
        if not self.provider:
            return self._mock_nl_to_workflow(description, language)

        system_prompt = self._get_from_nl_system_prompt(language)
        user_prompt = f"Converti questa descrizione in un workflow JSON valido:\n\n{description}"

        if self.provider == "openai":
            result = await self._call_openai(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            result = await self._call_anthropic(system_prompt, user_prompt)
        elif self.provider == "openrouter":
            result = await self._call_openrouter(system_prompt, user_prompt)
        elif self.provider == "google":
            result = await self._call_google(system_prompt, user_prompt)
        elif self.provider == "groq":
            result = await self._call_groq(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Parse JSON from result
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            return json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response: {result}")
            raise ValueError(f"AI generated invalid JSON: {str(e)}")

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model=self.model,  # Use configured model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API"""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.anthropic_api_key)

            response = await client.messages.create(
                model=self.model,  # Use configured model
                max_tokens=4000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def _call_openrouter(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenRouter API (uses OpenAI-compatible interface)"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )

            response = await client.chat.completions.create(
                model=self.model,  # Use configured model (e.g., meta-llama/llama-3.3-70b-instruct)
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

    async def _call_google(self, system_prompt: str, user_prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.google_api_key)
            model = genai.GenerativeModel(self.model)

            # Gemini doesn't have separate system/user, combine them
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = await model.generate_content_async(
                combined_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )

            return response.text

        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise

    async def _call_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Call Groq API (uses OpenAI-compatible interface)"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )

            response = await client.chat.completions.create(
                model=self.model,  # Use configured model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def _get_to_nl_system_prompt(self, language: str) -> str:
        """Get system prompt for workflow → natural language conversion"""
        lang_name = "italiano" if language == "it" else "English"

        return f"""Sei un esperto di workflow automation. Converti workflow JSON/YAML in descrizioni dettagliate in {lang_name}.

WORKFLOW SCHEMA (WorkflowTemplate):
- name: nome univoco del workflow
- version: versione (es. "1.0")
- description: descrizione generale
- trigger_patterns: pattern regex per attivazione automatica
- parameters: parametri di input con valori default
- nodes: lista di nodi/passi del workflow
  - id: identificatore univoco del nodo
  - agent: tipo agente (supervisor, researcher, analyst, writer, mcp_tool)
  - instruction: istruzioni dettagliate per l'agente
  - depends_on: lista di id di nodi da cui dipende
  - timeout: timeout in secondi (default 120)
  - tool_name: nome tool MCP (solo se agent="mcp_tool")
  - parallel_group: gruppo per esecuzione parallela
  - params: parametri specifici del nodo
- conditional_edges: routing condizionale (opzionale)
  - from_node: nodo sorgente
  - conditions: lista di condizioni if/then
    - field: campo da valutare
    - operator: operatore (equals, not_equals, >, <, >=, <=, contains, in)
    - value: valore di confronto
    - next_node: nodo destinazione se condizione vera
  - default: nodo destinazione se nessuna condizione è vera

FORMATO OUTPUT:
Genera una descrizione strutturata che spiega:
1. **SCOPO**: cosa fa il workflow (in 1-2 frasi)
2. **PARAMETRI**: parametri di configurazione (se presenti)
3. **PASSI**: per ogni node, spiega in modo chiaro e dettagliato:
   - Nome e ruolo
   - Cosa fa (basandoti su instruction)
   - Da quali step dipende
   - Configurazioni speciali (timeout, tool MCP, gruppo parallelo)
4. **ROUTING**: logica di flusso, specialmente se ci sono conditional_edges
5. **PATTERN**: pattern di attivazione (se presenti)

USA UN LINGUAGGIO CHIARO E COMPRENSIBILE ANCHE A NON TECNICI.
Evita di ripetere l'instruction verbatim se troppo tecnica - riassumila in modo comprensibile.
Se ci sono template variables ({{variabile}}), spiegale nel contesto.

ESEMPIO:

Input Workflow:
{{
  "name": "newsletter",
  "description": "Genera newsletter settimanale",
  "parameters": {{"topic": "AI", "audience": "developers"}},
  "nodes": [
    {{"id": "research", "agent": "researcher", "instruction": "Ricerca trend su {{topic}}", "depends_on": [], "timeout": 300}},
    {{"id": "write", "agent": "writer", "instruction": "Scrivi newsletter per {{audience}}", "depends_on": ["research"]}}
  ]
}}

Output Descrizione:
**SCOPO**
Questo workflow genera automaticamente una newsletter settimanale su un argomento specifico.

**PARAMETRI**
- topic: argomento da ricercare (default: "AI")
- audience: pubblico target (default: "developers")

**PASSI**

1. RICERCA (research)
   - Agente: Researcher (ricercatore)
   - Compito: Cerca i trend e le novità più recenti sull'argomento specificato
   - Timeout: 5 minuti
   - Nessuna dipendenza (step iniziale)

2. SCRITTURA (write)
   - Agente: Writer (scrittore)
   - Compito: Crea la newsletter personalizzata per il pubblico target, basandosi sui risultati della ricerca
   - Dipende da: ricerca completata
   - Timeout: 2 minuti (default)

**FLUSSO**
research → write → END

Ora converti il workflow fornito seguendo questo formato."""

    def _get_from_nl_system_prompt(self, language: str) -> str:
        """Get system prompt for natural language → workflow conversion"""
        return """Sei un esperto di workflow automation. Converti descrizioni in italiano in workflow JSON validi.

WORKFLOW SCHEMA (WorkflowTemplate):
{
  "name": "workflow_name",           // Nome univoco (lowercase, underscore)
  "version": "1.0",                  // Versione
  "description": "Descrizione...",   // Descrizione generale
  "trigger_patterns": [              // Opzionale: pattern regex
    "pattern1",
    "pattern2"
  ],
  "parameters": {                    // Opzionale: parametri default
    "param_name": "default_value"
  },
  "nodes": [
    {
      "id": "node_id",               // ID univoco (lowercase, underscore)
      "agent": "agent_type",         // supervisor | researcher | analyst | writer | mcp_tool
      "instruction": "...",          // Istruzioni dettagliate
      "depends_on": ["node_id"],     // Array di ID nodi ([] se iniziale)
      "timeout": 120,                // Opzionale: timeout secondi (default 120)
      "tool_name": "tool_name",      // Solo se agent="mcp_tool"
      "parallel_group": "group",     // Opzionale: gruppo esecuzione parallela
      "params": {}                   // Opzionale: parametri specifici
    }
  ],
  "conditional_edges": [             // Opzionale: routing condizionale
    {
      "from_node": "node_id",
      "conditions": [
        {
          "field": "field_path",     // es: "custom_metadata.has_error"
          "operator": "equals",      // equals | not_equals | > | < | >= | <= | contains | in
          "value": true,
          "next_node": "node_id"
        }
      ],
      "default": "node_id"           // Nodo default se nessuna condizione match
    }
  ]
}

REGOLE OBBLIGATORIE:
1. Ogni node DEVE avere un id univoco
2. depends_on può essere [] (nodo iniziale) o lista di id esistenti
3. agent DEVE essere uno tra: supervisor, researcher, analyst, writer, mcp_tool
4. Se agent="mcp_tool", DEVE avere tool_name
5. timeout in secondi (ometti se 120, è il default)
6. conditional_edges è OPZIONALE, usa solo se esplicitamente menzionato routing condizionale/if-then/retry
7. name DEVE essere lowercase con underscore (es: "database_query")

MAPPING SEMANTICO (italiano → JSON):
- "ricerca" / "cerca" → agent: "researcher"
- "analizza" / "valuta" → agent: "analyst"
- "scrivi" / "genera testo" → agent: "writer"
- "supervisore" / "coordina" → agent: "supervisor"
- "tool MCP" / "chiama API" → agent: "mcp_tool"
- "dipende da X" → depends_on: ["x"]
- "in parallelo con X" → parallel_group: "group_name"
- "se... allora..." → conditional_edges
- "riprova" / "retry" → conditional_edges con default che torna al nodo precedente

ESEMPI:

Esempio 1 - Semplice:
Descrizione: "Workflow che ricerca informazioni su un topic e poi scrive un report"
Output:
{
  "name": "research_report",
  "version": "1.0",
  "description": "Ricerca informazioni e genera report",
  "parameters": {"topic": "default_topic"},
  "nodes": [
    {
      "id": "research",
      "agent": "researcher",
      "instruction": "Ricerca informazioni dettagliate su {topic}",
      "depends_on": []
    },
    {
      "id": "write_report",
      "agent": "writer",
      "instruction": "Scrivi un report basato sui risultati della ricerca: {research}",
      "depends_on": ["research"]
    }
  ]
}

Esempio 2 - Con conditional routing:
Descrizione: "Query database, se c'è errore riprova, altrimenti procedi con analisi"
Output:
{
  "name": "database_query_retry",
  "version": "1.0",
  "description": "Query database con retry su errore",
  "nodes": [
    {
      "id": "execute_query",
      "agent": "mcp_tool",
      "tool_name": "query_database",
      "instruction": "Esegui query: {query}",
      "depends_on": []
    },
    {
      "id": "check_result",
      "agent": "analyst",
      "instruction": "Verifica se query è riuscita. Output: has_error: true/false",
      "depends_on": ["execute_query"]
    },
    {
      "id": "analyze",
      "agent": "analyst",
      "instruction": "Analizza i risultati",
      "depends_on": ["check_result"]
    }
  ],
  "conditional_edges": [
    {
      "from_node": "check_result",
      "conditions": [
        {
          "field": "custom_metadata.has_error",
          "operator": "equals",
          "value": false,
          "next_node": "analyze"
        }
      ],
      "default": "execute_query"
    }
  ]
}

IMPORTANTE:
- Restituisci SOLO JSON valido, NESSUN testo prima o dopo
- Se devi fare assunzioni, scegli l'opzione più semplice e ragionevole
- Non inventare field/operator non presenti nella spec
- Se la descrizione è ambigua, crea un workflow funzionante e sensato

Ora converti la descrizione fornita in JSON."""

    def _mock_workflow_to_nl(self, workflow: Dict[str, Any], language: str) -> str:
        """Mock conversion for when no AI API is available"""
        name = workflow.get("name", "workflow")
        description = workflow.get("description", "")
        nodes = workflow.get("nodes", [])

        nl = f"**SCOPO**\n{description}\n\n**PASSI**\n\n"

        for i, node in enumerate(nodes, 1):
            nl += f"{i}. {node.get('id', 'step').upper()} ({node.get('agent', 'unknown')})\n"
            nl += f"   - {node.get('instruction', 'N/A')[:100]}...\n"
            if node.get('depends_on'):
                nl += f"   - Dipende da: {', '.join(node['depends_on'])}\n"
            nl += "\n"

        nl += "\n(Descrizione generata automaticamente - configura OPENAI_API_KEY o ANTHROPIC_API_KEY per descrizioni migliori)"

        return nl

    def _mock_nl_to_workflow(self, description: str, language: str) -> Dict[str, Any]:
        """Mock conversion for when no AI API is available"""
        return {
            "name": "generated_workflow",
            "version": "1.0",
            "description": description[:200],
            "nodes": [
                {
                    "id": "step1",
                    "agent": "researcher",
                    "instruction": "Esegui il compito descritto",
                    "depends_on": []
                }
            ]
        }

    async def chat_modify_workflow(
        self,
        workflow: Dict[str, Any],
        user_message: str,
        conversation_history: list[Dict[str, str]],
        language: str = "it"
    ) -> Dict[str, Any]:
        """
        Modify workflow through conversational AI chat.

        Args:
            workflow: Current workflow JSON object
            user_message: User's modification request
            conversation_history: List of {role: "user"|"assistant", content: str}
            language: Language for conversation (default: "it")

        Returns:
            Dict with:
                - workflow: Modified workflow JSON
                - explanation: What was changed and why
                - changes: List of specific modifications made
        """
        if not self.provider:
            return self._mock_chat_modify(workflow, user_message)

        system_prompt = self._get_chat_modify_system_prompt(language)

        # Build conversation context
        conversation = ""
        for msg in conversation_history:
            role = "Utente" if msg["role"] == "user" else "Assistente"
            conversation += f"\n{role}: {msg['content']}\n"

        user_prompt = f"""
Workflow Corrente:
```json
{json.dumps(workflow, indent=2, ensure_ascii=False)}
```

Storico Conversazione:
{conversation}

Nuova Richiesta Utente:
{user_message}

Rispondi in formato JSON:
{{
  "workflow": {{...}},
  "explanation": "Spiegazione delle modifiche in italiano",
  "changes": ["Modifica 1", "Modifica 2", ...]
}}
"""

        try:
            if self.provider == "openai":
                response_text = await self._call_openai(system_prompt, user_prompt)
            else:  # anthropic
                response_text = await self._call_anthropic(system_prompt, user_prompt)

            # Parse JSON response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)

            logger.info(f"Chat modification successful: {len(result.get('changes', []))} changes")
            return result

        except Exception as e:
            logger.error(f"Chat modification error: {e}")
            raise

    def _get_chat_modify_system_prompt(self, language: str) -> str:
        """System prompt for chat-based workflow modification"""
        if language == "it":
            return """Sei un assistente esperto per la modifica di workflow JSON tramite conversazione in italiano.

Il tuo compito è:
1. Comprendere la richiesta dell'utente in linguaggio naturale
2. Applicare modifiche INCREMENTALI al workflow JSON esistente
3. Validare che le modifiche siano corrette
4. Spiegare chiaramente cosa hai modificato

SCHEMA WORKFLOW JSON COMPLETO:
```json
{
  "name": "string",
  "version": "string",
  "description": "string",
  "nodes": [
    {
      "id": "string (univoco)",
      "agent": "researcher | analyst | writer | mcp_tool | supervisor",
      "instruction": "string (istruzione dettagliata per l'agente)",
      "depends_on": ["id_nodo1", "id_nodo2"],
      "timeout": 300 (opzionale, secondi),
      "tool_name": "string (solo per agent=mcp_tool)",
      "params": {"key": "value"} (opzionale),
      "template": "string (opzionale)",
      "parallel_group": "string (opzionale, per esecuzione parallela)"
    }
  ],
  "conditional_edges": [
    {
      "from_node": "id_nodo",
      "conditions": [
        {
          "field": "has_error",
          "operator": "eq | ne | gt | lt | contains",
          "value": true,
          "next_node": "id_nodo_destinazione"
        }
      ],
      "default": "id_nodo_default"
    }
  ],
  "parameters": {
    "param_name": "default_value"
  },
  "trigger_patterns": ["regex1", "regex2"]
}
```

TIPI DI MODIFICHE COMUNI:

1. **Aggiungere Nodo**:
   - Crea nuovo nodo con id univoco
   - Aggiungi dipendenze corrette in depends_on
   - Se deve essere parallelo, usa parallel_group

2. **Modificare Nodo Esistente**:
   - Cambia timeout: modifica campo "timeout"
   - Cambia istruzione: modifica campo "instruction"
   - Cambia dipendenze: modifica array "depends_on"
   - Cambia agente: modifica campo "agent"

3. **Aggiungere Logica Condizionale**:
   - Aggiungi conditional_edge con from_node, conditions, default
   - Operators: "eq"=uguale, "ne"=diverso, "gt"=maggiore, "lt"=minore, "contains"=contiene

4. **Aggiungere Retry Logic**:
   - Crea conditional_edge che controlla has_error
   - Se has_error=true, ritorna a nodo precedente o nodo di retry

5. **Parallel Execution**:
   - Assegna stesso parallel_group a nodi che devono eseguire in parallelo
   - Aggiungi nodo di sincronizzazione che dipende da tutti: depends_on: ["nodo1", "nodo2"]

ESEMPI DI RICHIESTE:

Utente: "aggiungi un timeout di 10 minuti al nodo di ricerca"
→ Trova nodo con agent="researcher", aggiungi "timeout": 600

Utente: "se la query fallisce, riprova massimo 3 volte"
→ Aggiungi conditional_edge che controlla has_error=true
→ Aggiungi parametro retry_count
→ Crea logica di retry con max 3 tentativi

Utente: "esegui ricerca e analisi in parallelo"
→ Assegna parallel_group="group1" a nodi ricerca e analisi
→ Crea nodo di merge che depends_on: ["ricerca", "analisi"]

REGOLE IMPORTANTI:
- NON riscrivere tutto il workflow, fai solo modifiche INCREMENTALI
- Preserva tutti i campi esistenti che non devono essere modificati
- Genera id univoci per nuovi nodi (usa snake_case)
- Valida che depends_on riferisca nodi esistenti
- Spiega sempre cosa hai modificato e perché
- Se richiesta ambigua, chiedi chiarimenti invece di indovinare

OUTPUT FORMATO JSON:
```json
{
  "workflow": { /* workflow completo modificato */ },
  "explanation": "Ho modificato il nodo 'search' aggiungendo timeout di 600 secondi (10 minuti). Questo previene che la ricerca si blocchi indefinitamente.",
  "changes": [
    "Aggiunto timeout: 600 al nodo 'search'",
    "Modificato campo instruction del nodo 'analyze' per includere validazione risultati"
  ]
}
```

Rispondi SEMPRE in formato JSON valido. Mai testo libero."""
        else:  # English or other languages
            return """You are an expert assistant for modifying workflow JSON through conversational natural language.

[English version of the prompt - similar structure to Italian]

IMPORTANT RULES:
- Make INCREMENTAL modifications only
- Preserve existing fields that shouldn't change
- Generate unique IDs for new nodes
- Validate that depends_on references existing nodes
- Always explain what you modified and why

Always respond in valid JSON format."""

    def _mock_chat_modify(self, workflow: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """Mock chat modification when no AI API is available"""
        return {
            "workflow": workflow,
            "explanation": f"Modifica simulata per: {user_message}. Configura OPENAI_API_KEY o ANTHROPIC_API_KEY per modifiche reali.",
            "changes": [
                "Nessuna modifica effettuata (modalità mock)"
            ]
        }

    async def generate_workflow_from_description(
        self,
        description: str,
        agent_types: Optional[list[str]] = None,
        mcp_servers: Optional[list[str]] = None,
        language: str = "it"
    ) -> Dict[str, Any]:
        """
        Generate complete workflow JSON from natural language description.

        Args:
            description: Natural language description of the workflow
            agent_types: Optional list of preferred agent types
            mcp_servers: Optional list of required MCP servers
            language: Language for processing (default: "it")

        Returns:
            Workflow JSON object (WorkflowTemplate format)
        """
        if not self.provider:
            return self._mock_workflow_generation(description, agent_types)

        system_prompt = self._get_workflow_generation_system_prompt(language)

        # Build user prompt with constraints
        user_prompt = f"Genera un workflow completo per il seguente compito:\n\n{description}"

        if agent_types:
            user_prompt += f"\n\nAgent types preferiti: {', '.join(agent_types)}"

        if mcp_servers:
            user_prompt += f"\n\nMCP servers richiesti: {', '.join(mcp_servers)}"

        user_prompt += "\n\nRispondi SOLO con il JSON del workflow, nessun testo aggiuntivo."

        try:
            if self.provider == "openai":
                result = await self._call_openai(system_prompt, user_prompt)
            elif self.provider == "anthropic":
                result = await self._call_anthropic(system_prompt, user_prompt)
            elif self.provider == "openrouter":
                result = await self._call_openrouter(system_prompt, user_prompt)
            elif self.provider == "google":
                result = await self._call_google(system_prompt, user_prompt)
            elif self.provider == "groq":
                result = await self._call_groq(system_prompt, user_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Parse JSON from result
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            workflow = json.loads(result)

            logger.info(f"Generated workflow '{workflow.get('name')}' with {len(workflow.get('nodes', []))} nodes")
            return workflow

        except Exception as e:
            logger.error(f"Workflow generation error: {e}")
            raise

    def _get_workflow_generation_system_prompt(self, language: str) -> str:
        """System prompt for generating workflows from scratch"""
        return """Sei un esperto di workflow automation. Genera workflow JSON completi da descrizioni in linguaggio naturale.

WORKFLOW SCHEMA (WorkflowTemplate):
{
  "name": "workflow_name",           // Nome univoco (lowercase, underscore)
  "version": "1.0",                  // Versione
  "description": "Descrizione...",   // Descrizione generale
  "trigger_patterns": [              // Opzionale: pattern regex
    "pattern1"
  ],
  "parameters": {                    // Opzionale: parametri default
    "param_name": "default_value"
  },
  "nodes": [
    {
      "id": "node_id",               // ID univoco (lowercase, underscore)
      "agent": "agent_type",         // supervisor | researcher | analyst | writer | mcp_tool
      "instruction": "...",          // Istruzioni dettagliate per l'agente
      "depends_on": ["node_id"],     // Array di ID nodi ([] se iniziale)
      "timeout": 120,                // Opzionale: timeout secondi (default 120)
      "tool_name": "tool_name",      // Solo se agent="mcp_tool"
      "parallel_group": "group",     // Opzionale: gruppo esecuzione parallela
      "params": {}                   // Opzionale: parametri specifici
    }
  ],
  "conditional_edges": [             // Opzionale: routing condizionale
    {
      "from_node": "node_id",
      "conditions": [
        {
          "field": "field_path",
          "operator": "equals",      // equals | not_equals | > | < | >= | <= | contains | in
          "value": true,
          "next_node": "node_id"
        }
      ],
      "default": "node_id"
    }
  ]
}

AGENT TYPES:
- researcher: Ricerca informazioni (web, documenti, database)
- analyst: Analizza dati, valuta risultati, prende decisioni
- writer: Genera testi, report, documentazione
- supervisor: Coordina altri agenti, gestisce workflow complessi
- mcp_tool: Chiama tool MCP specifici (richiede tool_name)

BEST PRACTICES:
1. Crea flussi logici e sequenziali
2. Usa depends_on per definire l'ordine di esecuzione
3. Usa parallel_group per task indipendenti che possono eseguire in parallelo
4. Aggiungi conditional_edges solo se necessario (retry, routing basato su risultati)
5. Istruzioni dettagliate e specifiche per ogni node
6. Usa parametri ({{param_name}}) per valori configurabili

ESEMPI:

Esempio 1 - Ricerca e Report:
Descrizione: "Ricerca trend AI e genera report"
Output:
{
  "name": "ai_research_report",
  "version": "1.0",
  "description": "Ricerca trend AI e genera report dettagliato",
  "parameters": {"topic": "AI", "depth": "comprehensive"},
  "nodes": [
    {
      "id": "research",
      "agent": "researcher",
      "instruction": "Ricerca i trend più recenti su {{topic}}. Includi fonti autorevoli, statistiche e case study.",
      "depends_on": [],
      "timeout": 300
    },
    {
      "id": "analyze",
      "agent": "analyst",
      "instruction": "Analizza i risultati della ricerca. Identifica pattern, trend emergenti e insights chiave.",
      "depends_on": ["research"]
    },
    {
      "id": "write_report",
      "agent": "writer",
      "instruction": "Scrivi un report {{depth}} basato sull'analisi. Struttura: Executive Summary, Trend Analysis, Key Insights, Conclusions.",
      "depends_on": ["analyze"]
    }
  ]
}

Esempio 2 - Con MCP Tools:
Descrizione: "Query database e se ci sono errori riprova"
Output:
{
  "name": "database_query_retry",
  "version": "1.0",
  "description": "Esegue query database con retry automatico su errore",
  "parameters": {"query": "SELECT * FROM users"},
  "nodes": [
    {
      "id": "execute_query",
      "agent": "mcp_tool",
      "tool_name": "sqlite_query",
      "instruction": "Esegui query: {{query}}",
      "depends_on": []
    },
    {
      "id": "check_result",
      "agent": "analyst",
      "instruction": "Verifica se la query è riuscita. Controlla errori e validità risultati. Output: {has_error: true/false, retry_count: N}",
      "depends_on": ["execute_query"]
    }
  ],
  "conditional_edges": [
    {
      "from_node": "check_result",
      "conditions": [
        {
          "field": "custom_metadata.has_error",
          "operator": "equals",
          "value": false,
          "next_node": "END"
        }
      ],
      "default": "execute_query"
    }
  ]
}

REGOLE OUTPUT:
- Restituisci SOLO JSON valido, NESSUN testo prima/dopo
- Crea workflow funzionanti e realistici
- Usa nomi descrittivi per ID nodi
- Bilancia complessità e praticità
- Se mancano dettagli, fai assunzioni ragionevoli

Ora genera il workflow richiesto."""

    def _mock_workflow_generation(self, description: str, agent_types: Optional[list[str]]) -> Dict[str, Any]:
        """Mock workflow generation when no AI is available"""
        types = agent_types or ["researcher", "analyst", "writer"]

        nodes = []
        for i, agent_type in enumerate(types):
            nodes.append({
                "id": f"{agent_type}_{i+1}",
                "agent": agent_type,
                "instruction": f"Esegui task di {agent_type} per: {description[:100]}",
                "depends_on": [] if i == 0 else [f"{types[i-1]}_{i}"]
            })

        return {
            "name": "generated_workflow",
            "version": "1.0",
            "description": description[:200],
            "nodes": nodes
        }
