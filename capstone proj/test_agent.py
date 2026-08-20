"""
Run this AFTER starting the server (uvicorn main:app --reload) to sanity-check:
1. It answers correctly from KB
2. It refuses cleanly when info isn't in KB (no hallucination)
3. It redirects pricing questions instead of quoting a number
"""

import requests

BASE = "http://127.0.0.1:8000"

test_cases = [
    ("What services does QM Logics offer?", "should list the 6 services"),
    ("Where is QM Logics located?", "should mention Hasilpur Road, Bahawalpur"),
    ("How much does a website cost?", "should redirect to email, NOT give a number"),
    ("Do you guys build drones?", "should trigger fallback — not in KB, must refuse"),
    (
        "Who is the president of Pakistan?",
        "should trigger fallback — totally out of scope",
    ),
    (
        "Has QM Logics worked on any e-commerce projects?",
        "should mention portfolio e-commerce examples",
    ),
]

print("Running QM Agent test suite...\n" + "=" * 50)

for i, (question, expectation) in enumerate(test_cases, 1):
    resp = requests.post(
        f"{BASE}/chat", json={"message": question, "session_id": f"test_{i}"}
    )
    print(f"\n[{i}] Q: {question}")
    print(f"    Expected: {expectation}")
    print(f"    Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"    RAW ERROR RESPONSE: {resp.text}")
        continue
    reply = resp.json().get("reply", "ERROR")
    print(f"    A: {reply}")

print("\n" + "=" * 50)
print(
    "Manually verify: no hallucinated facts, pricing never stated as a number, fallback triggers on out-of-scope Qs."
)
