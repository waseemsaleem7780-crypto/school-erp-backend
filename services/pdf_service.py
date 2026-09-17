from database.db import get_db_connection, get_dict_cursor
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime


def generate_student_report_card(student_id: int):
    """Ek student ka PDF report card generate karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Student info
    cursor.execute("""
        SELECT s.id, s.roll_number, s.class_id, s.section_id,
               u.full_name, u.email,
               c.name as class_name, sec.name as section_name
        FROM students s
        LEFT JOIN users u ON u.id = s.user_id
        LEFT JOIN classes c ON c.id = s.class_id
        LEFT JOIN sections sec ON sec.id = s.section_id
        WHERE s.id = %s
    """, (student_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return None

    # Attendance summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'present') as present,
            COUNT(*) FILTER (WHERE status = 'half_day') as half_day
        FROM attendance 
        WHERE student_id = %s
    """, (student_id,))
    attendance = cursor.fetchone()

    # Results
    cursor.execute("""
        SELECT r.marks_obtained, r.grade, r.remarks,
               s.name as subject_name, s.code as subject_code,
               e.name as exam_name
        FROM results r
        LEFT JOIN subjects s ON s.id = r.subject_id
        LEFT JOIN exam e ON e.id = r.exam_id
        WHERE r.student_id = %s
        ORDER BY e.name, s.name
    """, (student_id,))
    results = cursor.fetchall()

    # Fee summary
    cursor.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM fee_payment WHERE student_id = %s
    """, (student_id,))
    fees = cursor.fetchone()

    conn.close()

    # ================= PDF Banao =================
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        alignment=1,
        spaceAfter=20,
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#718096'),
        alignment=1,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a202c'),
        spaceBefore=15,
        spaceAfter=10,
    )

    elements = []

    # Header
    elements.append(Paragraph("🎓 School ERP System", title_style))
    elements.append(Paragraph("Student Report Card", subtitle_style))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 20))

    # Student Info Table
    elements.append(Paragraph("📋 Student Information", section_style))
    student_data = [
        ['Name', student['full_name'] or 'N/A', 'Roll No', student['roll_number'] or 'N/A'],
        ['Class', student['class_name'] or 'N/A', 'Section', student['section_name'] or 'N/A'],
        ['Email', student['email'] or 'N/A', 'Student ID', f"#{student['id']}"],
    ]
    student_table = Table(student_data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 2.5*inch])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a202c')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 15))

    # Attendance Summary
    elements.append(Paragraph("📅 Attendance Summary", section_style))
    total = attendance['total'] or 0
    present = attendance['present'] or 0
    half_day = attendance['half_day'] or 0
    percentage = round((present / total * 100), 2) if total > 0 else 0

    attendance_data = [
        ['Total Days', 'Present', 'Half Day', 'Attendance %'],
        [str(total), str(present), str(half_day), f'{percentage}%'],
    ]
    attendance_table = Table(attendance_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 2*inch])
    attendance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    elements.append(attendance_table)
    elements.append(Spacer(1, 15))

    # Results
    elements.append(Paragraph("🏆 Exam Results", section_style))
    if results:
        results_data = [['Subject', 'Code', 'Marks', 'Grade', 'Remarks']]
        for r in results:
            results_data.append([
                r['subject_name'] or 'N/A',
                r['subject_code'] or 'N/A',
                str(r['marks_obtained']) if r['marks_obtained'] else 'N/A',
                r['grade'] or 'N/A',
                r['remarks'] or '—',
            ])
        results_table = Table(results_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1.8*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (3, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(results_table)
    else:
        elements.append(Paragraph("No results recorded yet.", styles['Normal']))

    elements.append(Spacer(1, 15))

    # Fee Summary
    elements.append(Paragraph("💰 Fee Summary", section_style))
    fee_data = [
        ['Total Payments', 'Total Amount Paid'],
        [str(fees['count'] or 0), f"Rs. {fees['total'] or 0:,}"],
    ]
    fee_table = Table(fee_data, colWidths=[3*inch, 3.8*inch])
    fee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f6ad55')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(fee_table)
    elements.append(Spacer(1, 30))

    # Footer
    elements.append(Paragraph(
        "This is a computer-generated report card. No signature required.",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#a0aec0'),
            alignment=1,
        )
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer