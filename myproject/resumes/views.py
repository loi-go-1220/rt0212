from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from collections import OrderedDict
from .models import Resume, InterviewQuestionAnswer
from .forms import ResumeBuilderForm, ResumeSearchForm
from .services import ResumeAIService
from .utils import PDFGenerator
import markdown
import html
import time


@login_required
def dashboard(request):
    """
    Main dashboard view - Resume builder page
    """
    profile = getattr(request.user, 'profile', None)
    default_name = (getattr(profile, 'default_name', '') or '').strip()
    default_base_resume = getattr(profile, 'default_base_resume', '') if profile else ''

    if request.method == 'POST':
        post_data = request.POST.copy()
        # If defaults exist, force them on the server side (dashboard inputs may be disabled)
        if default_name:
            post_data['profile_name'] = default_name
        if default_base_resume:
            post_data['initial_resume_text'] = default_base_resume

        form = ResumeBuilderForm(post_data)
        if form.is_valid():
            # Create resume instance but don't save yet
            resume = form.save(commit=False)
            resume.user = request.user
            resume.status = 'pending'
            resume.job_title = 'Position'  # Default value since we removed the input
            resume.save()
            
            try:
                total_start = time.time()
                print(f"🚀 [RESUME-GEN] Starting resume generation process for {resume.target_company}")
                print(f"📊 [RESUME-GEN] Resume ID: {resume.id}, User: {request.user.username}")
                print(f"📝 [RESUME-GEN] Initial resume length: {len(resume.initial_resume_text)} chars")
                print(f"📋 [RESUME-GEN] Job description length: {len(resume.job_description)} chars")
                
                # Test database connection
                db_test_start = time.time()
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                db_test_time = time.time() - db_test_start
                print(f"🔗 [DB-TEST] Database connection test: {db_test_time*1000:.1f}ms")
                
                # Use AI service to tailor resume
                ai_start = time.time()
                print(f"🤖 [AI-START] Initializing AI service...")
                ai_service = ResumeAIService()
                ai_init_time = time.time() - ai_start
                print(f"🤖 [AI-INIT] AI service initialization: {ai_init_time*1000:.1f}ms")
                
                ai_call_start = time.time()
                print(f"🤖 [AI-CALL] Calling OpenAI API for resume tailoring...")
                tailored_text = ai_service.tailor_resume(
                    initial_resume=resume.initial_resume_text,
                    job_description=resume.job_description
                )
                ai_call_time = time.time() - ai_call_start
                ai_total_time = time.time() - ai_start
                print(f"🤖 [AI-DONE] OpenAI API call: {ai_call_time:.2f}s")
                print(f"🤖 [AI-TOTAL] Total AI processing: {ai_total_time:.2f}s")
                print(f"📝 [AI-OUTPUT] Generated resume length: {len(tailored_text)} chars")
                
                # Update resume with tailored content
                db_save_start = time.time()
                print(f"💾 [DB-SAVE] Saving tailored resume to database...")
                resume.tailored_resume_text = tailored_text
                resume.status = 'completed'
                resume.save()
                db_save_time = time.time() - db_save_start
                print(f"💾 [DB-SAVE] Database save completed: {db_save_time*1000:.1f}ms")
                
                # Generate and return DOCX directly
                docx_start = time.time()
                print(f"📄 [DOCX-START] Generating DOCX document...")
                response = PDFGenerator.generate_resume_docx(
                    profile_name=resume.profile_name,
                    company_name=resume.target_company,
                    job_title=resume.job_title or 'Position',
                    tailored_resume_text=resume.tailored_resume_text
                )
                docx_time = time.time() - docx_start
                print(f"📄 [DOCX-DONE] DOCX generation completed: {docx_time:.2f}s")
                
                total_time = time.time() - total_start
                print(f"✅ [COMPLETE] Total process time: {total_time:.2f}s")
                print(f"📊 [BREAKDOWN] AI: {ai_total_time:.2f}s ({ai_total_time/total_time*100:.1f}%), DB: {(db_test_time+db_save_time)*1000:.1f}ms, DOCX: {docx_time:.2f}s ({docx_time/total_time*100:.1f}%)")
                
                return response
                
            except Exception as e:
                error_time = time.time() - total_start
                print(f"❌ [ERROR] Resume generation failed after {error_time:.2f}s: {str(e)}")
                print(f"❌ [ERROR] Exception type: {type(e).__name__}")
                
                # Mark resume as failed and save error
                db_error_start = time.time()
                resume.status = 'failed'
                resume.error_message = str(e)
                resume.save()
                db_error_time = time.time() - db_error_start
                print(f"💾 [DB-ERROR] Error state saved to database: {db_error_time*1000:.1f}ms")
                
                messages.error(request, f'Failed to generate resume: {str(e)}')
                return redirect('dashboard')
    else:
        # GET request: show the form with pre-loaded data from user profile
        initial_data = {}
        
        # Load default name from user profile, fallback to 'Matthew'
        if default_name:
            initial_data['profile_name'] = default_name
        else:
            initial_data['profile_name'] = 'Matthew'  # Fallback default
        
        # Load default base resume from user profile only
        if default_base_resume:
            initial_data['initial_resume_text'] = default_base_resume
        
        form = ResumeBuilderForm(initial=initial_data)
    
    # Get recent resumes for display
    recent_resumes = Resume.objects.filter(user=request.user)[:5]
    
    context = {
        'form': form,
        'recent_resumes': recent_resumes,
        'lock_profile_name': bool(default_name),
        'lock_initial_resume_text': bool(default_base_resume),
    }
    
    return render(request, 'resumes/dashboard.html', context)


@login_required
def resume_history(request):
    """
    Resume history list view with search and filtering, grouped by date
    """
    # Handle DOCX download from history page
    if request.method == 'POST' and 'download' in request.POST:
        resume_id = request.POST.get('resume_id')
        if resume_id:
            try:
                resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
                if resume.status == 'completed' and resume.tailored_resume_text:
                    print(f"📥 [HISTORY-DOWNLOAD] Starting DOCX download for resume ID: {resume.id}")
                    from .utils import PDFGenerator
                    response = PDFGenerator.generate_resume_docx(
                        profile_name=resume.profile_name,
                        company_name=resume.target_company,
                        job_title=resume.job_title or 'Position',
                        tailored_resume_text=resume.tailored_resume_text
                    )
                    return response
                else:
                    messages.error(request, 'Resume is not ready for download.')
            except Exception as e:
                print(f"❌ [HISTORY-DOWNLOAD] Download failed: {str(e)}")
                messages.error(request, f'Failed to download resume: {str(e)}')
    
    # Get all user's resumes
    resumes = Resume.objects.filter(user=request.user)
    
    # Handle search and filtering
    search_form = ResumeSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        status_filter = search_form.cleaned_data.get('status')
        
        if search_query:
            resumes = resumes.filter(
                Q(target_company__icontains=search_query) |
                Q(job_title__icontains=search_query) |
                Q(profile_name__icontains=search_query)
            )
        
        if status_filter:
            resumes = resumes.filter(status=status_filter)
    
    # Pagination with 100 resumes per page
    paginator = Paginator(resumes, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Group resumes by date
    resumes_by_date = OrderedDict()
    for resume in page_obj:
        date_key = resume.created_at.date()
        if date_key not in resumes_by_date:
            resumes_by_date[date_key] = []
        resumes_by_date[date_key].append(resume)
    
    # Get date counts for the current page
    date_counts = {}
    for date_key, resume_list in resumes_by_date.items():
        date_counts[date_key] = len(resume_list)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': resumes.count(),
        'resumes_by_date': resumes_by_date,
        'date_counts': date_counts,
    }
    
    return render(request, 'resumes/history.html', context)


@login_required
def resume_detail(request, pk):
    """
    Resume detail view - Shows full resume information
    """
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    # Handle DOCX download (no regeneration)
    if request.method == 'POST' and 'download' in request.POST:
        if resume.status == 'completed' and resume.tailored_resume_text:
            download_start = time.time()
            print(f"📥 [DOWNLOAD] Starting DOCX download for resume ID: {resume.id}")
            response = PDFGenerator.generate_resume_docx(
                profile_name=resume.profile_name,
                company_name=resume.target_company,
                job_title=resume.job_title or 'Position',
                tailored_resume_text=resume.tailored_resume_text
            )
            download_time = time.time() - download_start
            print(f"📥 [DOWNLOAD] DOCX download completed: {download_time:.2f}s")
            return response
        else:
            print(f"❌ [DOWNLOAD] Download failed - Resume not ready. Status: {resume.status}")
            messages.error(request, 'Resume is not ready for download.')
    
    # Handle regeneration (calls OpenAI again)
    if request.method == 'POST' and 'regenerate' in request.POST:
        try:
            regen_start = time.time()
            print(f"🔄 [REGEN] Starting resume regeneration for ID: {resume.id}")
            
            # Use AI service to re-tailor resume
            ai_start = time.time()
            print(f"🤖 [REGEN-AI] Initializing AI service for regeneration...")
            ai_service = ResumeAIService()
            tailored_text = ai_service.tailor_resume(
                initial_resume=resume.initial_resume_text,
                job_description=resume.job_description
            )
            ai_time = time.time() - ai_start
            print(f"🤖 [REGEN-AI] AI regeneration completed: {ai_time:.2f}s")
            
            # Update resume
            db_start = time.time()
            print(f"💾 [REGEN-DB] Updating resume in database...")
            resume.tailored_resume_text = tailored_text
            resume.status = 'completed'
            resume.error_message = None
            resume.save()
            db_time = time.time() - db_start
            print(f"💾 [REGEN-DB] Database update completed: {db_time*1000:.1f}ms")
            
            messages.success(request, 'Resume regenerated successfully! DOCX download will start automatically.')

            # Generate and return DOCX
            docx_start = time.time()
            print(f"📄 [REGEN-DOCX] Generating DOCX for regenerated resume...")
            response = PDFGenerator.generate_resume_docx(
                profile_name=resume.profile_name,
                company_name=resume.target_company,
                job_title=resume.job_title or 'Position',
                tailored_resume_text=resume.tailored_resume_text
            )
            docx_time = time.time() - docx_start
            total_regen_time = time.time() - regen_start
            print(f"📄 [REGEN-DOCX] DOCX generation completed: {docx_time:.2f}s")
            print(f"✅ [REGEN-COMPLETE] Total regeneration time: {total_regen_time:.2f}s")
            
            return response
            
        except Exception as e:
            resume.status = 'failed'
            resume.error_message = str(e)
            resume.save()
            messages.error(request, f'Failed to regenerate resume: {str(e)}')
    
    # Handle question answering
    if request.method == 'POST' and ('generate_answer' in request.POST or 
                                     (request.POST.get('form_type') == 'question_form' and 
                                      'clear_answer' not in request.POST)):
        question = request.POST.get('question', '').strip()
        
        if question and resume.status == 'completed' and resume.tailored_resume_text:
            try:
                ai_service = ResumeAIService()
                generated_answer = ai_service.generate_question_answer(
                    job_description=resume.job_description,
                    tailored_resume=resume.tailored_resume_text,
                    question=question
                )
                
                # Save the question and answer to database
                InterviewQuestionAnswer.objects.create(
                    resume=resume,
                    question=question,
                    answer=generated_answer
                )
                
                messages.success(request, 'Answer generated and saved successfully!')
                return redirect('resume_detail', pk=resume.id)
                
            except Exception as e:
                messages.error(request, f'Failed to generate answer: {str(e)}')
        else:
            if not question:
                messages.error(request, 'Please enter a question.')
            else:
                messages.error(request, 'Resume must be completed before generating answers.')
    
    # Handle clearing question and answer
    if request.method == 'POST' and 'clear_answer' in request.POST:
        qa_id = request.POST.get('qa_id')
        if qa_id:
            try:
                qa_item = InterviewQuestionAnswer.objects.get(
                    id=qa_id, 
                    resume=resume
                )
                qa_item.delete()
                messages.info(request, 'Question and answer deleted.')
            except InterviewQuestionAnswer.DoesNotExist:
                messages.error(request, 'Question and answer not found.')
        return redirect('resume_detail', pk=resume.id)
    
    # Handle cover letter generation
    if request.method == 'POST' and ('generate_cover_letter' in request.POST or 
                                     request.POST.get('form_type') == 'cover_letter_form'):
        if resume.status == 'completed' and resume.tailored_resume_text:
            try:
                ai_service = ResumeAIService()
                cover_letter_text = ai_service.generate_cover_letter(
                    job_description=resume.job_description,
                    tailored_resume=resume.tailored_resume_text,
                    company_name=resume.target_company
                )
                
                # Generate and return text file directly
                return PDFGenerator.generate_cover_letter_txt(
                    profile_name=resume.profile_name,
                    company_name=resume.target_company,
                    cover_letter_text=cover_letter_text
                )
                
            except Exception as e:
                messages.error(request, f'Failed to generate cover letter: {str(e)}')
        else:
            messages.error(request, 'Resume must be completed before generating cover letter.')
    
    # Get saved interview questions and answers from database
    interview_qa_list = InterviewQuestionAnswer.objects.filter(resume=resume).order_by('-created_at')
    
    # Convert markdown text to HTML for display
    job_description_html = None
    initial_resume_html = None
    tailored_resume_html = None
    
    if resume.job_description:
        # Unescape HTML entities and convert markdown to HTML
        job_description_html = markdown.markdown(
            html.unescape(resume.job_description),
            extensions=['fenced_code', 'tables', 'toc']
        )
    
    if resume.initial_resume_text:
        initial_resume_html = markdown.markdown(
            html.unescape(resume.initial_resume_text),
            extensions=['fenced_code', 'tables', 'toc']
        )
    
    if resume.tailored_resume_text:
        tailored_resume_html = markdown.markdown(
            html.unescape(resume.tailored_resume_text),
            extensions=['fenced_code', 'tables', 'toc']
        )
    
    # Convert interview Q&A answers to HTML
    for qa_item in interview_qa_list:
        qa_item.answer_html = markdown.markdown(
            html.unescape(qa_item.answer),
            extensions=['fenced_code', 'tables', 'toc']
        )
    
    context = {
        'resume': resume,
        'job_description_html': job_description_html,
        'initial_resume_html': initial_resume_html,
        'tailored_resume_html': tailored_resume_html,
        'interview_qa_list': interview_qa_list,
    }
    
    return render(request, 'resumes/detail.html', context)
