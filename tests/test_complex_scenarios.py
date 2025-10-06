#!/usr/bin/env python3
"""
Test scenari complessi che combinano:
- Query database via MCP (json_query_sse)
- Web research (researcher agent)
- Data analysis (analyst agent)
- Report generation (writer agent)
"""
import requests
import json
import time

def test_scenario(scenario_num, title, task_description):
    """Execute a test scenario"""
    print(f"\n{'='*80}")
    print(f"SCENARIO {scenario_num}: {title}")
    print(f"{'='*80}\n")

    payload = {
        "task_id": f"test-complex-{scenario_num}",
        "source_agent_id": "user",
        "target_agent_id": "supervisor",
        "task_description": task_description,
        "context": {},
        "response": None
    }

    print(f"📤 Task: {task_description}\n")

    start_time = time.time()

    try:
        response = requests.post(
            "http://localhost:8000/invoke",
            json=payload,
            timeout=180  # 3 minuti per scenari complessi
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request successful! (took {elapsed:.1f}s)")
            print(f"\n📊 Status: {result.get('status', 'unknown')}")

            metadata = result.get('metadata', {})
            print(f"📈 Metadata:")
            print(f"   - Messages: {metadata.get('message_count', 0)}")
            print(f"   - Agents used: {metadata.get('agents_used', [])}")

            if "result" in result and result["result"]:
                print(f"\n💡 Response:")
                response_text = result["result"]
                # Mostra primi 800 caratteri
                if len(response_text) > 800:
                    print(response_text[:800] + "\n... (truncated)")
                else:
                    print(response_text)

            print(f"\n⏱️  Total time: {elapsed:.2f} seconds")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all complex test scenarios"""

    print("\n" + "="*80)
    print("🧪 COMPLEX SCENARIOS TEST - Multi-Agent + Database Queries")
    print("="*80)

    scenarios = [
        {
            "num": 1,
            "title": "Database Query + Analysis",
            "task": """Interroga il database per ottenere i dipendenti con certificazioni AWS (usa json_query_sse con una JOIN tra employees e employee_certifications, filtrando per certification_name LIKE 'AWS%').

Poi analizza i risultati e crea un breve report che includa:
1. Numero totale di dipendenti con certificazioni AWS
2. Quali certificazioni AWS sono presenti
3. Una raccomandazione su eventuali gap di competenze AWS"""
        },

        {
            "num": 2,
            "title": "Database + Web Research + Comparative Analysis",
            "task": """Prima interroga il database per ottenere le top 3 certificazioni più comuni tra i nostri dipendenti (usa json_query_sse con GROUP BY e COUNT su employee_certifications).

Poi ricerca sul web quali sono le certificazioni tech più richieste nel mercato del lavoro nel 2025.

Infine, crea un'analisi comparativa che evidenzi:
1. Le nostre certificazioni attuali
2. Le certificazioni più richieste dal mercato
3. I gap da colmare
4. Raccomandazioni prioritarie"""
        },

        {
            "num": 3,
            "title": "Complex Database Query + Professional Report",
            "task": """Interroga il database per ottenere un report completo sui progetti (usa json_query_sse):
- Progetti attivi vs completati (raggruppa per status)
- Budget totale allocato
- Progetti per cliente (top 5 clienti)

Poi crea un executive report professionale con:
1. Executive Summary
2. Key Metrics (in formato tabellare)
3. Insights chiave
4. Raccomandazioni strategiche"""
        },

        {
            "num": 4,
            "title": "Employee Skills + Market Trends + Strategic Plan",
            "task": """Esegui questa analisi multi-step:

STEP 1 - Database: Interroga le competenze tecniche dei dipendenti (query su skills table per vedere quali skill sono più comuni)

STEP 2 - Web Research: Ricerca le competenze tecniche più richieste nel settore IT nel 2025

STEP 3 - Analysis: Compara le nostre skill con quelle richieste dal mercato

STEP 4 - Report: Crea un piano strategico di formazione con:
- Gap analysis dettagliata
- Priorità di formazione
- Timeline suggerita
- KPI per monitorare il progresso"""
        },

        {
            "num": 5,
            "title": "Comprehensive Workforce Analysis",
            "task": """Crea un'analisi completa della forza lavoro combinando:

DATABASE QUERIES:
1. Numero dipendenti per dipartimento
2. Distribuzione delle seniority/posizioni
3. Progetti attivi e loro team

WEB RESEARCH:
1. Trend di remote work nel 2025
2. Best practices per employee engagement

ANALYSIS & REPORT:
Crea un report esecutivo che includa:
- Snapshot attuale della forza lavoro (con dati dal DB)
- Benchmark con trend di mercato
- Raccomandazioni per migliorare engagement e produttività
- Action plan concreto"""
        }
    ]

    results = []

    for scenario in scenarios:
        success = test_scenario(
            scenario["num"],
            scenario["title"],
            scenario["task"]
        )
        results.append({
            "scenario": scenario["num"],
            "title": scenario["title"],
            "success": success
        })

        # Pausa tra scenari
        if scenario["num"] < len(scenarios):
            print("\n⏸️  Pausing 5 seconds before next scenario...")
            time.sleep(5)

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")

    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - Scenario {result['scenario']}: {result['title']}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n🎯 Total: {success_count}/{len(results)} scenarios passed")

    print("\n" + "="*80)
    print("✨ Complex scenarios test completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
