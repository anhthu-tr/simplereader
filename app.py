from flask import Flask, render_template, request, send_file
import pdfplumber, requests
from readability import Document
from bs4 import BeautifulSoup
from fpdf import FPDF
from ebooklib import epub

app = Flask(__name__)
saved_content = ""

def extract_pdf_text(path):
    text = ''
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text

def extract_web_text(url):
    response = requests.get(url)
    doc = Document(response.text)
    soup = BeautifulSoup(doc.summary(), 'html.parser')
    return soup.get_text()

@app.route('/', methods=['GET', 'POST'])
def index():
    global saved_content
    content = ''
    if request.method == 'POST':
        if 'link' in request.form and request.form['link']:
            content = extract_web_text(request.form['link'])
        elif 'file' in request.files:
            file = request.files['file']
            filepath = "temp.pdf"
            file.save(filepath)
            content = extract_pdf_text(filepath)
        saved_content = content
    return render_template('reader.html', content=saved_content)

@app.route('/save', methods=['POST'])
def save():
    global saved_content
    fmt = request.form.get('format')
    filename = f"output.{fmt}"
    if fmt == 'txt':
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(saved_content)
        return send_file(filename, as_attachment=True)
    elif fmt == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in saved_content.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf.output(filename)
        return send_file(filename, as_attachment=True)
    elif fmt == 'epub':
        book = epub.EpubBook()
        book.set_title("Trình đọc đơn giản")
        book.set_language("vi")
        chapter = epub.EpubHtml(title='Nội dung', file_name='chap.xhtml', lang='vi')
        chapter.content = f"<h1>Nội dung</h1><p>{saved_content.replace('\n', '<br>')}</p>"
        book.add_item(chapter)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav', chapter]
        epub.write_epub(filename, book)
        return send_file(filename, as_attachment=True)
    return "Định dạng không hỗ trợ", 400

if __name__ == '__main__':
    app.run(debug=True)
