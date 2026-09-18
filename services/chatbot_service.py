import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini configure karo
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Model select karo
model = genai.GenerativeModel('gemini-3.6-flash')


def get_chatbot_response(user_message: str, user_role: str, user_name: str, school_id: int):
    """
    User ke message ka AI response generate karo.
    """

    system_prompt = f"""You are a helpful School ERP assistant.

User Info:
- Name: {user_name}
- Role: {user_role}
- School ID: {school_id}

Instructions:
1. Reply in the SAME language the user asks (Urdu, English, or Roman Urdu)
2. Be friendly and helpful
3. Keep answers short (2-4 lines usually)
4. Use emojis occasionally

Example questions:
- "Meri attendance kitni hai?"
- "Fees kaise bharni hai?"
- "School timing kya hai?"

If you don't know something, politely say so.
"""

    try:
        response = model.generate_content(
            f"{system_prompt}\n\nUser: {user_message}"
        )
        return response.text
    except Exception as e:
        return f"Sorry, AI service mein problem aa gayi: {str(e)}"