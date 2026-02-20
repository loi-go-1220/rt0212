from django.http import HttpResponse
from django.conf import settings
from io import BytesIO
import markdown
from xhtml2pdf import pisa
import re
import os
import time


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
        Generate a PDF file from tailored resume text
        
        Args:
            profile_name (str): User's name
            company_name (str): Target company name
            job_title (str): Job title
            tailored_resume_text (str): Markdown formatted resume text
            
        Returns:
            HttpResponse: PDF file response for download
        """
        start_time = time.time()
        print(f"DEBUG: Starting PDF generation at {start_time}")
        
        # Convert markdown to HTML
        markdown_start = time.time()
        html_content = PDFGenerator._markdown_to_html(
            tailored_resume_text, 
            profile_name, 
            company_name, 
            job_title
        )
        markdown_time = time.time() - markdown_start
        print(f"DEBUG: Markdown conversion took {markdown_time:.2f} seconds")
        
        # Create PDF from HTML (using system fonts for reliability)
        pdf_start = time.time()
        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=buffer,
            encoding='utf-8'
        )
        pdf_time = time.time() - pdf_start
        print(f"DEBUG: PDF creation took {pdf_time:.2f} seconds")
        
        # Check for errors
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        
        # Get the PDF from the buffer
        response_start = time.time()
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create the HttpResponse object with PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{profile_name}_{company_name}_resume.pdf"'
        response.write(pdf)
        
        response_time = time.time() - response_start
        total_time = time.time() - start_time
        print(f"DEBUG: Response creation took {response_time:.2f} seconds")
        print(f"DEBUG: Total PDF generation took {total_time:.2f} seconds")
        
        return response
    
    @staticmethod
    def generate_cover_letter_txt(profile_name, company_name, cover_letter_text):
        """
        Generate a downloadable text file for cover letter
        """
        # Convert markdown to plain text (remove markdown formatting)
        plain_text = PDFGenerator._markdown_to_plain_text(cover_letter_text)
        
        # Create the HttpResponse object with text content
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{profile_name}_{company_name}_cover_letter.txt"'
        response.write(plain_text)
        
        return response
    
    @staticmethod
    def _markdown_to_plain_text(markdown_text):
        """
        Convert markdown text to plain text, preserving line breaks and removing markdown syntax
        """
        # Remove markdown bold formatting (**text** -> text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', markdown_text)
        
        # Remove markdown italic formatting (*text* -> text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Convert markdown line breaks to actual line breaks
        text = text.replace('  \n', '\n')  # Two spaces + newline = line break
        text = text.replace('\n\n', '\n')  # Double newlines to single
        
        # Clean up any remaining markdown syntax
        text = re.sub(r'#{1,6}\s*', '', text)  # Remove headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links, keep text
        
        return text.strip()
    
    @staticmethod
    def _markdown_to_html(markdown_text, profile_name, company_name, job_title):
        """
        Convert Markdown text to formatted HTML suitable for PDF generation
        
        Args:
            markdown_text (str): Resume content in Markdown format
            profile_name (str): User's name
            company_name (str): Target company name  
            job_title (str): Job title
            
        Returns:
            str: HTML content with embedded CSS styling
        """
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_text,
            extensions=['fenced_code', 'tables', 'toc']
        )
        
        # Wrap in complete HTML document with styling
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{profile_name} - {company_name} Resume</title>
            <style>
                @page {{
                    size: A4;
                    margin: 50px 45px;
                }}
                
                body {{
                    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}
                
                h1 {{
                    color: #CA3832;
                    font-size: 20px;
                    font-weight: bold;
                    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                    margin-top: 0;
                    margin-bottom: 4px;
                    text-align: left;
                }}
                
                h1 + p {{
                    color: #111;
                    font-weight: bold;
                    line-height: 1.2;
                    margin-bottom: 8px;
                }}
                
                h2 {{
                    color: #CA3832;
                    font-size: 15px;
                    font-weight: bold;
                    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                    margin-top: 12px;
                    margin-bottom: 8px;
                    border-bottom: 1px solid #CA3832;
                    padding-bottom: 2px;
                }}
                
                h3 {{
                    color: #CA3832;
                    font-size: 13px;
                    font-weight: bold;
                    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                    margin-top: 4px;
                    margin-bottom: 6px;
                }}
                
                p {{
                    margin-bottom: 4px;
                    margin-top: 0;
                    text-align: justify;
                }}
                
                p em {{
                    line-height: 1.1;
                }}
                
                ul, ol {{
                    margin-bottom: 0;
                    padding-left: 1.1em;
                    margin-left: 0;
                }}
                
                li {{
                    margin-bottom: 2px;
                    line-height: 1.4;
                }}
                
                strong {{
                    font-weight: bold;
                    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                }}
                
                b {{
                    font-weight: bold;
                    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                }}
                
                em {{
                    font-style: italic;
                }}
                
                a {{
                    color: #CA3832;
                    text-decoration: underline;
                }}
                
                /* Hide horizontal rules (---) */
                hr {{
                    display: none;
                }}
                
                /* Prevent page breaks inside elements */
                h1, h2, h3 {{
                    page-break-after: avoid;
                }}
                
                ul, ol {{
                    page-break-inside: avoid;
                }}
                
                li {{
                    page-break-inside: avoid;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        return full_html