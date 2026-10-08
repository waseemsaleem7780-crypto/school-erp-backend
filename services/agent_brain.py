"""
Agent Brain — Gemini LLM jo parent ke sawalon ka jawab deta hai.
Tools ko call karta hai, data laata hai, natural language jawab banata hai.
"""
import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

from services.agent_tools import (
    TOOLS_SCHEMA,
    TOOL_FUNCTIONS,
    get_guardian_by_phone,
    get_student_info,
    log_agent_interaction,
)

load_dotenv()

# ─── Gemini Setup ───
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-flash-latest"
FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash",
]

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


# ─── System Prompt ───
def build_system_prompt(student_info: dict) -> str:
    """Parent Agent ka persona + rules."""
    name = student_info.get("full_name", "Student")
    cls = student_info.get("class_name", "")
    sec = student_info.get("section_name", "")
    roll = student_info.get("roll_number", "")

    return f"""
Tum ek school ka Parent Support Agent ho. Tumhara naam "School Assistant" hai.

🎯 Tumhara kaam:
Parent ke sawalon ka jawab dena — koi bhi sawal ho, foran jawab do.

👤 Jis student ke baare mein sawal hai:
- Naam: {name}
- Class: {cls} ({sec})
- Roll Number: {roll}
- Student ID: {student_info.get('id')}

🤝 GREETING RULES (bahut zaroori):
Jab parent sirf greeting bheje (jaise "Assalam o Alaikum", "Salam", "Hello", "Hi", "AoA"), to:
1. Pehle "Wa Alaikum Assalam" se jawab do
2. Uske baad student ki poori info dikhao — Naam, Class, Section, Roll No
3. Phir poocho: "Aap kya maloomat chahte hain?" aur ye list do:
   - 📊 Attendance
   - 📝 Homework & Assignments
   - 🎯 Marks & Results
   - 💰 Fees
   - 📅 Timetable
   - 📢 Notices
   - 📚 Study Material

GREETING example:
"Wa Alaikum Assalam! 😊
Aap ke bache {name} (Class {cls}-{sec}, Roll No {roll}) ki info main de sakta hoon.
Aap kya jaanna chahte hain?
📊 Attendance
📝 Homework & Assignments
🎯 Marks & Results
💰 Fees
📅 Timetable
📢 Notices
Bas sawal bhejein!"

Agar parent greeting + sawal dono bheje (jaise "Assalam o Alaikum, attendance batao"):
- Pehle "Wa Alaikum Assalam" kahe
- Phir seedha jawab do

🤝 GREETING RULES (bahut zaroori):
Jab parent sirf greeting bheje (jaise "Assalam o Alaikum", "Salam", "Hello", "Hi", "AoA"), to:
1. Pehle "Wa Alaikum Assalam" ya "Wa Alaikumus Salam" se jawab do
2. Uske baad student ki poori info dikhao — Naam, Class, Section, Roll No
3. Phir poocho: "Aap kya maloomat chahte hain?" aur ye list do:
   - 📊 Attendance
   - 📝 Homework & Assignments
   - 🎯 Marks & Results
   - 💰 Fees
   - 📅 Timetable
   - 📢 Notices
   - 📚 Study Material

GREETING ka example jawab:
"Wa Alaikum Assalam! 😊
Aap ke bache {name} (Class {cls}-{sec}, Roll No {roll}) ki info main de sakta hoon.
Aap kya jaanna chahte hain?
📊 Attendance
📝 Homework & Assignments
🎯 Marks & Results
💰 Fees
📅 Timetable
📢 Notices
Bas sawal bhejein!"

Agar parent greeting ke saath sawal bhi pooche (jaise "Assalam o Alaikum, attendance batao"), to:
- Pehle "Wa Alaikum Assalam" kahe
- Phir seedha sawal ka jawab do

🤝 GREETING RULES (bahut zaroori):
Jab parent sirf greeting bheje (jaise "Assalam o Alaikum", "Salam", "Hello", "Hi", "AoA"), to:
1. Pehle "Wa Alaikum Assalam" ya "Wa Alaikumus Salam" se jawab do
2. Uske baad student ki poori info dikhao — Naam, Class, Section, Roll No
3. Phir poocho: "Aap kya maloomat chahte hain? Main in cheezon mein madad kar sakta hoon:" aur list do
   - 📊 Attendance
   - 📝 Homework & Assignments
   - 🎯 Marks & Results
   - 💰 Fees
   - 📅 Timetable
   - 📢 Notices
   - 📚 Study Material

GREETING ka example jawab:
"Wa Alaikum Assalam! 😊 
Aap ke bache *{name}* (Class {cls}-{sec}, Roll No {roll}) ki info main de sakta hoon. 
Aap kya jaanna chahte hain?
📊 Attendance
📝 Homework & Assignments  
🎯 Marks & Results
💰 Fees
📅 Timetable
📢 Notices
Bas sawal bhejein!"

Agar parent greeting ke saath sawal bhi pooche (jaise "Assalam o Alaikum, attendance batao"), to:
- Pehle "Wa Alaikum Assalam" kahe
- Phir seedha sawal ka jawab do

📋 Rules:
1. Hamesha Roman Urdu ya English mein jawab do (parent jis zubaan mein pooche, usi mein jawab do)
2. Pyaar se baat karo — "Ji", "Bhai", "Behen" jaise respectful words
3. Data tools se lao — khud se mat banao
4. Sirf is student ke baare mein jawab do (doosre students ka data kabhi na do)
5. CNIC, password, address, ya koi sensitive cheez kabhi na do
6. Medical advice kabhi na do — doctor ko bhejo
7. Agar data na mile, saaf batao: "Ye record mein nahi mila"
8. Agar confidence kam ho, bolo: "Main teacher se confirm karke batata hoon"
9. Reply chhota rakho — 3-5 lines max
10. Emoji ka istemal karo — friendly lagta hai 😊

🛠️ Available tools (in ko call karo jab data chahiye):
- get_student_info — student ki basic info
- get_attendance_recent — last N din ki attendance
- get_attendance_summary — attendance percentage
- get_attendance_by_date — ek din ki attendance
- get_marks — saare exam ke marks
- get_marks_by_subject — ek subject ke marks
- get_homework — recent homework
- get_assignments — recent assignments
- get_fee_payments — fee history
- get_timetable — class ka timetable
- get_notices — class ke notices
- get_exams — upcoming exams
- get_study_materials — study material list

⚠️ Tool call karte waqt sirf is student ke student_id/class_id use karo:
- student_id = {student_info.get('id')}
- class_id = {student_info.get('class_id')}
- section_id = {student_info.get('section_id')}
""".strip()


# ─── Tool Declaration for Gemini ───
def build_gemini_tools():
    """OpenAI-style TOOLS_SCHEMA ko Gemini format mein convert karo."""
    declarations = []
    for tool in TOOLS_SCHEMA:
        fn = tool["function"]
        declarations.append({
            "name": fn["name"],
            "description": fn["description"],
            "parameters": fn["parameters"],
        })
    return [{"function_declarations": declarations}]


# ─── Main Agent Loop ───
def ask_agent(parent_phone: str, question: str) -> dict:
    """
    Parent ke sawal ka jawab do.
    
    Returns:
        {
            "success": True/False,
            "answer": "jawab",
            "intent": "attendance/marks/...",
            "tools_used": ["get_attendance_summary"],
            "guardian_id": 1,
            "student_id": 5,
            "response_ms": 1200
        }
    """
    start_time = time.time()

    # 1. Guardian dhundo
    guardian = get_guardian_by_phone(parent_phone)
    if not guardian:
        return {
            "success": False,
            "answer": "Aap registered nahi hain. School office se rabta karein.",
            "guardian_id": None,
            "student_id": None,
            "intent": "unregistered",
            "tools_used": [],
            "response_ms": int((time.time() - start_time) * 1000),
        }

    student_id = guardian["student_id"]
    guardian_id = guardian["id"]

    # 2. Student info
    student_info = get_student_info(student_id)
    if not student_info:
        return {
            "success": False,
            "answer": "Student ka record nahi mila. School se rabta karein.",
            "guardian_id": guardian_id,
            "student_id": student_id,
            "intent": "no_student",
            "tools_used": [],
            "response_ms": int((time.time() - start_time) * 1000),
        }

    # 3. Gemini call with tools
    client = get_client()
    system_prompt = build_system_prompt(student_info)
    gemini_tools = build_gemini_tools()

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=question)]
        )
    ]

    tools_used = []
    intent = "unknown"
    final_answer = ""

    try:
        for iteration in range(5):  # max 5 tool loops
            response = None
            last_error = None
            for model_try in FALLBACK_MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_try,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            tools=gemini_tools,
                            temperature=0.3,
                            http_options=types.HttpOptions(timeout=30000),
                        ),
                    )
                    if model_try != MODEL_NAME:
                        print(f"Fallback model used: {model_try}")
                    break
                except Exception as e:
                    last_error = e
                    print(f"{model_try} failed: {str(e)[:80]}")
                    time.sleep(1)
                    continue

            if response is None:
                raise Exception(f"All models failed. Last error: {last_error}")

            # Check for tool calls
            tool_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(part.function_call)

            if not tool_calls:
                # No more tools → final answer
                final_answer = response.text or "Main samajh nahi paya, dobara poochain."
                break

            # Add model's response to contents
            contents.append(response.candidates[0].content)

            # Execute each tool call
            tool_response_parts = []
            for fc in tool_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                tools_used.append(tool_name)

                # Detect intent from first tool
                if intent == "unknown":
                    if "attendance" in tool_name:
                        intent = "attendance"
                    elif "marks" in tool_name:
                        intent = "marks"
                    elif "homework" in tool_name:
                        intent = "homework"
                    elif "assignment" in tool_name:
                        intent = "assignment"
                    elif "fee" in tool_name:
                        intent = "fees"
                    elif "timetable" in tool_name:
                        intent = "timetable"
                    elif "notice" in tool_name:
                        intent = "notices"
                    elif "exam" in tool_name:
                        intent = "exams"
                    elif "study_material" in tool_name:
                        intent = "study_material"
                    elif "student_info" in tool_name:
                        intent = "student_info"

                # Execute
                func = TOOL_FUNCTIONS.get(tool_name)
                if func:
                    try:
                        result = func(**tool_args)
                        # RealDictRow / list of RealDictRow ko JSON-safe banao
                        result = _to_json_safe(result)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result},
                    )
                )

            # Add tool responses back
            contents.append(
                types.Content(role="user", parts=tool_response_parts)
            )

        if not final_answer:
            final_answer = "Main abhi jawab nahi de saka, dobara koshish karein."

    except Exception as e:
        final_answer = f"Error: {str(e)}"
        print(f"❌ Agent error: {e}")

    response_ms = int((time.time() - start_time) * 1000)

    # 4. Log
    try:
        log_agent_interaction(
            guardian_id=guardian_id,
            student_id=student_id,
            question=question,
            answer=final_answer,
            intent=intent,
            tools_used=",".join(tools_used),
            response_ms=response_ms,
        )
    except Exception as e:
        print(f"Log failed: {e}")

    return {
        "success": True,
        "answer": final_answer,
        "intent": intent,
        "tools_used": tools_used,
        "guardian_id": guardian_id,
        "student_id": student_id,
        "response_ms": response_ms,
    }


def _to_json_safe(obj):
    """RealDictRow / datetime / date / time / timedelta / Decimal ko JSON-safe banao."""
    from datetime import date, datetime, time, timedelta
    from decimal import Decimal

    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(x) for x in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.strftime("%H:%M")
    if isinstance(obj, timedelta):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="ignore")
    return obj

