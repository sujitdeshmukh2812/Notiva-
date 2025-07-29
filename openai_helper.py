import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Get API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

def check_openai_config():
    """Check if OpenAI is properly configured"""
    return bool(openai.api_key)

def answer_subject_doubt(question, subject_name=None):
    """
    Use GPT-3.5-turbo to answer subject-related doubts
    """
    if not check_openai_config():
        return "OpenAI API is not configured. Please contact the administrator."
        
    try:
        system_message = "You are a helpful educational assistant. Answer student questions clearly and concisely. "
        if subject_name:
            system_message += f"Focus on {subject_name} related concepts."
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message["content"]
        
    except Exception as e:
        return f"I'm sorry, I couldn't process your question right now. Please try again later."

def generate_document_summary(document_title, document_description=None):
    """
    Generate a brief summary for a document based on its title and description
    """
    if not check_openai_config():
        return "Auto-summary unavailable - OpenAI not configured"
        
    try:
        content = f"Document Title: {document_title}"
        if document_description:
            content += f"\nDescription: {document_description}"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that creates brief summaries for academic documents. Provide a concise 1-2 sentence summary based on the title and description provided."
                },
                {"role": "user", "content": content}
            ],
            max_tokens=100,
            temperature=0.5
        )
        
        return response.choices[0].message["content"]
        
    except Exception as e:
        return "Auto-summary unavailable"