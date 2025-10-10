#!/usr/bin/env python3
"""
Generate PDF Documentation for Cortex-Flow
Creates a professional PDF document with all project information.
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    ListFlowable,
    ListItem,
    KeepTogether,
    Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# Custom colors matching the HTML theme
PRIMARY_COLOR = HexColor('#6366f1')
SECONDARY_COLOR = HexColor('#8b5cf6')
ACCENT_COLOR = HexColor('#ec4899')
DARK_BG = HexColor('#0f172a')
LIGHT_BG = HexColor('#1e293b')
TEXT_PRIMARY = HexColor('#1e293b')
TEXT_SECONDARY = HexColor('#475569')
SUCCESS_COLOR = HexColor('#10b981')

class GradientBackground(Flowable):
    """Custom flowable for gradient backgrounds"""
    def __init__(self, width, height, color1, color2):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color1 = color1
        self.color2 = color2

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        # Simple gradient effect
        for i in range(100):
            ratio = i / 100.0
            r = self.color1.red * (1-ratio) + self.color2.red * ratio
            g = self.color1.green * (1-ratio) + self.color2.green * ratio
            b = self.color1.blue * (1-ratio) + self.color2.blue * ratio
            canvas.setFillColorRGB(r, g, b)
            canvas.rect(0, self.height * i/100, self.width, self.height/100, fill=1, stroke=0)
        canvas.restoreState()

class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbers and headers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(TEXT_SECONDARY)
        self.drawRightString(
            letter[0] - inch/2,
            inch/2,
            f"Page {self._pageNumber} of {page_count}"
        )
        # Header
        self.setFillColor(PRIMARY_COLOR)
        self.setFont("Helvetica-Bold", 10)
        self.drawString(inch/2, letter[1] - inch/2, "🧠 Cortex-Flow Documentation")
        # Header line
        self.setStrokeColor(PRIMARY_COLOR)
        self.setLineWidth(1)
        self.line(inch/2, letter[1] - inch/2 - 5, letter[0] - inch/2, letter[1] - inch/2 - 5)
        self.restoreState()

def create_styles():
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    # Subtitle
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=TEXT_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica'
    ))

    # Section headers
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=PRIMARY_COLOR,
        spaceAfter=15,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    ))

    # Subsection headers
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=SECONDARY_COLOR,
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    ))

    # Feature title
    styles.add(ParagraphStyle(
        name='FeatureTitle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=TEXT_PRIMARY,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))

    # Body text
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=TEXT_PRIMARY,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=14
    ))

    # Code style
    styles.add(ParagraphStyle(
        name='CustomCode',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        textColor=TEXT_PRIMARY,
        leftIndent=20,
        rightIndent=20,
        backColor=HexColor('#f5f5f5'),
        borderColor=HexColor('#e0e0e0'),
        borderWidth=1,
        borderPadding=5,
        spaceAfter=10
    ))

    # Bullet style
    styles.add(ParagraphStyle(
        name='BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_PRIMARY,
        leftIndent=20,
        spaceAfter=5
    ))

    return styles

def create_cover_page(styles):
    """Create the cover page"""
    elements = []

    elements.append(Spacer(1, 2*inch))

    # Title
    elements.append(Paragraph("🧠 Cortex-Flow", styles['CustomTitle']))

    # Subtitle
    elements.append(Paragraph(
        "A Distributed Multi-Agent AI System",
        styles['CustomSubtitle']
    ))
    elements.append(Paragraph(
        "Powered by LangChain, LangGraph, and FastAPI",
        styles['CustomBody']
    ))

    elements.append(Spacer(1, 1*inch))

    # Version info
    version_data = [
        ['Version:', 'v1.1 Stable'],
        ['Date:', datetime.now().strftime('%B %Y')],
        ['Status:', 'Production Ready'],
        ['License:', 'MIT']
    ]

    version_table = Table(version_data, colWidths=[2*inch, 3*inch])
    version_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_SECONDARY),
        ('TEXTCOLOR', (1, 0), (1, -1), PRIMARY_COLOR),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(version_table)
    elements.append(PageBreak())

    return elements

def create_toc(styles):
    """Create table of contents"""
    elements = []

    elements.append(Paragraph("Table of Contents", styles['SectionHeader']))
    elements.append(Spacer(1, 0.5*inch))

    toc_data = [
        ("1. Introduction", "3"),
        ("2. Features Overview", "4"),
        ("   2.1 Multi-Agent System", "4"),
        ("   2.2 Workflow Templates", "5"),
        ("   2.3 MCP Integration", "6"),
        ("   2.4 Python Libraries", "7"),
        ("   2.5 Web Interface", "8"),
        ("   2.6 OpenAI Compatible API", "9"),
        ("3. System Architecture", "10"),
        ("4. Getting Started", "12"),
        ("   4.1 Installation", "12"),
        ("   4.2 Quick Examples", "13"),
        ("5. Agent System", "15"),
        ("6. Workflow System", "17"),
        ("7. Library System", "19"),
        ("8. API Reference", "21"),
        ("9. Security & Best Practices", "23"),
        ("10. Release Notes", "25"),
    ]

    toc_table_data = []
    for entry, page in toc_data:
        if entry.startswith("   "):
            # Subsection
            toc_table_data.append([
                Paragraph(entry, styles['BulletStyle']),
                Paragraph(page, styles['Normal'])
            ])
        else:
            # Main section
            toc_table_data.append([
                Paragraph(f"<b>{entry}</b>", styles['Normal']),
                Paragraph(f"<b>{page}</b>", styles['Normal'])
            ])

    toc_table = Table(toc_table_data, colWidths=[6*inch, 1*inch])
    toc_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    elements.append(toc_table)
    elements.append(PageBreak())

    return elements

def create_introduction(styles):
    """Create introduction section"""
    elements = []

    elements.append(Paragraph("1. Introduction", styles['SectionHeader']))

    elements.append(Paragraph(
        """Cortex-Flow is a cutting-edge distributed multi-agent AI system that revolutionizes how we build
        and deploy intelligent workflows. By combining the power of LangChain, LangGraph, and FastAPI,
        it provides a robust platform for creating sophisticated AI applications.""",
        styles['CustomBody']
    ))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("Key Highlights", styles['SubsectionHeader']))

    highlights = [
        "Production-ready distributed architecture",
        "Template-based workflow system with visual execution",
        "Specialized AI agents using the ReAct pattern",
        "Model Context Protocol (MCP) for tool integration",
        "Custom Python library system for extensibility",
        "OpenAI-compatible API for seamless integration",
        "Powerful web interface for workflow management"
    ]

    for highlight in highlights:
        elements.append(Paragraph(f"• {highlight}", styles['BulletStyle']))

    elements.append(PageBreak())

    return elements

def create_features_section(styles):
    """Create features section"""
    elements = []

    elements.append(Paragraph("2. Features Overview", styles['SectionHeader']))

    # Multi-Agent System
    elements.append(Paragraph("2.1 Multi-Agent System", styles['SubsectionHeader']))
    elements.append(Paragraph(
        """The multi-agent system is the core of Cortex-Flow, featuring specialized AI agents that work
        together using the ReAct (Reasoning-Action-Observation) pattern. Each agent has a specific role
        and expertise, enabling complex task decomposition and parallel execution.""",
        styles['CustomBody']
    ))

    agent_data = [
        ["Agent", "Role", "Capabilities"],
        ["Supervisor", "Orchestrator", "Task decomposition, delegation, coordination"],
        ["Researcher", "Information Gathering", "Web research, data collection, fact-checking"],
        ["Analyst", "Data Analysis", "Pattern recognition, data processing, insights"],
        ["Writer", "Content Generation", "Reports, summaries, documentation"],
        ["Custom", "User-Defined", "Any specialized task or domain"]
    ]

    agent_table = Table(agent_data, colWidths=[1.5*inch, 2*inch, 3.5*inch])
    agent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    elements.append(agent_table)
    elements.append(Spacer(1, 0.3*inch))

    # Workflow Templates
    elements.append(Paragraph("2.2 Workflow Templates", styles['SubsectionHeader']))
    elements.append(Paragraph(
        """The workflow template system enables you to define complex AI pipelines using JSON-based
        configurations. Workflows support conditional routing, parallel execution, and composable
        sub-workflows, all compiled to native LangGraph for optimal performance.""",
        styles['CustomBody']
    ))

    workflow_features = [
        "JSON-based workflow definitions",
        "Conditional routing with dynamic branching",
        "Parallel node execution for performance",
        "Composable sub-workflows for modularity",
        "Native LangGraph compilation",
        "Visual workflow builder interface"
    ]

    for feature in workflow_features:
        elements.append(Paragraph(f"• {feature}", styles['BulletStyle']))

    elements.append(Spacer(1, 0.3*inch))

    # MCP Integration
    elements.append(Paragraph("2.3 MCP Integration", styles['SubsectionHeader']))
    elements.append(Paragraph(
        """The Model Context Protocol (MCP) integration allows Cortex-Flow to connect with external tools
        and services. Any MCP-compliant server can be integrated, providing access to filesystems,
        databases, APIs, and custom tools.""",
        styles['CustomBody']
    ))

    elements.append(Spacer(1, 0.3*inch))

    # Python Libraries
    elements.append(Paragraph("2.4 Python Libraries System", styles['SubsectionHeader']))
    elements.append(Paragraph(
        """The new Python library system (v1.1) enables you to integrate any Python functionality into
        your workflows. Using a simple decorator-based approach, you can expose Python functions as
        workflow nodes with automatic type validation and security controls.""",
        styles['CustomBody']
    ))

    elements.append(Paragraph("Built-in Libraries:", styles['FeatureTitle']))

    library_data = [
        ["Library", "Functions", "Use Cases"],
        ["REST API", "GET, POST, PUT, DELETE", "API integrations, webhooks, data fetching"],
        ["Filesystem", "Read, Write, JSON operations", "Data persistence, file processing, logs"],
        ["Email", "Send notifications", "Alerts, reports, user communication"],
        ["Database", "Query, Insert, Update", "Data storage, analytics, CRUD operations"]
    ]

    lib_table = Table(library_data, colWidths=[1.5*inch, 2*inch, 3.5*inch])
    lib_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    elements.append(lib_table)

    elements.append(PageBreak())

    return elements

def create_architecture_section(styles):
    """Create architecture section"""
    elements = []

    elements.append(Paragraph("3. System Architecture", styles['SectionHeader']))

    elements.append(Paragraph(
        """Cortex-Flow follows a microservices architecture where each component operates independently
        but works together seamlessly. This distributed design ensures scalability, resilience, and
        flexibility.""",
        styles['CustomBody']
    ))

    elements.append(Spacer(1, 0.3*inch))

    # Architecture layers
    elements.append(Paragraph("Architecture Layers", styles['SubsectionHeader']))

    layers = [
        ("Application Layer", "Web UI (React), CLI Tools, REST API, WebSocket connections"),
        ("Agent Layer", "Supervisor, Researcher, Analyst, Writer, Custom Agents"),
        ("Core Engine", "LangGraph compiler, Workflow engine, MCP client, Library executor"),
        ("Infrastructure", "FastAPI servers, Redis/PostgreSQL, Docker, Kubernetes")
    ]

    for layer_name, components in layers:
        elements.append(Paragraph(f"<b>{layer_name}:</b>", styles['FeatureTitle']))
        elements.append(Paragraph(components, styles['BulletStyle']))
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("Key Design Principles", styles['SubsectionHeader']))

    principles = [
        "Microservices architecture for independent scaling",
        "Event-driven communication between agents",
        "Stateless design with external state persistence",
        "Container-native deployment with Docker/Kubernetes",
        "Async I/O for optimal performance",
        "Capability-based security model"
    ]

    for principle in principles:
        elements.append(Paragraph(f"• {principle}", styles['BulletStyle']))

    elements.append(PageBreak())

    return elements

def create_code_examples(styles):
    """Create code examples section"""
    elements = []

    elements.append(Paragraph("4. Getting Started", styles['SectionHeader']))

    elements.append(Paragraph("4.1 Installation", styles['SubsectionHeader']))

    install_code = """# Clone the repository
git clone https://github.com/cortex-flow/cortex-flow.git
cd cortex-flow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the system
python scripts/start_all.py"""

    elements.append(Paragraph(install_code, styles['CustomCode']))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("4.2 Quick Examples", styles['SubsectionHeader']))

    # Workflow example
    elements.append(Paragraph("Workflow Template Example:", styles['FeatureTitle']))

    workflow_code = """{
  "name": "research_and_report",
  "nodes": [
    {
      "id": "research",
      "agent": "researcher",
      "instruction": "Research {topic} trends in 2024"
    },
    {
      "id": "analyze",
      "agent": "analyst",
      "instruction": "Analyze the research findings",
      "depends_on": ["research"]
    },
    {
      "id": "save_data",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_json",
      "function_params": {
        "path": "./output/analysis.json",
        "data": "{analyze_output}"
      },
      "depends_on": ["analyze"]
    }
  ]
}"""

    elements.append(Paragraph(workflow_code, styles['CustomCode']))

    elements.append(Spacer(1, 0.3*inch))

    # Library example
    elements.append(Paragraph("Custom Library Example:", styles['FeatureTitle']))

    library_code = """from libraries.base import library_tool, LibraryResponse

@library_tool(
    name="send_email",
    description="Send email notification",
    parameters={
        "to": {"type": "string", "required": True},
        "subject": {"type": "string", "required": True},
        "body": {"type": "string", "required": True}
    },
    timeout=30
)
async def send_email(to: str, subject: str, body: str):
    # Your implementation here
    await smtp_client.send(to, subject, body)

    return LibraryResponse(
        success=True,
        data="Email sent successfully",
        metadata={"recipient": to}
    )"""

    elements.append(Paragraph(library_code, styles['CustomCode']))

    elements.append(PageBreak())

    return elements

def create_security_section(styles):
    """Create security section"""
    elements = []

    elements.append(Paragraph("9. Security & Best Practices", styles['SectionHeader']))

    elements.append(Paragraph(
        """Security is a core design principle in Cortex-Flow. The system implements multiple layers of
        security controls to ensure safe execution of AI workflows and protection of sensitive data.""",
        styles['CustomBody']
    ))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("Security Features", styles['SubsectionHeader']))

    security_features = [
        ("Capability-Based Access Control", "Libraries must declare required capabilities (filesystem, network, etc.)"),
        ("Path Validation", "Filesystem operations restricted to allowed directories"),
        ("Resource Limits", "CPU, memory, and execution time limits for library functions"),
        ("Sandboxing", "Optional process isolation for critical operations"),
        ("Input Validation", "Automatic type checking and sanitization"),
        ("Secrets Management", "Environment-based configuration with encrypted storage")
    ]

    for feature, description in security_features:
        elements.append(Paragraph(f"<b>{feature}:</b>", styles['FeatureTitle']))
        elements.append(Paragraph(description, styles['BulletStyle']))
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("Best Practices", styles['SubsectionHeader']))

    practices = [
        "Always use environment variables for API keys and secrets",
        "Implement input validation in custom libraries",
        "Set appropriate timeouts for long-running operations",
        "Use rate limiting for resource-intensive functions",
        "Enable audit logging for security-critical operations",
        "Regularly update dependencies and security patches",
        "Follow the principle of least privilege for capabilities",
        "Test workflows in isolated environments before production"
    ]

    for practice in practices:
        elements.append(Paragraph(f"• {practice}", styles['BulletStyle']))

    elements.append(PageBreak())

    return elements

def create_release_notes(styles):
    """Create release notes section"""
    elements = []

    elements.append(Paragraph("10. Release Notes", styles['SectionHeader']))

    releases = [
        {
            "version": "v1.1 - October 2025",
            "title": "Python Library Integration System",
            "features": [
                "Custom Python libraries with decorator-based registration",
                "Type validation with Pydantic",
                "Security capabilities system",
                "Built-in REST API and Filesystem libraries",
                "Variable substitution from workflow state"
            ]
        },
        {
            "version": "v1.0 - October 2025",
            "title": "Multi-Project Configuration",
            "features": [
                "JSON-based configuration system",
                "Multi-environment support",
                "Project isolation",
                "Secrets separation",
                "Backward compatibility"
            ]
        },
        {
            "version": "v0.4 - September 2025",
            "title": "LangGraph Integration",
            "features": [
                "Native LangGraph compilation",
                "Streaming support",
                "Checkpointing system",
                "Human-in-the-loop workflows",
                "Performance optimizations"
            ]
        }
    ]

    for release in releases:
        elements.append(Paragraph(f"<b>{release['version']}</b>", styles['SubsectionHeader']))
        elements.append(Paragraph(release['title'], styles['FeatureTitle']))
        for feature in release['features']:
            elements.append(Paragraph(f"• {feature}", styles['BulletStyle']))
        elements.append(Spacer(1, 0.2*inch))

    return elements

def generate_pdf(filename="cortex_flow_documentation.pdf"):
    """Generate the complete PDF document"""

    # Create document
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Get styles
    styles = create_styles()

    # Build content
    elements = []

    # Cover page
    elements.extend(create_cover_page(styles))

    # Table of contents
    elements.extend(create_toc(styles))

    # Main content
    elements.extend(create_introduction(styles))
    elements.extend(create_features_section(styles))
    elements.extend(create_architecture_section(styles))
    elements.extend(create_code_examples(styles))
    elements.extend(create_security_section(styles))
    elements.extend(create_release_notes(styles))

    # Build PDF
    doc.build(elements, canvasmaker=NumberedCanvas)

    print(f"✅ PDF documentation generated successfully: {filename}")
    print(f"📄 File size: {os.path.getsize(filename) / 1024:.2f} KB")

if __name__ == "__main__":
    # Check for required library
    try:
        import reportlab
        generate_pdf()
    except ImportError:
        print("❌ ReportLab library not installed.")
        print("📦 Install it with: pip install reportlab")
        print("\nAlternatively, you can use the HTML file directly or convert it to PDF using:")
        print("  - Browser's print to PDF feature")
        print("  - wkhtmltopdf tool")
        print("  - Online HTML to PDF converters")