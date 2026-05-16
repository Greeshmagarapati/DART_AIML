
"""Offline response engine for the FSSAI DART chatbot.

This module keeps the chatbot fully usable without any network calls.
It works with the 44-test dataset shipped in the app and supports:
- direct test lookup by test number, id, name, adulterant, or keywords
- category summaries
- procedure / result / health-risk / reporting questions
- a simple analyzer for the Test Detail page

The logic is intentionally rule-based and dependency-light for easy deployment.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "dart_knowledge.json"

GENERAL_CONTACTS = (
    "📞 FSSAI contacts:\n"
    "• Toll-Free: 1800-11-2100\n"
    "• WhatsApp: 98 6868 6868\n"
    "• Email: compliance@fssai.gov.in\n"
    "• Website: www.fssai.gov.in"
)

DEFAULT_RESPONSE = {
    "result": "🧠 I can help with DART tests, health risks, and reporting.",
    "explanation": (
        "Ask me about any food test by name, test number, adulterant, category, "
        "procedure, pure result, adulterated result, health risk, or how to report to FSSAI."
    ),
    "risk_level": "Info",
    "mode": "offline",
}

GENERAL_RESPONSES = [
    ("fssai contact", GENERAL_CONTACTS),
    ("how to report", GENERAL_CONTACTS),
    ("report", GENERAL_CONTACTS),
    ("contact", GENERAL_CONTACTS),
    ("what is dart", (
        "🧪 DART means Detect Adulteration with Rapid Test. "
        "It helps people check common food adulteration using simple home-based methods."
    )),
    ("dart", (
        "🧪 DART means Detect Adulteration with Rapid Test. "
        "It is an offline, household-friendly food safety guide that explains simple checks for common adulterants."
    )),
    ("fssai", (
        "FSSAI is the Food Safety and Standards Authority of India. "
        "It publishes food safety guidance, including the DART booklet and consumer awareness material."
    )),
    ("most dangerous", (
        "🚨 Some of the most serious adulterations are lead chromate in turmeric, argemone seeds in mustard, "
        "TOCP in oils, malachite green in vegetables, and rhodamine B in ragi or sweet potato."
    )),
]

CATEGORY_ALIASES = {
    "milk": "milk-dairy",
    "milk and dairy": "milk-dairy",
    "dairy": "milk-dairy",
    "oil": "oils-fats",
    "oils": "oils-fats",
    "fats": "oils-fats",
    "sugar": "sweets-sugar",
    "sweet": "sweets-sugar",
    "sweets": "sweets-sugar",
    "cereal": "cereals-pulses",
    "cereals": "cereals-pulses",
    "pulses": "cereals-pulses",
    "grain": "cereals-pulses",
    "spice": "spices",
    "spices": "spices",
    "vegetable": "vegetables-fruits",
    "vegetables": "vegetables-fruits",
    "fruit": "vegetables-fruits",
    "fruits": "vegetables-fruits",
    "beverage": "beverages",
    "beverages": "beverages",
    "coffee": "beverages",
    "tea": "beverages",
}

INTENT_HINTS = {
    "procedure": ["how to", "steps", "procedure", "test method", "method", "perform", "do the test", "how do i test"],
    "results": ["pure result", "adulterated result", "what will happen", "expected result", "difference", "outcome"],
    "health": ["health", "risk", "effect", "danger", "harm", "toxic", "symptom", "safe"],
    "summary": ["about", "what is", "explain", "tell me", "details", "describe"],
    "list": ["all tests", "list tests", "show tests", "how many tests", "full list", "every test"],
    "contact": ["report", "complaint", "contact", "helpline", "whatsapp", "email"],
}

@lru_cache(maxsize=1)
def load_data() -> Dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_data() -> Dict[str, Any]:
    return load_data()


def flatten_tests() -> List[Dict[str, Any]]:
    data = get_data()
    flat: List[Dict[str, Any]] = []
    for category in data["categories"]:
        for test in data["tests"].get(category["id"], []):
            item = dict(test)
            item["category_id"] = category["id"]
            item["category_name"] = category["name"]
            flat.append(item)
    return flat


ALL_TESTS = flatten_tests()
TEST_BY_ID = {t["id"]: t for t in ALL_TESTS}
TEST_BY_NUMBER = {int(t["testNo"]): t for t in ALL_TESTS}
CATEGORY_BY_ID = {c["id"]: c for c in get_data()["categories"]}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()

def tokenize(text: str) -> List[str]:
    return [t for t in norm(text).split() if t]

def fuzzy_phrase_match(phrase: str, text: str) -> bool:
    phrase_tokens = [t for t in tokenize(phrase) if len(t) > 2]
    text_tokens = tokenize(text)
    if not phrase_tokens or not text_tokens:
        return False

    matched = 0
    for p_tok in phrase_tokens:
        prefix = p_tok[:5]
        if any(t == p_tok or t.startswith(prefix) or prefix.startswith(t[:4]) for t in text_tokens):
            matched += 1

    # One-word phrases need an exact/fuzzy hit; multi-word phrases need most meaningful words.
    if len(phrase_tokens) == 1:
        return matched == 1
    return matched >= max(2, len(phrase_tokens) - 1)


def find_intent(message: str) -> str:
    msg = norm(message)
    for intent, hints in INTENT_HINTS.items():
        if any(h in msg for h in hints):
            return intent
    if "pure" in msg or "adulterated" in msg:
        return "results"
    return "summary"


def detect_category(message: str) -> Optional[str]:
    msg = norm(message)
    for alias, category_id in CATEGORY_ALIASES.items():
        if alias in msg:
            return category_id
    return None


def score_test(test: Dict[str, Any], message: str) -> int:
    msg = norm(message)
    score = 0

    if test["id"] in msg:
        score += 120

    if re.search(rf"\btest\s*{re.escape(str(test['testNo']))}\b", msg) or msg == str(test["testNo"]):
        score += 100
    if re.search(rf"\b{re.escape(str(test['testNo']))}\b", msg):
        score += 25

    name = norm(test["name"])
    adulterant = norm(test.get("adulterant", ""))
    category_name = norm(test.get("category_name", ""))

    if name and name in msg:
        score += 90
    elif all(token in msg for token in name.split()[:3] if token not in {"of", "in", "the"}):
        score += 35

    if adulterant and adulterant in msg:
        score += 45

    if category_name and category_name in msg:
        score += 15

    for keyword in test.get("keywords", []):
        kw = norm(keyword)
        if kw and kw in msg:
            score += 20

    for token in (test["name"], test.get("adulterant", "")):
        for word in norm(token).split():
            if len(word) > 3 and word in msg:
                score += 4

    return score


def find_best_test(message: str) -> Optional[Dict[str, Any]]:
    candidates = [(score_test(test, message), test) for test in ALL_TESTS]
    candidates.sort(key=lambda x: (x[0], -x[1]["testNo"]), reverse=True)
    best_score, best_test = candidates[0]
    if best_score < 20:
        return None
    return best_test


def list_tests_for_category(category_id: str) -> str:
    category = CATEGORY_BY_ID.get(category_id)
    if not category:
        return ""
    items = [t for t in ALL_TESTS if t["category_id"] == category_id]
    lines = [
        f"🗂️ {category['name']} — {len(items)} tests",
        category.get("description", ""),
        "",
    ]
    for t in items:
        lines.append(f"• Test {t['testNo']}: {t['name']} — detects {t.get('adulterant', 'adulterant')}")
    return "\n".join([line for line in lines if line])


def summarize_test(test: Dict[str, Any]) -> str:
    return (
        f"Test {test['testNo']}: {test['name']}.\n"
        f"Detects: {test.get('adulterant', 'unknown adulterant')}.\n"
        f"Pure result: {test.get('pureResult', 'Not provided')}.\n"
        f"Adulterated result: {test.get('adulteratedResult', 'Not provided')}.\n"
        f"Health risk: {test.get('healthRisk', 'Not provided')}."
    )


def answer_for_test(test: Dict[str, Any], message: str) -> Dict[str, Any]:
    intent = find_intent(message)
    category = test.get("category_name", "Unknown category")
    intro = f"🧪 Test {test['testNo']} — {test['name']} ({category})"

    if intent == "procedure":
        procedure = "\n".join(f"{i+1}. {step}" for i, step in enumerate(test.get("procedure", [])))
        response = f"{intro}\n\nProcedure:\n{procedure}"
    elif intent == "results":
        response = (
            f"{intro}\n\n"
            f"Pure result: {test.get('pureResult', 'Not provided')}\n"
            f"Adulterated result: {test.get('adulteratedResult', 'Not provided')}"
        )
    elif intent == "health":
        response = (
            f"{intro}\n\n"
            f"Risk level: {test.get('riskLevel', 'Unknown')}\n"
            f"Health risk: {test.get('healthRisk', 'Not provided')}"
        )
    else:
        response = (
            f"{intro}\n\n"
            f"Detects: {test.get('adulterant', 'unknown adulterant')}\n"
            f"Pure result: {test.get('pureResult', 'Not provided')}\n"
            f"Adulterated result: {test.get('adulteratedResult', 'Not provided')}\n"
            f"Health risk: {test.get('healthRisk', 'Not provided')}\n"
            f"Risk level: {test.get('riskLevel', 'Unknown')}"
        )

    keywords = test.get("keywords", [])
    if keywords:
        response += "\n\nCommon clues: " + ", ".join(keywords[:5])

    return {
        "response": response,
        "mode": "offline",
        "test_id": test["id"],
        "test_no": test["testNo"],
        "category": category,
        "full": test,
    }


def answer_general(message: str) -> Optional[Dict[str, Any]]:
    msg = norm(message)

    for key, response in GENERAL_RESPONSES:
        if key in msg:
            return {"response": response, "mode": "offline"}

    if "all tests" in msg or "full list" in msg:
        lines = ["🗂️ Here is the full test list:"]
        for category in get_data()["categories"]:
            items = [t for t in ALL_TESTS if t["category_id"] == category["id"]]
            lines.append(f"\n{category['name']} ({len(items)}):")
            for t in items:
                lines.append(f"• Test {t['testNo']}: {t['name']}")
        return {"response": "\n".join(lines), "mode": "offline"}

    category_id = detect_category(message)
    if category_id:
        # If the user mentions a category but not a specific test, return the category's test list.
        if any(h in msg for h in ("all", "list", "show", "every", "full", "how to", "steps", "test")):
            return {"response": list_tests_for_category(category_id), "mode": "offline"}
        category = CATEGORY_BY_ID.get(category_id)
        if category:
            items = [t for t in ALL_TESTS if t["category_id"] == category_id]
            preview = "\n".join(f"• Test {t['testNo']}: {t['name']}" for t in items[:4])
            return {
                "response": (
                    f"🗂️ {category['name']} has {len(items)} tests in this app.\n"
                    f"{category.get('description', '')}\n\n"
                    f"Top tests:\n{preview}\n\n"
                    f"Ask me for a test number or exact item name and I will explain the steps."
                ),
                "mode": "offline",
            }

    return None


def answer_message(message: str) -> Dict[str, Any]:
    general = answer_general(message)
    if general:
        return general

    test = find_best_test(message)
    if test:
        return answer_for_test(test, message)

    return {"response": DEFAULT_RESPONSE["explanation"], "mode": "offline"}


def analyze_observation(test_id: Optional[str], observation: str, test_name: str = "", category: str = "", food_item: str = "") -> Dict[str, Any]:
    test = TEST_BY_ID.get(test_id or "")
    if not test and test_name:
        test = find_best_test(test_name)
    if not test and food_item:
        test = find_best_test(food_item)
    if not test:
        return {
            "result": "🔍 ANALYSIS INCOMPLETE",
            "explanation": "I could not identify the test. Please send a clearer test name or test ID.",
            "risk_level": "Unknown",
            "mode": "offline",
        }

    obs = observation or ""
    keyword_hits = sum(1 for kw in test.get("keywords", []) if fuzzy_phrase_match(kw, obs))
    pure_hits = sum(1 for kw in [test.get("pureResult", "")] if kw and fuzzy_phrase_match(kw, obs))
    adulterated_hits = sum(1 for kw in [test.get("adulteratedResult", "")] if kw and fuzzy_phrase_match(kw, obs))

    # Bias toward adulterated if the observation clearly mentions a known clue.
    is_adulterated = keyword_hits > 0 or adulterated_hits > 0
    is_pure = pure_hits > 0 or any(token in obs for token in ("no ", "pure", "clean", "normal", "not adulterated"))

    if is_adulterated and not is_pure:
        return {
            "result": "⚠️ ADULTERATED (Offline Analysis)",
            "adulterant": test.get("adulterant", ""),
            "explanation": (
                f"Your observation matches the adulteration pattern for {test['name']}. "
                f"{test.get('adulteratedResult', '')}"
            ).strip(),
            "health_effects": [test.get("healthRisk", "")],
            "risk_level": test.get("riskLevel", "High"),
            "action": "Report to FSSAI at 1800-11-2100.",
            "mode": "offline",
            "test_id": test["id"],
        }

    if is_pure:
        return {
            "result": "✅ NOT ADULTERATED (Offline Analysis)",
            "explanation": test.get("pureResult", "Observation matches the pure sample."),
            "risk_level": "Safe",
            "mode": "offline",
            "test_id": test["id"],
        }

    return {
        "result": "🔍 ANALYSIS INCOMPLETE",
        "explanation": (
            f"I found the test: {test['name']}, but the observation needs more detail. "
            f"Try describing colour, layer, residue, settling, floating, foam, or smell."
        ),
        "risk_level": "Unknown",
        "mode": "offline",
        "test_id": test["id"],
    }


def get_static_response(test_id: str, message: str) -> Dict[str, Any]:
    test = TEST_BY_ID.get(test_id)
    if not test:
        # Fall back to a message-level match
        return answer_message(message)
    return answer_for_test(test, message)


def get_test_by_id(test_id: str) -> Optional[Dict[str, Any]]:
    return TEST_BY_ID.get(test_id)


def get_all_tests() -> List[Dict[str, Any]]:
    return ALL_TESTS


def get_category_by_id(category_id: str) -> Optional[Dict[str, Any]]:
    return CATEGORY_BY_ID.get(category_id)
