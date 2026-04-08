import os
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ResumeAIService:
    """
    Service for interacting with AI APIs (OpenAI or Anthropic) to tailor resumes
    """
    
    def __init__(self):
        # Determine which AI provider to use
        self.provider = os.getenv('AI_PROVIDER', 'openai').lower()
        
        if self.provider == 'anthropic':
            self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            self.model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4')
        else:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    def tailor_resume(self, initial_resume, job_description, custom_prompt=None):
        """
        Tailor a resume based on job description using AI (OpenAI or Anthropic)
        
        Args:
            initial_resume (str): The original resume text
            job_description (str): The job description to tailor for
            custom_prompt (str, optional): Custom system prompt from user
        
        Returns:
            str: The tailored resume text
        
        Raises:
            Exception: If the API call fails
        """
        try:
            # Use custom prompt if provided, otherwise use default
            system_prompt = custom_prompt if custom_prompt else self._get_default_prompt()
            
            # Build the user message content
            user_content = f"""Initial Resume:
{initial_resume}

Job Description:
{job_description}

Please tailor this resume for the job description provided."""
            
            if self.provider == 'anthropic':
                # Anthropic API call
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7
                )
                return response.content[0].text
            else:
                # OpenAI API call
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
                
                api_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                
                # Use correct token parameter based on model
                if any(x in self.model.lower() for x in ['gpt-4.5', 'gpt-5', 'o1', 'o3']):
                    api_params['max_completion_tokens'] = 4096
                else:
                    api_params['max_tokens'] = 4096
                
                response = self.client.chat.completions.create(**api_params)
                return response.choices[0].message.content
            
        except Exception as e:
            # Handle API errors
            message = str(e)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                response_obj = getattr(e, "response", None)
                status_code = getattr(response_obj, "status_code", None)

            # Anthropic-specific errors
            if self.provider == 'anthropic':
                if status_code in (401, 403):
                    raise Exception(
                        f"{self.provider.upper()} authentication failed. Please verify your `ANTHROPIC_API_KEY` in `.env` and restart the server."
                    )
                raise Exception(f"Anthropic API error: {message}")
            
            # OpenAI-specific errors
            if status_code == 403 and "unsupported_country_region_territory" in message:
                raise Exception(
                    "OpenAI blocked this request because your country/region/territory is not supported. "
                    "Try disabling VPN (if it routes through a restricted region) or switching VPN to a supported region, "
                    "or use a different AI provider."
                )

            if status_code in (401, 403) and ("invalid_api_key" in message or "Incorrect API key" in message):
                raise Exception(
                    "OpenAI authentication failed. Please verify your `OPENAI_API_KEY` in `.env` and restart the server."
                )

            raise Exception(f"{self.provider.upper()} API error: {message}")

    def generate_question_answer(self, job_description, tailored_resume, question):
        """
        Generate an answer to a recruiter question based on job description and tailored resume
        """
        try:
            # System prompt for question answering
            system_prompt = """You are an expert job interview coach helping candidates answer recruiter questions.

Your task is to generate concise, professional answers based on the provided job description and resume.

Guidelines:
- Provide 1-2 sentences maximum
- Use a casual, concise, oral tone (as if speaking in an interview)
- Make really important words **bold** using markdown
- Use line breaks for better readability
- Base your answer on the specific job requirements and candidate's experience
- Be confident but not arrogant
- Focus on relevant skills and achievements from the resume"""

            # User content with job description, resume, and question
            user_content = f"""Here is the job description:
{job_description}

Here is my resume:
{tailored_resume}

Recruiter is asking:
{question}

Please provide 1-2 sentences with casual, concise, oral tone (Make really important words bold and use line breaks)"""

            if self.provider == 'anthropic':
                # Anthropic API call
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7
                )
                return response.content[0].text.strip()
            else:
                # OpenAI API call
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]

                api_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                
                if any(x in self.model.lower() for x in ['gpt-4.5', 'gpt-5', 'o1', 'o3']):
                    api_params['max_completion_tokens'] = 200
                else:
                    api_params['max_tokens'] = 200

                response = self.client.chat.completions.create(**api_params)
                return response.choices[0].message.content.strip()

        except Exception as e:
            # Handle API errors
            message = str(e)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                response_obj = getattr(e, "response", None)
                status_code = getattr(response_obj, "status_code", None)

            if self.provider == 'anthropic':
                if status_code in (401, 403):
                    raise Exception(
                        "Anthropic authentication failed. Please verify your `ANTHROPIC_API_KEY` in `.env` and restart the server."
                    )
                raise Exception(f"Anthropic API error: {message}")

            if status_code == 403 and "unsupported_country_region_territory" in message:
                raise Exception(
                    "OpenAI blocked this request because your country/region/territory is not supported. "
                    "Try disabling VPN (if it routes through a restricted region) or switching VPN to a supported region, "
                    "or use a different AI provider."
                )

            if status_code in (401, 403) and ("invalid_api_key" in message or "Incorrect API key" in message):
                raise Exception(
                    "OpenAI authentication failed. Please verify your `OPENAI_API_KEY` in `.env` and restart the server."
                )

            raise Exception(f"{self.provider.upper()} API error: {message}")
    
    def _get_default_prompt(self):
        """
        Get the built-in system prompt for resume tailoring
        """
        return """@base resume.md This is my sample resume
@jd.md is job description.
update this resume which align with jd even tech stack.
we should change tech stack (you should change content (language, framework, cloud platform...) which related with main tech stack in base resume to things (language, framework, cloud platform...) which related with job description's tech stacks )

Output requirements:
- Return ONLY the updated resume in Markdown.
- Keep it professional and ATS-friendly.
- Keep company names, titles, and dates as-is, but update wording/bullets to better match the JD.
- When the base resume mentions technologies that don't match the JD, replace them with the closest JD-related alternatives and adjust the bullet content accordingly (language, frameworks, cloud platform, tooling)."""

    def generate_cover_letter(self, job_description, tailored_resume, company_name):
        """
        Generate a cover letter based on job description and tailored resume
        """
        try:
            # System prompt for cover letter generation
            system_prompt = """You are an expert cover letter writer helping candidates create compelling cover letters.

Your task is to generate a professional cover letter based on the provided job description and resume.

Guidelines:
- Provide 5-6 sentences maximum
- Use a casual, concise, oral tone (as if speaking to the hiring manager)
- Make really important words **bold** using markdown
- Use line breaks for better readability
- Focus on relevant skills and achievements from the resume
- Show enthusiasm for the specific company and role
- Be confident but not arrogant
- Connect candidate's experience to job requirements"""

            # User content with job description, resume, and company
            user_content = f"""Here is the job description:
{job_description}

Here is my resume:
{tailored_resume}

Company name: {company_name}

Please provide 5-6 sentences with casual, concise, oral tone (Make really important words bold and use line breaks)"""

            if self.provider == 'anthropic':
                # Anthropic API call
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7
                )
                return response.content[0].text.strip()
            else:
                # OpenAI API call
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]

                api_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                
                if any(x in self.model.lower() for x in ['gpt-4.5', 'gpt-5', 'o1', 'o3']):
                    api_params['max_completion_tokens'] = 300
                else:
                    api_params['max_tokens'] = 300

                response = self.client.chat.completions.create(**api_params)
                return response.choices[0].message.content.strip()

        except Exception as e:
            # Handle API errors
            message = str(e)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                response_obj = getattr(e, "response", None)
                status_code = getattr(response_obj, "status_code", None)

            if self.provider == 'anthropic':
                if status_code in (401, 403):
                    raise Exception(
                        "Anthropic authentication failed. Please verify your `ANTHROPIC_API_KEY` in `.env` and restart the server."
                    )
                raise Exception(f"Anthropic API error: {message}")

            if status_code == 403 and "unsupported_country_region_territory" in message:
                raise Exception(
                    "OpenAI blocked this request because your country/region/territory is not supported. "
                    "Try disabling VPN (if it routes through a restricted region) or switching VPN to a supported region, "
                    "or use a different AI provider."
                )

            if status_code in (401, 403) and ("invalid_api_key" in message or "Incorrect API key" in message):
                raise Exception(
                    "OpenAI authentication failed. Please verify your `OPENAI_API_KEY` in `.env` and restart the server."
                )

            raise Exception(f"{self.provider.upper()} API error: {message}")
