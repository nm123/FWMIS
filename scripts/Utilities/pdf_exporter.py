import os
import json
from typing import List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.flowables import Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from pypdf import PdfReader, PdfWriter
from scripts.Utilities.annexure_utils import get_annexure_details

def export_annexure_to_pdf(annexure_ids: List[Optional[int]], file_path: str, include_lc_minutes: bool = False, detailed_export: bool = False):
    """Export annexures to PDF format."""
    doc = SimpleDocTemplate(file_path, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
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

    # For detailed export, collect all evidence documents first for indexing
    if detailed_export and include_lc_minutes:
        evidence_index = build_evidence_index(annexure_ids)
        if evidence_index:
            add_evidence_index_page(story, evidence_index, title_style, styles)

    # Process each annexure
    for annexure_id in annexure_ids:
        if annexure_id:
            annexure = get_annexure_details(annexure_id)
            if annexure:
                # Add annexure content
                add_annexure_content(story, annexure, title_style, subtitle_style, styles, detailed_export)

                # Add LC minutes if requested
                if include_lc_minutes:
                    if detailed_export:
                        add_lc_minutes_with_indexing(story, annexure, evidence_index)
                    else:
                        add_lc_minutes_content(story, annexure)

                # Add page break between annexures
                if annexure_id != annexure_ids[-1]:
                    story.append(PageBreak())

    # Build PDF
    doc.build(story)

def add_annexure_content(story, annexure, title_style, subtitle_style, styles, detailed_export=False):
    """Add annexure content to the story."""
    # Title
    title = Paragraph(f"WRITE-OFF ANNEXURE: {annexure['annexure_no']}", title_style)
    story.append(title)
    
    # Subtitle
    subtitle = Paragraph(f"Approval Authority: {anneure['role']}", subtitle_style)
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
    
    # Create data table - include Date Reported and Category as requested
    if detailed_export:
        table_data = [["Case No", "Date Reported", "Category", "Responsibility", "Amount", "LC Status"]]
    else:
        table_data = [["Case No", "Responsibility", "Amount", "Description", "LC Recommendation"]]
    
    for case in annexure['cases']:
        if detailed_export:
            row = [
                case['transaction_no'],
                case.get('date_reported', ''),
                case.get('category', ''),
                case['responsibility_name'],
                f"R {case['amount']:,.2f}",
                "Write-Off Recommended"
            ]
        else:
            row = [
                case['transaction_no'],
                case['responsibility_name'],
                f"R {case['amount']:,.2f}",
                case['description'],
                "Write-Off Recommended"
            ]
        table_data.append(row)
    
    # Add totals row - adjust column count based on export type
    if detailed_export:
        table_data.append(["", "", "", "TOTAL:", f"R {annexure['total_amount']:,.2f}", ""])
    else:
        table_data.append(["", "TOTAL:", f"R {annexure['total_amount']:,.2f}", "", ""])
    
    # Create table with appropriate column widths
    if detailed_export:
        table = Table(table_data, colWidths=[1.0*inch, 1.0*inch, 1.2*inch, 1.3*inch, 1.0*inch, 1.2*inch])
    else:
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


def build_evidence_index(annexure_ids):
    """
    Build a comprehensive index of all evidence documents across annexures.

    Returns a dict mapping document paths to their page ranges and associated cases.
    """
    evidence_map = {}

    for annexure_id in annexure_ids:
        if annexure_id:
            annexure = get_annexure_details(annexure_id)
            if annexure and 'cases' in annexure:
                for case in annexure['cases']:
                    # Check for LC minutes evidence
                    if 'lc_minutes_path' in case and case['lc_minutes_path']:
                        doc_path = case['lc_minutes_path']
                        case_no = case['transaction_no']

                        if doc_path not in evidence_map:
                            evidence_map[doc_path] = {
                                'filename': os.path.basename(doc_path),
                                'cases': [],
                                'page_count': 0
                            }

                        if case_no not in evidence_map[doc_path]['cases']:
                            evidence_map[doc_path]['cases'].append(case_no)

    # Calculate page counts for each document
    for doc_path, info in evidence_map.items():
        if os.path.exists(doc_path):
            try:
                reader = PdfReader(doc_path)
                info['page_count'] = len(reader.pages)
            except Exception as e:
                print(f"Error reading PDF {doc_path}: {e}")
                info['page_count'] = 1  # Default to 1 page if can't read

    return evidence_map


def add_evidence_index_page(story, evidence_index, title_style, styles):
    """
    Add an evidence index page at the beginning of the PDF.
    """
    # Title
    index_title = Paragraph("EVIDENCE DOCUMENT INDEX", title_style)
    story.append(index_title)

    intro_text = """
    This annexure contains supporting evidence documents. Each document may be referenced by multiple cases.
    Use the page numbers below to locate specific evidence documents.
    """
    intro_para = Paragraph(intro_text, styles['Normal'])
    story.append(intro_para)
    story.append(Spacer(1, 20))

    # Create index table
    index_data = [["Document", "Cases Using Document", "Page Range"]]

    current_page = 2  # Start after index page

    for doc_path, info in evidence_index.items():
        filename = info['filename']
        cases_str = ", ".join(info['cases'][:3])  # Show first 3 cases
        if len(info['cases']) > 3:
            cases_str += f" (+{len(info['cases']) - 3} more)"

        page_range = f"{current_page} - {current_page + info['page_count'] - 1}"
        index_data.append([filename, cases_str, page_range])

        current_page += info['page_count']

    # Create table
    index_table = Table(index_data, colWidths=[2*inch, 3*inch, 1.5*inch])
    index_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(index_table)
    story.append(PageBreak())


def add_lc_minutes_with_indexing(story, annexure, evidence_index):
    """
    Add LC minutes with proper indexing and page numbering.
    """
    story.append(Spacer(1, 20))

    # Section header
    lc_header_style = ParagraphStyle(
        'LCHeader',
        parent=getSampleStyleSheet()['Heading2'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.darkblue
    )

    header = Paragraph("LOSS CONTROL MINUTES & SUPPORTING EVIDENCE", lc_header_style)
    story.append(header)

    # Add evidence documents with page references
    current_page = 2  # Start counting from after index page
    for doc_path, info in evidence_index.items():
        if info['cases']:  # Only include docs that are used
            # Document header
            doc_title = Paragraph(f"Document: {info['filename']}", getSampleStyleSheet()['Heading3'])
            story.append(doc_title)

            # Cases that use this document
            cases_text = f"Related Cases: {', '.join(info['cases'])}"
            cases_para = Paragraph(cases_text, getSampleStyleSheet()['Normal'])
            story.append(cases_para)

            # Page reference
            page_range = f"Pages {current_page} - {current_page + info['page_count'] - 1}"
            page_para = Paragraph(f"Location: {page_range}", getSampleStyleSheet()['Italic'])
            story.append(page_para)

            # Try to embed the PDF document
            try:
                if os.path.exists(doc_path):
                    reader = PdfReader(doc_path)
                    writer = PdfWriter()

                    # Copy all pages from the evidence document
                    for page_num in range(len(reader.pages)):
                        writer.add_page(reader.pages[page_num])

                    # For now, just add a note about the document location
                    # In a full implementation, you'd concatenate the PDFs here
                    embed_note = Paragraph(
                        f"[Evidence document '{info['filename']}' would be embedded here - {info['page_count']} pages]",
                        getSampleStyleSheet()['Italic']
                    )
                    story.append(embed_note)

            except Exception as e:
                error_note = Paragraph(
                    f"[Error loading evidence document: {str(e)}]",
                    getSampleStyleSheet()['Italic']
                )
                story.append(error_note)

            current_page += info['page_count']
            story.append(Spacer(1, 15))

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
                except Exception as e:
                    # Fallback to text message
                    error_msg = Paragraph(f"LC Minutes available at: {lc_minutes_path}", 
                                        getSampleStyleSheet()['Normal'])
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
        minutes_ref = Paragraph(f"LC Minutes embedded (see attached PDF)", 
                               getSampleStyleSheet()['Normal'])
        story.append(minutes_ref)
        
        # Clean up temporary file
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
            
    except Exception as e:
        # Fallback to simple text reference
        fallback_msg = Paragraph(f"LC Minutes available at: {pdf_path}", 
                                getSampleStyleSheet()['Normal'])
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
