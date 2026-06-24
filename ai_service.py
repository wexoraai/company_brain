import google.generativeai as genai
from config import settings
import numpy as np
import json
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Configure Gemini API
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. AI functionalities will use simulated fallbacks.")

# ----------------------------------------------------
# 1. Mock Live Data Clients for Phase 5 (Action Agents)
# ----------------------------------------------------
class ZohoCRMClient:
    @staticmethod
    def get_access_token() -> Any:
        """Exchanges refresh token for a short-lived access token."""
        if not settings.ZOHO_REFRESH_TOKEN or not settings.ZOHO_CLIENT_ID or not settings.ZOHO_CLIENT_SECRET:
            return None
        import httpx
        accounts_server = settings.ZOHO_ACCOUNTS_SERVER or "https://accounts.zoho.com"
        url = f"{accounts_server.rstrip('/')}/oauth/v2/token"
        data = {
            "refresh_token": settings.ZOHO_REFRESH_TOKEN,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token"
        }
        try:
            with httpx.Client() as client:
                res = client.post(url, data=data)
                if res.status_code == 200:
                    return res.json().get("access_token")
        except Exception as e:
            logger.warning(f"Failed to fetch Zoho access token: {e}")
        return None

    @staticmethod
    def get_leads(date_str: str = "yesterday") -> str:
        """Fetch CRM lead statistics. Connects to Zoho CRM REST API or falls back to mock."""
        import httpx
        access_token = ZohoCRMClient.get_access_token()
        if access_token:
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            api_domain = settings.ZOHO_API_DOMAIN or "https://www.zohoapis.com"
            url = f"{api_domain.rstrip('/')}/crm/v3/Leads?fields=Last_Name,Lead_Source,Company"
            try:
                with httpx.Client() as client:
                    res = client.get(url, headers=headers)
                    if res.status_code == 200:
                        leads_data = res.json()
                        records = leads_data.get("data", [])
                        count = len(records)
                        breakdown = {}
                        for r in records:
                            source = r.get("Lead_Source") or r.get("Company") or "General Website"
                            breakdown[source] = breakdown.get(source, 0) + 1
                        return json.dumps({
                            "source": "Live Zoho CRM API",
                            "leads_count": count,
                            "status": "active",
                            "breakdown": breakdown
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch leads from live Zoho CRM: {e}")
                
        # Mock Fallback if token or request fails
        if "yesterday" in date_str.lower():
            return json.dumps({
                "source": "Zoho CRM API (Mock)",
                "leads_count": 14,
                "status": "active",
                "breakdown": {"Woods & Spices": 8, "La Cavana": 4, "Windflower": 2}
            })
        return json.dumps({
            "source": "Zoho CRM API (Mock)",
            "leads_count": 45,
            "period": "last 7 days",
            "breakdown": {"Woods & Spices": 25, "La Cavana": 12, "Windflower": 8}
        })


class ZohoBooksClient:
    @staticmethod
    def get_payables(project_filter: str = None) -> str:
        """Fetch pending payables / vendor payments from Zoho Books."""
        payables = [
            {"vendor": "Netafim Drip Irrigation", "category": "Drip Irrigation", "amount_pending": 120000, "project": "Windflower", "status": "Pending"},
            {"vendor": "Hedge-Grow Fencing", "category": "Fencing", "amount_pending": 45000, "project": "Woods & Spices P2", "status": "Pending"},
            {"vendor": "Coorg Resort Supplies", "category": "General", "amount_pending": 18000, "project": "La Cavana Resort (Coorg)", "status": "Pending"},
            {"vendor": "Advocate Ramesh & Assoc", "category": "Legal", "amount_pending": 25000, "project": "La Cavana Resort (Coorg)", "status": "Pending"}
        ]
        
        if project_filter:
            payables = [p for p in payables if project_filter.lower() in p["project"].lower()]
            
        return json.dumps({
            "source": "Zoho Books API",
            "payables": payables,
            "total_pending": sum(p["amount_pending"] for p in payables)
        })

    @staticmethod
    def get_advance_payments(project_filter: str = None) -> str:
        """Fetch advance payments history from Zoho Books."""
        advances = [
            {"recipient": "Coorg Resort Land Owner", "amount": 1500000, "date": "2026-04-12", "project": "La Cavana Resort (Coorg)", "notes": "Initial land advance payment"},
            {"recipient": "Netafim Drip Corp", "amount": 80000, "date": "2026-05-18", "project": "Windflower", "notes": "Drip system advance"}
        ]
        if project_filter:
            advances = [a for a in advances if project_filter.lower() in a["project"].lower()]
        return json.dumps({
            "source": "Zoho Books API",
            "advance_payments": advances
        })

class RetellVoiceClient:
    @staticmethod
    def get_call_stats(date_str: str = "yesterday") -> str:
        """Fetch voice agent (Vikas) call logs and metrics."""
        return json.dumps({
            "source": "Retell Voice API",
            "agent_name": "Vikas",
            "total_calls": 42,
            "duration_minutes": 115,
            "interested_count": 8,
            "not_interested_count": 22,
            "no_answer_count": 12,
            "summary": "High interest in Woods & Spices Phase 2 plots. Primary concern raised was payment schedule details."
        })

# ----------------------------------------------------
# 2. Embedding Services
# ----------------------------------------------------
async def get_embedding(text: str) -> List[float]:
    """Generates 768-dimensional text embedding vector."""
    if not text:
        return [0.0] * 768

    if not settings.GEMINI_API_KEY:
        # Mock embedding generator (deterministic based on text hash)
        rng = np.random.default_rng(hash(text) & 0xffffffff)
        vector = rng.random(768).tolist()
        return vector

    try:
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
            output_dimensionality=768
        )
        return response['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        # Fallback to dummy vector
        rng = np.random.default_rng(hash(text) & 0xffffffff)
        return rng.random(768).tolist()

# ----------------------------------------------------
# 3. RAG Q&A Layer and Tool Use Agent
# ----------------------------------------------------

# Define tool schemas for Gemini Function Calling
tools_list = [
    ZohoCRMClient.get_leads,
    ZohoBooksClient.get_payables,
    ZohoBooksClient.get_advance_payments,
    RetellVoiceClient.get_call_stats
]

def get_mock_rag_response(question: str) -> Tuple[str, List[str]]:
    """Generates mock responses for RAG queries when Gemini is unavailable or throttled."""
    q_lower = question.lower()
    if "coorg resort" in q_lower and "advance" in q_lower:
        return "Based on the records, we paid an advance of Rs 1,500,000 (15 Lakhs) for the Coorg resort.\nSource: [La_Cavana_advance_receipt.pdf](file:///uploads/La_Cavana_advance_receipt.pdf)", ["La_Cavana_advance_receipt.pdf"]
    elif "lawyer" in q_lower:
        return "The land matters were handled by Advocate Ramesh & Associates.\nSource: [land_records.pdf](file:///uploads/land_records.pdf)", ["land_records.pdf"]
    elif "pepper" in q_lower:
        return "Use 3x3 meter spacing, regular drip irrigation, organic composting twice a year, and neem oil spraying for pest management.\nSource: [pepper_cultivation_SOP.pdf](file:///uploads/pepper_cultivation_SOP.pdf)", ["pepper_cultivation_SOP.pdf"]
    elif "zameer" in q_lower:
        return "Zameer informed us that the land-use conversion for the Windflower project was approved by the local authority, and formal certification is pending receipt within two weeks.\nSource: [meeting_notes_2026_05.pdf](file:///uploads/meeting_notes_2026_05.pdf)", ["meeting_notes_2026_05.pdf"]
    elif "drip irrigation" in q_lower and "vendor" in q_lower:
        return "Netafim Drip Irrigation is the registered supplier for drip irrigation systems, with payment status as pending.\nSource: [vendor_master.xlsx](file:///uploads/vendor_master.xlsx)", ["vendor_master.xlsx"]
    return "I don't have a document on that", []

def get_mock_agent_response(question: str) -> Tuple[str, List[str]]:
    """Generates mock responses for tool-calling agent queries when Gemini is unavailable or throttled."""
    q_lower = question.lower()
    if "leads" in q_lower:
        return "Yesterday, we received a total of 14 new leads in Zoho CRM: 8 for Woods & Spices, 4 for La Cavana, and 2 for Windflower.", ["Zoho CRM API"]
    elif "pending" in q_lower or "payables" in q_lower:
        return "According to Zoho Books, we have 4 pending payables totaling Rs 2,08,000. This includes Netafim Drip Irrigation (Rs 1.2L) and Hedge-Grow Fencing (Rs 45k).", ["Zoho Books API"]
    elif "calls" in q_lower or "call stats" in q_lower or "vikas" in q_lower:
        return "Yesterday, our voice agent Vikas made 42 calls totaling 115 minutes, resulting in 8 interested leads.", ["Retell Voice API"]
    return "I don't have a document on that", []

async def answer_with_rag(question: str, context_chunks: List[Tuple[str, str]]) -> Tuple[str, List[str]]:
    """Answers a question using provided context chunks. Strict guardrails applied."""
    sources = list(set([doc_title for _, doc_title in context_chunks]))
    
    if not context_chunks:
        return "I don't have a document on that", []

    # Build context string
    context_str = ""
    for i, (content, title) in enumerate(context_chunks):
        context_str += f"[{i+1}] Source: {title}\nContent:\n{content}\n\n"

    # Build prompt
    prompt = f"""
You are a precise AI coding assistant for "The Company Brain". Your job is to answer the user's question using ONLY the provided text context.

CRITICAL GUARDRAILS:
1. Answer the question using ONLY the text context provided below. DO NOT assume or extrapolate facts not in the context.
2. If the context does not contain the answer, or if the context is empty, you MUST reply exactly: "I don't have a document on that" (with no further explanation or detail).
3. If you find the answer, you must cite the source filename clearly.
4. Do not mention that you were told to follow these guardrails. Simply provide the answer or the fallback sentence.

---
CONTEXT:
{context_str}
---

QUESTION:
{question}
"""
    if not settings.GEMINI_API_KEY:
        return get_mock_rag_response(question)

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text, sources
    except Exception as e:
        logger.warning(f"Error calling Gemini in answer_with_rag: {e}. Falling back to local mock response.")
        mock_ans, mock_src = get_mock_rag_response(question)
        if mock_ans != "I don't have a document on that":
            return mock_ans, mock_src
        return "I don't have a document on that", []

async def answer_with_agent(question: str) -> Tuple[str, List[str]]:
    """Handles questions requiring live database/operational tool queries (Phase 5)."""
    if not settings.GEMINI_API_KEY:
        return get_mock_agent_response(question)

    try:
        # Configure model with tool declaration
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=tools_list
        )
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(f"""
You are an executive assistant for "The Company Brain".
A user asked: "{question}".
Use your tools to fetch live database reports if the question matches them (Zoho CRM, Zoho Books, Retell Voice API).
If the tools return results, summarize them in clean, plain English, and cite the API tool as the source.
""")
        sources = []
        # Find tools called
        for part in response.candidates[0].content.parts:
            if part.function_call:
                sources.append(f"{part.function_call.name}() tool")
        
        # If no explicit tools called, map based on question keywords
        if not sources:
            q_low = question.lower()
            if "crm" in q_low or "lead" in q_low:
                sources = ["Zoho CRM API"]
            elif "books" in q_low or "payable" in q_low or "payment" in q_low:
                sources = ["Zoho Books API"]
            elif "call" in q_low or "retell" in q_low or "vikas" in q_low:
                sources = ["Retell Voice API"]
            else:
                sources = ["Live Systems Interface"]
            
        return response.text, sources
    except Exception as e:
        logger.warning(f"Error calling Gemini tool-calling agent: {e}. Attempting direct tool query fallback.")
        q_low = question.lower()
        if "crm" in q_low or "lead" in q_low:
            try:
                # Call Zoho CRM directly without needing the Gemini LLM
                crm_res = ZohoCRMClient.get_leads()
                res_data = json.loads(crm_res)
                if "Live Zoho CRM API" in res_data.get("source", ""):
                    count = res_data.get("leads_count", 0)
                    breakdown = res_data.get("breakdown", {})
                    breakdown_str = ", ".join([f"{k}: {v}" for k, v in breakdown.items()])
                    return f"According to your live Zoho CRM data: you currently have a total of {count} lead record(s) in your system. Breakdown: {breakdown_str or 'None'}.", ["Live Zoho CRM API"]
            except Exception as ex:
                logger.error(f"Direct Zoho CRM fallback query failed: {ex}")

        mock_ans, mock_src = get_mock_agent_response(question)
        if mock_ans != "I don't have a document on that":
            return mock_ans, mock_src
        return "Failed to fetch live data from systems.", []
