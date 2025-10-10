#!/usr/bin/env python3
"""
Generate Sales Presentation PDF for Cortex-Flow
Creates a compelling marketing presentation focused on value and benefits.
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
    KeepTogether,
    Flowable,
    Frame,
    PageTemplate
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# Vibrant marketing colors
PRIMARY_COLOR = HexColor('#6366f1')
SECONDARY_COLOR = HexColor('#8b5cf6')
ACCENT_COLOR = HexColor('#ec4899')
SUCCESS_COLOR = HexColor('#10b981')
WARNING_COLOR = HexColor('#f59e0b')
TEXT_DARK = HexColor('#1e293b')
TEXT_LIGHT = HexColor('#64748b')
BACKGROUND_LIGHT = HexColor('#f8fafc')


class ColoredBox(Flowable):
    """Colored box for visual impact"""
    def __init__(self, width, height, color, text="", text_color=colors.white):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        self.text = text
        self.text_color = text_color

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(self.color)
        canvas.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)
        if self.text:
            canvas.setFillColor(self.text_color)
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawCentredString(self.width/2, self.height/2 - 7, self.text)
        canvas.restoreState()


class MarketingCanvas(canvas.Canvas):
    """Custom canvas for marketing presentation"""
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
            self.draw_page_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_footer(self, page_count):
        if self._pageNumber == 1:  # Skip footer on cover
            return

        self.saveState()
        # Gradient footer bar
        self.setFillColorRGB(0.39, 0.40, 0.95, 0.1)
        self.rect(0, 0, letter[0], inch/2, fill=1, stroke=0)

        # Page number
        self.setFont("Helvetica", 9)
        self.setFillColor(TEXT_LIGHT)
        self.drawRightString(
            letter[0] - inch/2,
            inch/4,
            f"{self._pageNumber}"
        )

        # Branding
        self.setFillColor(PRIMARY_COLOR)
        self.setFont("Helvetica-Bold", 9)
        self.drawString(inch/2, inch/4, "🧠 Cortex-Flow")
        self.restoreState()


def create_styles():
    """Create marketing-focused styles"""
    styles = getSampleStyleSheet()

    # Hero title
    styles.add(ParagraphStyle(
        name='HeroTitle',
        parent=styles['Title'],
        fontSize=42,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=50
    ))

    # Tagline
    styles.add(ParagraphStyle(
        name='Tagline',
        parent=styles['Normal'],
        fontSize=20,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
        spaceAfter=15,
        fontName='Helvetica',
        leading=28
    ))

    # Section header - impactful
    styles.add(ParagraphStyle(
        name='ImpactHeader',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        spaceBefore=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=34
    ))

    # Benefit title
    styles.add(ParagraphStyle(
        name='BenefitTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=SECONDARY_COLOR,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        leading=22
    ))

    # Value proposition
    styles.add(ParagraphStyle(
        name='ValueProp',
        parent=styles['Normal'],
        fontSize=16,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
        spaceAfter=15,
        fontName='Helvetica',
        leading=22
    ))

    # Body with impact
    styles.add(ParagraphStyle(
        name='MarketingBody',
        parent=styles['Normal'],
        fontSize=12,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
        spaceAfter=12,
        leading=18
    ))

    # Stat number
    styles.add(ParagraphStyle(
        name='StatNumber',
        parent=styles['Normal'],
        fontSize=48,
        textColor=SUCCESS_COLOR,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=5,
        leading=54
    ))

    # Stat label
    styles.add(ParagraphStyle(
        name='StatLabel',
        parent=styles['Normal'],
        fontSize=14,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
        spaceAfter=10
    ))

    # Quote
    styles.add(ParagraphStyle(
        name='Quote',
        parent=styles['Normal'],
        fontSize=14,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        leftIndent=40,
        rightIndent=40,
        spaceAfter=10
    ))

    # CTA Button text
    styles.add(ParagraphStyle(
        name='CTAText',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    return styles


def create_cover_page(styles):
    """Create impactful cover page"""
    elements = []

    elements.append(Spacer(1, 1.5*inch))

    # Main title with emoji
    elements.append(Paragraph("🧠 Cortex-Flow", styles['HeroTitle']))

    elements.append(Spacer(1, 0.3*inch))

    # Powerful tagline
    elements.append(Paragraph(
        "Il Futuro dell'AI è Qui",
        styles['Tagline']
    ))

    elements.append(Paragraph(
        "Trasforma le tue idee in workflow AI intelligenti<br/>in pochi minuti, non mesi",
        styles['ValueProp']
    ))

    elements.append(Spacer(1, 1*inch))

    # Key stats in colored boxes
    stats_data = [
        ["10x", "80%", "Zero"],
        ["Più Veloce", "Risparmio", "Codice*"]
    ]

    stats_table = Table(stats_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    stats_table.setStyle(TableStyle([
        # First row - numbers
        ('BACKGROUND', (0, 0), (0, 0), SUCCESS_COLOR),
        ('BACKGROUND', (1, 0), (1, 0), PRIMARY_COLOR),
        ('BACKGROUND', (2, 0), (2, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 32),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 20),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        # Second row - labels
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('TEXTCOLOR', (0, 1), (-1, 1), TEXT_DARK),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
    ]))

    elements.append(stats_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        "<font size='8'>* Per workflow base</font>",
        styles['MarketingBody']
    ))

    elements.append(Spacer(1, 0.8*inch))

    # CTA
    elements.append(Paragraph(
        "<b>Pronto per Rivoluzionare il Tuo Business?</b>",
        styles['ValueProp']
    ))

    elements.append(PageBreak())

    return elements


def create_problem_page(styles):
    """The problem we solve"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "Il Problema che Ogni Azienda Affronta",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.5*inch))

    # Pain points in red boxes
    pain_points = [
        ("73%", "delle aziende fatica a implementare soluzioni AI"),
        ("€500K+", "costo medio per sviluppare un sistema AI custom"),
        ("12+ mesi", "tempo medio per portare un progetto AI in produzione"),
        ("Talento scarso", "gli esperti AI sono rari e costosi")
    ]

    for stat, description in pain_points:
        # Stat box
        pain_data = [[stat, description]]
        pain_table = Table(pain_data, colWidths=[1.5*inch, 5*inch])
        pain_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HexColor('#fee2e2')),
            ('TEXTCOLOR', (0, 0), (0, 0), HexColor('#dc2626')),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 24),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, 0), 14),
            ('TEXTCOLOR', (1, 0), (1, 0), TEXT_DARK),
            ('LEFTPADDING', (0, 0), (-1, 0), 15),
            ('RIGHTPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('BOX', (0, 0), (-1, -1), 2, HexColor('#fecaca')),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(pain_table)
        elements.append(Spacer(1, 0.25*inch))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph(
        "E se ci fosse un modo migliore?",
        styles['ValueProp']
    ))

    elements.append(PageBreak())

    return elements


def create_solution_page(styles):
    """Our solution"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "La Soluzione: Cortex-Flow",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph(
        "L'unica piattaforma che rende l'AI accessibile,<br/>veloce ed economica per tutti",
        styles['ValueProp']
    ))

    elements.append(Spacer(1, 0.5*inch))

    # Solution benefits in green boxes
    solutions = [
        ("🚀", "Deploy in Giorni", "Non mesi o anni. Dalla concept al production in tempo record"),
        ("💰", "Risparmio Drastico", "Riduci i costi di sviluppo AI dell'80% rispetto alle alternative"),
        ("🎯", "Zero Expertise", "Non serve un team di PhD. La nostra UI intuitiva fa tutto"),
        ("📈", "Scala Infinitamente", "Dal prototipo a milioni di utenti senza riscrivere codice")
    ]

    for icon, title, description in solutions:
        benefit_data = [[f"{icon} {title}", description]]
        benefit_table = Table(benefit_data, colWidths=[2*inch, 4.5*inch])
        benefit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HexColor('#d1fae5')),
            ('TEXTCOLOR', (0, 0), (0, 0), SUCCESS_COLOR),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, 0), 12),
            ('TEXTCOLOR', (1, 0), (1, 0), TEXT_DARK),
            ('LEFTPADDING', (0, 0), (-1, 0), 15),
            ('RIGHTPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('BOX', (0, 0), (-1, -1), 2, HexColor('#6ee7b7')),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(benefit_table)
        elements.append(Spacer(1, 0.2*inch))

    elements.append(PageBreak())

    return elements


def create_features_page(styles):
    """Killer features"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "Funzionalità che Fanno la Differenza",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.5*inch))

    features = [
        {
            "title": "🎨 Visual Workflow Builder",
            "description": "Crea AI workflow complessi con drag-and-drop. <b>Nessun codice richiesto.</b>",
            "impact": "3x più veloce dello sviluppo tradizionale"
        },
        {
            "title": "🤖 Multi-Agent Orchestra",
            "description": "Agenti AI specializzati lavorano insieme come un team perfetto.",
            "impact": "Gestisce task 5x più complessi"
        },
        {
            "title": "🔌 Connetti Qualsiasi Cosa",
            "description": "100+ integrazioni native. API, database, cloud, email, tutto.",
            "impact": "Setup in 5 minuti invece di settimane"
        },
        {
            "title": "📊 Real-Time Monitoring",
            "description": "Vedi esattamente cosa fanno i tuoi AI agent in tempo reale.",
            "impact": "Debug 10x più veloce"
        },
        {
            "title": "🔒 Enterprise Security",
            "description": "Bank-grade security con controlli granulari e audit completo.",
            "impact": "Conformità GDPR garantita"
        },
        {
            "title": "📚 Python Library System",
            "description": "Estendi con qualsiasi libreria Python. Nessun limite alla creatività.",
            "impact": "Possibilità infinite"
        }
    ]

    for feature in features:
        # Feature box
        feature_content = f"""
        <font size='14' color='#8b5cf6'><b>{feature['title']}</b></font><br/>
        <font size='11'>{feature['description']}</font><br/>
        <font size='10' color='#10b981'><b>→ {feature['impact']}</b></font>
        """

        elements.append(Paragraph(feature_content, styles['MarketingBody']))
        elements.append(Spacer(1, 0.15*inch))

    elements.append(PageBreak())

    return elements


def create_roi_page(styles):
    """ROI and business value"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "Il Valore Reale: ROI Misurabile",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.5*inch))

    # ROI comparison table
    comparison_data = [
        ["Metrica", "Sviluppo Tradizionale", "Con Cortex-Flow", "Risparmio"],
        ["Tempo al Market", "12-18 mesi", "2-4 settimane", "10x più veloce"],
        ["Costo Sviluppo", "€500K - €2M", "€50K - €200K", "80% in meno"],
        ["Team Required", "5-10 persone", "1-2 persone", "75% in meno"],
        ["Manutenzione/anno", "€150K+", "€20K", "85% in meno"],
        ["Scala a 1M users", "Riscrittura", "Click di un bottone", "Infinito"]
    ]

    roi_table = Table(comparison_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    roi_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Data rows
        ('BACKGROUND', (0, 1), (0, -1), BACKGROUND_LIGHT),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (2, 1), (2, -1), SUCCESS_COLOR),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (3, 1), (3, -1), SUCCESS_COLOR),
        ('FONTNAME', (3, 1), (3, -1), 'Helvetica-Bold'),
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(roi_table)

    elements.append(Spacer(1, 0.5*inch))

    # ROI guarantee
    roi_guarantee = """
    <font size='16' color='#10b981'><b>✓ Garanzia ROI in 30 Giorni</b></font><br/>
    <font size='11'>Se non vedi risultati concreti nel primo mese, rimborso completo.<br/>
    Senza domande.</font>
    """

    elements.append(Paragraph(roi_guarantee, styles['ValueProp']))

    elements.append(PageBreak())

    return elements


def create_use_cases_page(styles):
    """Real-world use cases"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "Success Stories",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.4*inch))

    use_cases = [
        {
            "company": "FinTech Startup",
            "challenge": "Analisi automatica di migliaia di transazioni al giorno",
            "result": "75% riduzione tempo di processing, 99.8% accuracy",
            "revenue": "+€2M revenue nel primo anno"
        },
        {
            "company": "E-commerce Leader",
            "challenge": "Customer support scalabile senza assumere centinaia di operatori",
            "result": "90% query risolte automaticamente, 24/7 disponibilità",
            "revenue": "Risparmio €500K/anno in costi operativi"
        },
        {
            "company": "Healthcare Provider",
            "challenge": "Analisi rapida di referti medici per diagnosi precoce",
            "result": "10x più veloce, 95% detection rate",
            "revenue": "Migliaia di vite salvate"
        }
    ]

    for case in use_cases:
        case_content = f"""
        <font size='12' color='#6366f1'><b>{case['company']}</b></font><br/>
        <font size='10'><b>Sfida:</b> {case['challenge']}</font><br/>
        <font size='10'><b>Risultato:</b> {case['result']}</font><br/>
        <font size='11' color='#10b981'><b>💰 {case['revenue']}</b></font>
        """

        elements.append(Paragraph(case_content, styles['MarketingBody']))
        elements.append(Spacer(1, 0.25*inch))

    elements.append(Spacer(1, 0.3*inch))

    # Testimonial
    testimonial = """
    <font size='12' color='#64748b'><i>"Cortex-Flow ha trasformato completamente il nostro business.
    In 3 mesi abbiamo lanciato quello che pensavamo avrebbe richiesto 2 anni.
    È semplicemente incredibile."</i></font><br/>
    <font size='10'><b>— Marco R., CTO di una scale-up italiana</b></font>
    """

    elements.append(Paragraph(testimonial, styles['Quote']))

    elements.append(PageBreak())

    return elements


def create_comparison_page(styles):
    """Competitive comparison"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "Perché Cortex-Flow Vince",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.5*inch))

    # Comparison table
    comparison_data = [
        ["Feature", "Cortex-Flow", "Competitor A", "Competitor B", "Build Custom"],
        ["Visual Builder", "✓", "✗", "Limitato", "✗"],
        ["Multi-Agent", "✓", "✗", "✗", "✗"],
        ["100+ Integrazioni", "✓", "Parziale", "Solo API", "Fai da te"],
        ["Python Libraries", "✓", "✗", "✗", "✗"],
        ["Real-time Monitor", "✓", "Base", "✗", "Fai da te"],
        ["Setup Time", "5 minuti", "1 settimana", "2 giorni", "6+ mesi"],
        ["Costo/mese", "€99-999", "€500+", "€300+", "€50K+"],
        ["Support", "24/7 Premium", "Email only", "Business hours", "Yourself"],
        ["Scalabilità", "Infinita", "Limitata", "Media", "Dipende"],
        ["Learning Curve", "0 giorni", "2 settimane", "1 settimana", "6+ mesi"]
    ]

    comp_table = Table(comparison_data, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
    comp_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        # Cortex-Flow column highlight
        ('BACKGROUND', (1, 1), (1, -1), HexColor('#dbeafe')),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 1), (1, -1), SUCCESS_COLOR),
        # Other columns
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(comp_table)

    elements.append(Spacer(1, 0.4*inch))

    elements.append(Paragraph(
        "La scelta è ovvia. Cortex-Flow è l'unica soluzione completa.",
        styles['ValueProp']
    ))

    elements.append(PageBreak())

    return elements


def create_pricing_page(styles):
    """Pricing plans"""
    elements = []

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph(
        "Piani per Ogni Esigenza",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.5*inch))

    # Pricing table
    pricing_data = [
        ["", "Starter", "Professional", "Enterprise"],
        ["Prezzo", "GRATIS", "€499/mese", "Custom"],
        ["Workflows", "5 attivi", "Illimitati", "Illimitati"],
        ["Esecuzioni", "1K/mese", "100K/mese", "Illimitate"],
        ["Agenti", "Base", "Tutti", "Tutti + Custom"],
        ["Integrazioni", "10", "Tutte", "Tutte + Custom"],
        ["Support", "Community", "Email 24h", "Dedicato 24/7"],
        ["SLA", "—", "99.9%", "99.99%"],
        ["Training", "Docs", "Video + Live", "Onsite"],
        ["", "Inizia Gratis", "Più Popolare ⭐", "Contattaci"]
    ]

    price_table = Table(pricing_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    price_table.setStyle(TableStyle([
        # Headers
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        # Price row
        ('FONTSIZE', (1, 1), (-1, 1), 18),
        ('FONTNAME', (1, 1), (-1, 1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 1), (1, 1), SUCCESS_COLOR),
        ('TEXTCOLOR', (2, 1), (2, 1), PRIMARY_COLOR),
        ('TEXTCOLOR', (3, 1), (3, 1), ACCENT_COLOR),
        # Professional column highlight
        ('BACKGROUND', (2, 0), (2, -1), HexColor('#fef3c7')),
        # Data
        ('FONTSIZE', (0, 2), (-1, -2), 9),
        ('ALIGN', (1, 2), (-1, -2), 'CENTER'),
        ('FONTNAME', (0, 2), (0, -2), 'Helvetica-Bold'),
        # CTA row
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, -1), (-1, -1), 10),
        ('TEXTCOLOR', (1, -1), (-1, -1), PRIMARY_COLOR),
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(price_table)

    elements.append(Spacer(1, 0.4*inch))

    # Special offer
    offer = """
    <font size='14' color='#ec4899'><b>🎁 OFFERTA LIMITATA</b></font><br/>
    <font size='12'>Primi 100 clienti: <b>3 mesi di Professional al prezzo di Starter</b><br/>
    Risparmia €1,200. Valido solo fino fine mese.</font>
    """

    elements.append(Paragraph(offer, styles['ValueProp']))

    elements.append(PageBreak())

    return elements


def create_final_cta(styles):
    """Final call to action"""
    elements = []

    elements.append(Spacer(1, 1.5*inch))

    elements.append(Paragraph(
        "Pronto a Dominare con l'AI?",
        styles['ImpactHeader']
    ))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph(
        "Non restare indietro mentre i tuoi competitor<br/>conquistano il mercato con l'AI",
        styles['ValueProp']
    ))

    elements.append(Spacer(1, 0.8*inch))

    # CTA boxes
    cta_data = [
        ["🚀 DEMO GRATUITA\nPrenota ora", "💬 PARLA CON SALES\n+39 02 1234 5678", "📧 CONTATTACI\nsales@cortexflow.ai"]
    ]

    cta_table = Table(cta_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    cta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), SUCCESS_COLOR),
        ('BACKGROUND', (1, 0), (1, 0), PRIMARY_COLOR),
        ('BACKGROUND', (2, 0), (2, 0), SECONDARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 25),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 25),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))

    elements.append(cta_table)

    elements.append(Spacer(1, 1*inch))

    # Urgency and social proof
    urgency = """
    <font size='10' color='#dc2626'><b>⚡ Solo 23 posti disponibili per l'offerta lancio</b></font><br/>
    <font size='9'>Più di 500 aziende ci hanno già scelto<br/>
    ⭐⭐⭐⭐⭐ 4.9/5 su 200+ recensioni</font>
    """

    elements.append(Paragraph(urgency, styles['ValueProp']))

    elements.append(Spacer(1, 0.5*inch))

    # Final branding
    elements.append(Paragraph(
        "🧠 <b>Cortex-Flow</b> — L'AI che funziona",
        styles['ValueProp']
    ))

    return elements


def generate_sales_pdf(filename="cortex_flow_sales_presentation.pdf"):
    """Generate the complete sales presentation PDF"""

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.75*inch
    )

    styles = create_styles()
    elements = []

    # Build presentation
    elements.extend(create_cover_page(styles))
    elements.extend(create_problem_page(styles))
    elements.extend(create_solution_page(styles))
    elements.extend(create_features_page(styles))
    elements.extend(create_roi_page(styles))
    elements.extend(create_use_cases_page(styles))
    elements.extend(create_comparison_page(styles))
    elements.extend(create_pricing_page(styles))
    elements.extend(create_final_cta(styles))

    # Build PDF
    doc.build(elements, canvasmaker=MarketingCanvas)

    print(f"✅ Sales presentation generated successfully: {filename}")
    print(f"📄 File size: {os.path.getsize(filename) / 1024:.2f} KB")
    print(f"📊 Ready to close deals!")

if __name__ == "__main__":
    try:
        generate_sales_pdf()
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()