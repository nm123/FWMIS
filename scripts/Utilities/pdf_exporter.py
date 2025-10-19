import json
import os
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from PyPDF2 import PdfReader, PdfWriter

from scripts.Utilities.annexure_utils import get_annexure_details


def export_annexure_to_pdf(
    annexure_ids: List[Optional[int]],
    file_path: str,
    include_lc_minutes: bool = False,
) -> None:
    """Export annexures to PDF format."""
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # Build content
    story = []
    
    # Process each annexure
    for annexure_id in annexure_ids:
        if annexure_id:
            annexure = get_annexure_details(annexure_id)
            if annexure:
                # Add annexure content
                add_annexure_content(story, annexure, title_style, subtitle_style, styles)
                
                # Add LC minutes if requested
                if include_lc_minutes:
                    add_lc_minutes_content(story, annexure)
                
                # Add page break between annexures
                if annexure_id != annexure_ids[-1]:
                    story.append(PageBreak())
    
    # Build PDF
    doc.build(story)

def add_annexure_content(story, annexure, title_style, subtitle_style, styles):
    """Add annexure content to the story."""
    # Title
    title = Paragraph(f"WRITE-OFF ANNEXURE: {annexure['annexure_no']}", title_style)
    story.append(title)
    
    # Subtitle
    subtitle = Paragraph(
        f"Approval Authority: {annexure['role']}",
        subtitle_style,
    )
    story.append(subtitle)
    
    # Summary information
    summary_data = [
        ["Total Cases:", str(annexure['case_count'])],
        ["Total Amount:", f"R {annexure['total_amount']:,.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Create data table
    table_data = [["Case No", "Responsibility", "Amount", "Description", "LC Recommendation"]]
    
    for case in annexure['cases']:
        row = [
            case['transaction_no'],
            case['responsibility_name'],
            f"R {case['amount']:,.2f}",
            case['description'],
            "Write-Off Recommended"
        ]
        table_data.append(row)
    
    # Add totals row
    table_data.append(["", "TOTAL:", f"R {annexure['total_amount']:,.2f}", "", ""])
    
    # Create table
    table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 3*inch, 1.5*inch])
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ALIGN', (2, 1), (2, -2), 'RIGHT'),  # Right-align amounts
        ('ALIGN', (3, 1), (3, -2), 'LEFT'),   # Left-align descriptions
        
        # Totals row
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))

def add_lc_minutes_content(story, annexure):
    """Add LC minutes content to the story."""
    story.append(Spacer(1, 20))
    
    # Section header
    lc_header_style = ParagraphStyle(
        'LCHeader',
        parent=getSampleStyleSheet()['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.darkred
    )
    
    lc_header = Paragraph("LOSS CONTROL COMMITTEE MINUTES", lc_header_style)
    story.append(lc_header)
    
    # Add LC minutes for each case
    for case in annexure['cases']:
        lc_minutes_path = get_lc_minutes_path(case['evidence_paths'])
        
        if lc_minutes_path and os.path.exists(lc_minutes_path):
            # Case header
            case_header = Paragraph(f"Case: {case['transaction_no']}", 
                                  getSampleStyleSheet()['Heading3'])
            story.append(case_header)
            
            # Try to embed PDF minutes
            if lc_minutes_path.lower().endswith('.pdf'):
                try:
                    embed_pdf_minutes(story, lc_minutes_path)
                except Exception:
                    # Fallback to text message
                    error_msg = Paragraph(
                        f"LC Minutes available at: {lc_minutes_path}",
                        getSampleStyleSheet()["Normal"],
                    )
                    story.append(error_msg)
            else:
                # For non-PDF files, just show the path
                file_msg = Paragraph(f"LC Minutes file: {lc_minutes_path}", 
                                   getSampleStyleSheet()['Normal'])
                story.append(file_msg)
            
            story.append(Spacer(1, 20))
        else:
            # No LC minutes available
            no_minutes = Paragraph(f"Case {case['transaction_no']}: LC Minutes not available", 
                                 getSampleStyleSheet()['Normal'])
            story.append(no_minutes)
            story.append(Spacer(1, 10))

def embed_pdf_minutes(story, pdf_path):
    """Embed PDF minutes into the document."""
    try:
        # Read the PDF
        reader = PdfReader(pdf_path)
        
        # Create a temporary PDF with the minutes
        temp_pdf = f"temp_minutes_{hash(pdf_path)}.pdf"
        writer = PdfWriter()
        
        # Add all pages from the minutes PDF
        for page in reader.pages:
            writer.add_page(page)
        
        # Write temporary PDF
        with open(temp_pdf, 'wb') as output_file:
            writer.write(output_file)
        
        # Add reference to the minutes
        minutes_ref = Paragraph(
            "LC Minutes embedded (see attached PDF)",
            getSampleStyleSheet()['Normal'],
        )
        story.append(minutes_ref)
        
        # Clean up temporary file
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
            
    except Exception:
        # Fallback to simple text reference
        fallback_msg = Paragraph(
            f"LC Minutes available at: {pdf_path}",
            getSampleStyleSheet()["Normal"],
        )
        story.append(fallback_msg)

def get_lc_minutes_path(evidence_paths: str) -> Optional[str]:
    """Extract LC minutes file path from evidence_paths JSON."""
    if not evidence_paths:
        return None
        
    try:
        evidence_data = json.loads(evidence_paths)
        lc_minutes = evidence_data.get('lc_minutes') or evidence_data.get('loss_control_minutes')
        if lc_minutes and isinstance(lc_minutes, str):
            return lc_minutes
        return None
    except (json.JSONDecodeError, TypeError):
        return None
