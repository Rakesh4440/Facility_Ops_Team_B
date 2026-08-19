import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.units import inch

def build_pdf_documentation(output_filename="FacilityOps_Project_Documentation_Final.pdf"):
    pdf_path = Path(output_filename).resolve()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    primary_color = colors.HexColor("#0b1530")      # Dark Navy
    accent_color = colors.HexColor("#1672d4")       # Royal Blue
    cyan_color = colors.HexColor("#00a896")         # Cyan Green
    text_color = colors.HexColor("#222222")         # Dark Grey
    bg_light = colors.HexColor("#f4f7fc")           # Light Gray/Blue

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1b2a4a"),
        backColor=colors.HexColor("#eaeef7"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=8
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("FacilityOps AI Platform", title_style))
    story.append(Paragraph("Predictive Maintenance & Role-Based Facility Management System", subtitle_style))
    story.append(Paragraph("<b>Author / Developer:</b> Academic Engineering Team &nbsp;|&nbsp; <b>Framework:</b> Streamlit, Plotly, Pandas, Ollama AI", body_style))
    story.append(Paragraph("<b>Version:</b> 2.0 (Final Production Edition with RBAC Authentication)", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=8, spaceAfter=15))

    # Section 1: Executive Overview
    story.append(Paragraph("1. Executive Overview", h1_style))
    story.append(Paragraph(
        "<b>FacilityOps AI Platform</b> is an enterprise-grade predictive maintenance and facility operations web application designed to monitor industrial machinery health, predict component failures, automate preventive maintenance scheduling, manage work orders, and utilize local LLM artificial intelligence (via Ollama) to recommend targeted maintenance interventions.",
        body_style
    ))
    story.append(Paragraph(
        "The primary goal of this project is to eliminate costly operational downtime by transforming raw sensory equipment signals (temperature, rotational speed, torque, tool wear) into actionable diagnostic insights for maintenance personnel.",
        body_style
    ))

    # Section 2: Role-Based Authentication & Security Model
    story.append(Paragraph("2. Role-Based Authentication & Access Control (RBAC)", h1_style))
    story.append(Paragraph(
        "The application incorporates a secure multi-user authentication gateway supporting <b>Role-Based Access Control (RBAC)</b> with cryptographic SHA-256 password hashing. Users are categorized into two primary system roles:",
        body_style
    ))

    rbac_data = [
        [Paragraph("<b>User Role</b>", body_style), Paragraph("<b>Target Persona</b>", body_style), Paragraph("<b>Authorized System Modules & Access Scope</b>", body_style)],
        [
            Paragraph("<b>👑 System Administrator (Admin)</b>", body_style),
            Paragraph("Facility Directors, Operations Managers, Data Analysts", body_style),
            Paragraph("<b>Unrestricted Access to All 7 Modules + Home Page:</b><br/>• Full Dataset & EDA Analytics<br/>• Facility BI Performance Dashboard<br/>• Machine Explorer & AI Diagnostics<br/>• Work Order Management<br/>• Preventive Maintenance Schedules<br/>• AI Operations Recommendation Engine", body_style)
        ],
        [
            Paragraph("<b>🔧 Field Technician (Technician)</b>", body_style),
            Paragraph("Maintenance Engineers, Shift Technicians, Field Operators", body_style),
            Paragraph("<b>Focused Operational Workflow (4 Key Modules):</b><br/>• 📊 Maintenance Status Dashboard<br/>• 🔍 Machine Explorer & Equipment Inspection<br/>• 📋 Work Order Management & Resolution<br/>• 📅 Preventive Maintenance Schedules & Checklists", body_style)
        ]
    ]

    t_rbac = Table(rbac_data, colWidths=[1.8*inch, 1.8*inch, 3.6*inch])
    t_rbac.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), bg_light),
        ('TEXTCOLOR', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_rbac)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Default System Accounts for Evaluation:", h2_style))
    story.append(Paragraph("• <b>Admin Account:</b> Username: <code>admin</code> | Password: <code>admin123</code> | Role: Administrator", bullet_style))
    story.append(Paragraph("• <b>Technician Account:</b> Username: <code>tech</code> | Password: <code>tech123</code> | Role: Technician", bullet_style))
    story.append(Paragraph("• <b>Self-Registration & Password Recovery:</b> Built-in Sign-Up tab with security question verification.", bullet_style))

    # Section 3: Dataset Architecture
    story.append(Paragraph("3. Dataset Architecture (AI4I 2020)", h1_style))
    story.append(Paragraph(
        "The system processes the synthetic <b>AI4I 2020 Predictive Maintenance Dataset</b> (10,000 real-world industrial records across 14 operational features). The machine types are categorized into Quality Variants: <b>L (Low - 60%)</b>, <b>M (Medium - 30%)</b>, and <b>H (High - 10%)</b>.",
        body_style
    ))

    dataset_features = [
        [Paragraph("<b>Feature Name</b>", body_style), Paragraph("<b>Type</b>", body_style), Paragraph("<b>Description & Failure Modes</b>", body_style)],
        [Paragraph("Air temperature [K]", body_style), Paragraph("Float", body_style), Paragraph("Ambient room temperature in Kelvin.", body_style)],
        [Paragraph("Process temperature [K]", body_style), Paragraph("Float", body_style), Paragraph("Internal machine operating temperature. Heat Dissipation Failure (HDF) occurs if temp difference < 8.6 K and speed < 1380 rpm.", body_style)],
        [Paragraph("Rotational speed [rpm]", body_style), Paragraph("Integer", body_style), Paragraph("Spindle rotational speed. Power Failure (PWF) occurs if Power (Torque × Speed) < 3500 W or > 90000 W.", body_style)],
        [Paragraph("Torque [Nm]", body_style), Paragraph("Float", body_style), Paragraph("Torque exerted on the tool. Overstrain Failure (OSF) occurs if Torque × Tool Wear exceeds material limits.", body_style)],
        [Paragraph("Tool wear [min]", body_style), Paragraph("Integer", body_style), Paragraph("Cumulative tool usage time. Tool Wear Failure (TWF) occurs between 200–240 minutes.", body_style)],
        [Paragraph("Machine Failure / Specific Modes", body_style), Paragraph("Binary", body_style), Paragraph("Target indicators: TWF, HDF, PWF, OSF, and RNF (Random Failures).", body_style)]
    ]

    t_dataset = Table(dataset_features, colWidths=[1.8*inch, 1.0*inch, 4.4*inch])
    t_dataset.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), bg_light),
        ('TEXTCOLOR', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_dataset)
    story.append(Spacer(1, 10))

    # Section 4: Detailed Module Breakdown
    story.append(Paragraph("4. System Modules & Functional Architecture", h1_style))

    modules = [
        ("1. Authentication Gateway (components/auth_ui.py & utils/auth.py)",
         "Integrated single-page entry with modern glassmorphism design. Features 1-click quick demo buttons, account creation, password recovery, and automatic session page guards."),
        ("2. Maintenance Status Dashboard (1_Maintenance_Status_Dashboard.py)",
         "Real-time operational monitoring dashboard showing overdue tasks, upcoming 7-day maintenance schedules, active work orders, and historical maintenance resolution logs."),
        ("3. Exploratory Data Analysis - EDA (2_EDA.py) [Admin Only]",
         "Deep-dive statistical correlation charts, missing value inspection, distribution histograms, and failure type breakdown across machinery types."),
        ("4. Executive BI Dashboard (3_Dashboard.py) [Admin Only]",
         "Interactive Plotly visualization platform for exploring temperature deltas, torque vs. rotational speed distributions, and machine failure clustering."),
        ("5. Machine Explorer & AI Inspector (4_Machine_Explorer.py)",
         "Searchable machinery repository with detailed sensor health gauges. Integrates a local AI assistant (Ollama) to inspect individual machine conditions and auto-generate official PDF Work Orders."),
        ("6. Work Order Management (5_Work_Orders.py)",
         "Kanban-style tracking system for Open, In Progress, and Completed work orders. Allows technicians to record repair actions, assign staff, and export PDF work orders."),
        ("7. Preventive Maintenance Schedules (6_Maintenance_Schedules.py)",
         "Calendar-driven schedule planner supporting daily, weekly, monthly, and operating-hours frequencies with customizable inspection checklists."),
        ("8. AI Maintenance Recommendation Engine (7_AI_Maintenance_Recommendations.py) [Admin Only]",
         "Automated AI briefing engine synthesizing live equipment wear and open work orders into strategic executive maintenance recommendations.")
    ]

    for title, desc in modules:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(Spacer(1, 10))

    # Section 5: Technology Stack & Installation
    story.append(Paragraph("5. Technology Stack & Deployment Guide", h1_style))
    story.append(Paragraph("• <b>Frontend & Dashboard Framework:</b> Streamlit 1.59.2", bullet_style))
    story.append(Paragraph("• <b>Data Processing & Analytics:</b> Python 3.10+, Pandas, NumPy", bullet_style))
    story.append(Paragraph("• <b>Data Visualization:</b> Plotly Express & Plotly Graph Objects", bullet_style))
    story.append(Paragraph("• <b>Local AI Intelligence:</b> Ollama LLM integration (llama3 / mistral)", bullet_style))
    story.append(Paragraph("• <b>Document Engine:</b> ReportLab PDF Generation Library", bullet_style))
    story.append(Paragraph("• <b>Security Architecture:</b> Cryptographic SHA-256 password hashing & JSON storage", bullet_style))

    story.append(Paragraph("Command to Run Application:", h2_style))
    story.append(Paragraph("<code>streamlit run app.py</code>", code_style))

    doc.build(story)
    print(f"Successfully generated documentation PDF at: {pdf_path}")
    return str(pdf_path)

if __name__ == "__main__":
    build_pdf_documentation()
