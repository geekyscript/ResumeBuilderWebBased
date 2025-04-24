from flask import Flask, render_template, request, send_file, redirect, url_for
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from textwrap import wrap
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def wrap_text(text, width):
    lines = []
    for line in text.split('\n'):
        lines.extend(wrap(line.strip(), width))
    return lines

@app.route('/', methods=['GET', 'POST'])
def resume_form():
    if request.method == 'POST':
        data = request.form.to_dict()
        file = request.files.get('photo')
        photo_path = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(photo_path)

        file_path = generate_pdf(data, photo_path)
        return send_file(file_path, as_attachment=True)

    return render_template('form.html')

def generate_pdf(data, photo_path):
    file_name = f"{data['name']}_Resume.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4
    margin_bottom = 50
    sidebar_width = width * 0.3
    content_x = sidebar_width + 10
    first_page = True
    page_number = 1

    def draw_sidebar():
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.rect(0, 0, sidebar_width, height, fill=1)
        if photo_path:
            c.drawImage(photo_path, 40, height - 120, width=80, height=80, mask='auto')

        sidebar_y = height - 140
        for title, content in [("SKILLS", data['skills']), ("LANGUAGES", data['languages']),
                               ("CERTIFICATES", data['certificates']), ("HONOR AWARDS", data['awards']),
                               ("INTERESTS", data['interests'])]:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.white)
            c.drawString(40, sidebar_y, f"• {title}")
            sidebar_y -= 18
            c.setFont("Helvetica", 10)
            for line in wrap_text(content, 32):
                c.drawString(50, sidebar_y, f"- {line}")
                sidebar_y -= 14
            sidebar_y -= 10

    def draw_left_bar_background():
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.rect(0, 0, sidebar_width, height, fill=1)

    def draw_header():
        nonlocal y
        y = height - 60
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawString(content_x, y, data['name'])
        y -= 20
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#7F8C8D"))
        c.drawString(content_x, y, f"Email: {data['email']} | Phone: {data['phone']}")
        y -= 30

    def draw_footer(page_num):
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#7F8C8D"))
        footer_text = f"Page {page_num}"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, 20, footer_text)

    def check_page_break(extra_space_needed=60):
        nonlocal y, first_page, page_number
        if y < margin_bottom + extra_space_needed:
            draw_footer(page_number)
            c.showPage()
            page_number += 1
            if first_page:
                first_page = False
            draw_left_bar_background()
            draw_header()

    def draw_main_block(title, content):
        nonlocal y
        check_page_break()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawString(content_x, y, f"• {title}")
        y -= 15
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        for line in wrap_text(content, 75):
            check_page_break()
            c.drawString(content_x + 10, y, line)
            y -= 12
        y -= 10

    def draw_main_section(title, content):
        nonlocal y
        check_page_break()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawString(content_x, y, f"• {title}")
        y -= 15
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        for line in content.split('\n'):
            check_page_break()
            if '|' in line:
                parts = line.split('|')
                job_title = parts[0].strip()
                company = parts[1].strip()
                location = parts[2].strip() if len(parts) > 2 else ''
                duration = parts[3].strip() if len(parts) > 3 else ''
                c.setFont("Helvetica-Bold", 10)
                c.drawString(content_x + 10, y, job_title)
                y -= 12
                c.setFont("Helvetica", 9)
                for wrapped_line in wrap(f"{company}, {location} ({duration})", 75):
                    check_page_break()
                    c.drawString(content_x + 12, y, wrapped_line)
                    y -= 12
            else:
                for wrapped_line in wrap(line.strip(), 75):
                    check_page_break()
                    c.drawString(content_x + 10, y, f"- {wrapped_line}")
                    y -= 12
        y -= 10

    y = height - 60
    draw_sidebar()
    draw_header()
    draw_main_block("PROFILE SUMMARY", data['summary'])
    draw_main_section("WORK EXPERIENCE", data['experience'])
    draw_main_section("EDUCATION", data['education'])
    draw_footer(page_number)
    c.save()
    return file_name

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
