import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ResumeAIService:
    """
    Service for interacting with OpenAI API to tailor resumes
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')  # Default to GPT-4o (latest and best)
    
    def tailor_resume(self, initial_resume, job_description, custom_prompt=None):
        """
        Tailor a resume based on job description using OpenAI
        
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
            
            # Prepare the messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            # Prepare API parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            
            # Use correct token parameter based on model
            # Newer models (gpt-4.5+, o1, o3, etc.) use max_completion_tokens
            # Older models (gpt-4, gpt-4o, gpt-3.5-turbo) use max_tokens
            if any(x in self.model.lower() for x in ['gpt-4.5', 'gpt-5', 'o1', 'o3']):
                api_params['max_completion_tokens'] = 4096
            else:
                api_params['max_tokens'] = 4096
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)
            
            # Extract the tailored resume
            tailored_resume = response.choices[0].message.content
            return tailored_resume
            
        except Exception as e:
            # Improve common OpenAI errors into user-friendly messages
            message = str(e)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                response = getattr(e, "response", None)
                status_code = getattr(response, "status_code", None)

            # Region restriction (most common for new users)
            if status_code == 403 and "unsupported_country_region_territory" in message:
                raise Exception(
                    "OpenAI blocked this request because your country/region/territory is not supported. "
                    "Try disabling VPN (if it routes through a restricted region) or switching VPN to a supported region, "
                    "or use a different AI provider."
                )

            # Auth errors
            if status_code in (401, 403) and ("invalid_api_key" in message or "Incorrect API key" in message):
                raise Exception(
                    "OpenAI authentication failed. Please verify your `OPENAI_API_KEY` in `.env` and restart the server."
                )

            raise Exception(f"OpenAI API error: {message}")

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

            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            # Prepare API parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            
            # Use correct token parameter based on model
            if any(x in self.model.lower() for x in ['gpt-4.5', 'gpt-5', 'o1', 'o3']):
                api_params['max_completion_tokens'] = 200  # Shorter response for questions
            else:
                api_params['max_tokens'] = 200

            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            # Same error handling as tailor_resume method
            message = str(e)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                response = getattr(e, "response", None)
                status_code = getattr(response, "status_code", None)

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

            raise Exception(f"OpenAI API error: {message}")
    
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

            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            # Prepare API parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            
            # Use correct token parameter based on model
            if any(x in self.model.lower() for x in ['gpt-4.5', 'gpt-5', 'o1', 'o3']):
                api_params['max_completion_tokens'] = 300  # Slightly longer for cover letters
            else:
                api_params['max_tokens'] = 300

            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            # Same error handling as other methods
            message = str(e)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                response = getattr(e, "response", None)
                status_code = getattr(response, "status_code", None)

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

            raise Exception(f"OpenAI API error: {message}")
