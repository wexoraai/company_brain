import asyncio
import httpx
import sys

# Define base URL for the server
BASE_URL = "http://localhost:8000"

# Target questions for verification
verification_cases = [
    {
        "id": 1,
        "question": "What advance did we pay for the Coorg resort?",
        "expected_keywords": ["15", "1,500,000", "lakhs", "coorg"],
        "expected_source": "La_Cavana_advance_receipt.pdf"
    },
    {
        "id": 2,
        "question": "Which lawyer handled this land?",
        "expected_keywords": ["ramesh", "associates"],
        "expected_source": "land_records.pdf"
    },
    {
        "id": 3,
        "question": "Show all pepper cultivation SOPs.",
        "expected_keywords": ["spacing", "3x3", "compost", "neem"],
        "expected_source": "pepper_cultivation_SOP.pdf"
    },
    {
        "id": 4,
        "question": "What did Zameer tell us about conversion?",
        "expected_keywords": ["approved", "conversion", "two weeks", "certificate"],
        "expected_source": "meeting_notes_2026_05.pdf"
    },
    {
        "id": 5,
        "question": "Which vendors supply drip irrigation?",
        "expected_keywords": ["netafim", "irrigation"],
        "expected_source": "vendor_master.xlsx"
    },
    {
        "id": 6,
        "question": "How many CRM leads came yesterday?",
        "expected_keywords": ["14", "leads", "crm"],
        "expected_source": "Zoho CRM API"
    },
    {
        "id": 7,
        "question": "Which vendors are pending payment?",
        "expected_keywords": ["netafim", "pending", "payables"],
        "expected_source": "Zoho Books API"
    }
]

async def verify_question(client: httpx.AsyncClient, case: dict) -> bool:
    print(f"\n[Case {case['id']}] Q: \"{case['question']}\"")
    try:
        response = await client.post(
            f"{BASE_URL}/api/search/ask",
            json={"question": case["question"]}
        )
        if response.status_code != 200:
            print(f"  [FAIL] Failed with status code {response.status_code}: {response.text}")
            return False

        data = response.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        q_type = data.get("type", "")

        print(f"  Type: {q_type.upper()}")
        print(f"  Answer: {answer}")
        print(f"  Sources: {sources}")

        # Validate sources
        source_matched = any(case["expected_source"].lower() in src.lower() for src in sources)
        if not source_matched:
            print(f"  [FAIL] Expected source '{case['expected_source']}' not found in sources: {sources}")
            return False

        # Validate keyword presence
        ans_lower = answer.lower()
        keyword_matches = [kw for kw in case["expected_keywords"] if kw.lower() in ans_lower]
        if not keyword_matches:
            print(f"  [FAIL] Expected keywords {case['expected_keywords']} not found in answer.")
            return False

        print(f"  [PASS] Case {case['id']} passed validation! Matched keywords: {keyword_matches}")
        return True
    except Exception as e:
        print(f"  [ERROR] Error during execution: {e}")
        return False

async def main():
    print("=== STARTING THE COMPANY BRAIN VERIFICATION SUITE ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check server health first
        try:
            health = await client.get(f"{BASE_URL}/")
            if health.status_code != 200:
                print(f"Server is running but returned status {health.status_code}. Ensure server is started.")
                sys.exit(1)
        except Exception:
            print("[FAIL] Cannot connect to the server. Please run the server in another terminal or start the docker container.")
            sys.exit(1)

        success = True
        for idx, case in enumerate(verification_cases):
            if idx > 0:
                print("  Waiting 20 seconds to respect Gemini API Free Tier rate limit...")
                await asyncio.sleep(20)
                
            res = await verify_question(client, case)
            if not res:
                success = False

        print("\n==========================================")
        if success:
            print("[SUCCESS] ALL VERIFICATION CASES PASSED SUCCESSFULLY!")
        else:
            print("[WARNING] SOME VERIFICATION CASES FAILED. Check details above.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
