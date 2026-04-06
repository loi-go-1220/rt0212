from django.http import HttpResponse
from django.conf import settings
from io import BytesIO
import markdown
from xhtml2pdf import pisa
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from htmldocx import HtmlToDocx
import re
import os
import html


class PDFGenerator:
    """
    Utility class for generating PDF files from resume content
    """
    
    @staticmethod
    def _get_absolute_font_path(font_filename):
        """Get the absolute path to a font file"""
        return os.path.join(settings.BASE_DIR, 'static', 'fonts', font_filename)
    
    @staticmethod
    def generate_resume_pdf(profile_name, company_name, job_title, tailored_resume_text):
        """
        Generate a PDF resume using xhtml2pdf
        """
        import time
        pdf_gen_start = time.time()
        
        # Convert markdown to HTML with extensions for better compatibility
        # Use 'extra' extension which includes many useful features
        # Don't use 'nl2br' as it can cause issues with line breaks
        markdown_start = time.time()
        html_content = markdown.markdown(
            tailored_resume_text,
            extensions=['extra'],
            output_format='html5'
        )
        markdown_time = time.time() - markdown_start
        print(f"📄 [PDF-MD] Markdown to HTML conversion: {markdown_time*1000:.1f}ms")
        
        # Clean up any escaped HTML that should be rendered
        # If the source markdown has &nbsp; as text, replace with space
        html_content = html_content.replace('&amp;nbsp;', '&nbsp;')
        html_content = html_content.replace('&lt;u&gt;', '<u>')
        html_content = html_content.replace('&lt;/u&gt;', '</u>')
        html_content = html_content.replace('&lt;br&gt;', '<br/>')
        html_content = html_content.replace('&lt;br/&gt;', '<br/>')
        html_content = html_content.replace('&lt;br /&gt;', '<br/>')
        
        # Create full HTML document with styling
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{profile_name} - {job_title} at {company_name} Resume</title>
    <style type="text/css">
        @page {{
            size: A4;
            margin: 50px 45px;
        }}
        
        body {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333333;
        }}
        
        h1 {{
            color: #000000;
            font-size: 20px;
            font-weight: bold;
            margin: 0 0 4px 0;
            padding: 0;
        }}
        
        h2 {{
            color: #000000;
            font-size: 15px;
            font-weight: bold;
            margin: 12px 0 8px 0;
            padding: 0 0 2px 0;
            border-bottom: 1px solid #000000;
        }}
        
        h3 {{
            color: #000000;
            font-size: 13px;
            font-weight: bold;
            margin: 4px 0 6px 0;
            padding: 0;
        }}
        
        p {{
            margin: 0 0 4px 0;
            padding: 0;
            text-align: justify;
        }}
        
        ul {{
            margin: 0 0 0 0;
            padding: 0 0 0 20px;
            list-style-type: disc;
        }}
        
        ol {{
            margin: 0 0 0 0;
            padding: 0 0 0 20px;
        }}
        
        li {{
            margin: 0 0 2px 0;
            padding: 0;
        }}
        
        strong {{
            font-weight: bold;
        }}
        
        b {{
            font-weight: bold;
        }}
        
        hr {{
            display: none;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        # Create PDF from HTML
        html_build_time = time.time() - markdown_start
        print(f"📄 [PDF-HTML] HTML document build: {html_build_time*1000:.1f}ms")
        
        pdf_create_start = time.time()
        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            full_html,
            dest=buffer,
            encoding='utf-8'
        )
        pdf_create_time = time.time() - pdf_create_start
        print(f"📄 [PDF-CREATE] PDF creation (pisa): {pdf_create_time*1000:.1f}ms")
        
        # Check for errors
        if pisa_status.err:
            buffer.close()
            print(f"❌ [PDF-ERROR] PDF generation failed with pisa errors")
            return HttpResponse('Error generating PDF', status=500)
        
        # Get PDF content
        response_start = time.time()
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create HTTP response
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"{profile_name}_{company_name}.pdf".replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        response_time = time.time() - response_start
        total_pdf_time = time.time() - pdf_gen_start
        print(f"📄 [PDF-RESPONSE] HTTP response creation: {response_time*1000:.1f}ms")
        print(f"📄 [PDF-TOTAL] Total PDF generation: {total_pdf_time*1000:.1f}ms")
        print(f"📄 [PDF-SIZE] Generated PDF size: {len(pdf)} bytes")
        
        return response
    
    @staticmethod
    def generate_resume_docx(profile_name, company_name, job_title, tailored_resume_text):
        """
        Generate a DOCX resume using python-docx and htmldocx
        """
        import time
        docx_gen_start = time.time()

        # Convert markdown to HTML
        markdown_start = time.time()
        html_content = markdown.markdown(
            tailored_resume_text,
            extensions=['extra'],
            output_format='html5'
        )
        markdown_time = time.time() - markdown_start
        print(f"📄 [DOCX-MD] Markdown to HTML conversion: {markdown_time*1000:.1f}ms")

        # Clean up escaped HTML
        html_content = html_content.replace('&amp;nbsp;', '&nbsp;')
        html_content = html_content.replace('&lt;u&gt;', '<u>')
        html_content = html_content.replace('&lt;/u&gt;', '</u>')
        html_content = html_content.replace('&lt;br&gt;', '<br/>')
        html_content = html_content.replace('&lt;br/&gt;', '<br/>')
        html_content = html_content.replace('&lt;br /&gt;', '<br/>')

        # Build DOCX document
        doc = Document()

        # Set narrow margins (1.27 cm ~ 720 twips)
        from docx.shared import Cm
        for section in doc.sections:
            section.top_margin = Cm(1.8)
            section.bottom_margin = Cm(1.8)
            section.left_margin = Cm(1.6)
            section.right_margin = Cm(1.6)

        # Set default body font
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)

        # Style heading levels
        for heading_level, size in [('Heading 1', 16), ('Heading 2', 13), ('Heading 3', 11)]:
            h_style = doc.styles[heading_level]
            h_style.font.color.rgb = RGBColor(0, 0, 0)
            h_style.font.size = Pt(size)
            h_style.font.bold = True

        # Parse HTML into document
        parser = HtmlToDocx()
        parser.add_html_to_document(html_content, doc)

        docx_create_time = time.time() - docx_gen_start
        print(f"📄 [DOCX-CREATE] Document build: {docx_create_time*1000:.1f}ms")

        # Save to buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        filename = f"{profile_name}_{company_name}.docx".replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        total_time = time.time() - docx_gen_start
        print(f"📄 [DOCX-TOTAL] Total DOCX generation: {total_time*1000:.1f}ms")
        print(f"📄 [DOCX-SIZE] Generated DOCX size: {buffer.getbuffer().nbytes} bytes")

        buffer.close()
        return response

    @staticmethod
    def generate_cover_letter_txt(profile_name, company_name, cover_letter_text):
        """
        Generate a downloadable text file for cover letter
        """
        # Clean up the markdown formatting for plain text
        plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cover_letter_text)  # Remove bold
        plain_text = re.sub(r'\*(.*?)\*', r'\1', plain_text)  # Remove italic
        plain_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', plain_text)  # Remove links, keep text
        
        # Create HTTP response
        response = HttpResponse(plain_text, content_type='text/plain')
        filename = f"{profile_name}_{company_name}_CoverLetter.txt".replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
