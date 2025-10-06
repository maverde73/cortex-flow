#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         CORTEX FLOW - Multi-Agent AI System                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Project Structure:"
echo ""
tree -L 2 -I '.venv|__pycache__|*.pyc|.git' --dirsfirst

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Implementation Statistics:"
echo "═══════════════════════════════════════════════════════════════"

echo "Agents: $(find agents -name '*.py' ! -name '__init__.py' | wc -l)"
echo "Servers: $(find servers -name '*.py' ! -name '__init__.py' | wc -l)"
echo "Tools: $(find tools -name '*.py' ! -name '__init__.py' | wc -l)"
echo "Schemas: $(find schemas -name '*.py' ! -name '__init__.py' | wc -l)"
echo "Total Python files: $(find . -name '*.py' ! -path './.venv/*' | wc -l)"
echo "Total Lines of Code: $(find . -name '*.py' ! -path './.venv/*' -exec wc -l {} + | tail -1 | awk '{print $1}')"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Quick Commands:"
echo "═══════════════════════════════════════════════════════════════"
echo "Start system:  ./scripts/start_all.sh"
echo "Stop system:   ./scripts/stop_all.sh"
echo "Test system:   python tests/test_system.py"
echo "View docs:     cat README.md"
echo "View examples: cat EXAMPLES.md"
echo ""
