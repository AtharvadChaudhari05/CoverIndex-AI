from __future__ import annotations

import os
import re
from collections import OrderedDict

from .config import load_system_prompt
from .index import PageIndex
from .models import QueryResult, QueryRoute
from .utils import compact_whitespace, normalize_text, split_sentences, tokenize

INSURER_KEYWORDS = OrderedDict(
    [
        ("HDFC Life", ["hdfc", "hdfc life"]),
        ("SBI General", ["sbi", "sbi general"]),
        ("Tata AIG", ["tata aig", "tata"]),
        ("LIC", ["lic", "life insurance corporation", "life insurance corp"]),
        ("ICICI Prudential", ["icici", "prudential", "icici prudential"]),
        ("Aegon Life", ["aegon", "aegon life"]),
    ]
)

INTENT_RULES = OrderedDict(
    [
        ("claim", ["claim", "death benefit", "nominee", "intimate a claim", "claim documents", "documents needed"]),
        ("eligibility", ["eligibility", "eligible", "age", "occupation", "entry age", "maximum age", "minimum age"]),
        ("premium", ["premium", "policy fee", "charges", "installment", "grace period"]),
        ("benefits", ["benefit", "cover", "coverage", "sum assured", "maturity", "survival benefit", "death benefit"]),
        ("exclusions", ["exclusion", "not covered", "waiting period", "exempt", "pre-existing disease"]),
        ("surrender", ["surrender", "paid-up", "termination", "discontinuance", "surrender value"]),
        ("rider", ["rider", "waiver of premium", "accidental disability", "health plus"]),
        ("free-look", ["free look", "cooling off", "return the policy", "look period"]),
        ("policy details", ["policy number", "term", "maturity date", "nominee"]),
    ]
)

INSURANCE_SCOPE_TERMS = [
    "insurance",
    "policy",
    "claim",
    "claims",
    "renewal",
    "renewals",
    "premium",
    "coverage",
    "covered",
    "sum assured",
    "insurer",
    "cashless",
    "hospitalization",
    "health",
    "motor",
    "term life",
    "term insurance",
    "life insurance",
    "add-on",
    "add ons",
    "exclusion",
    "waiting period",
    "co-pay",
    "copay",
    "deductible",
    "policy document",
    "policy pdf",
]

OUT_OF_SCOPE_TERMS = [
    "python",
    "java",
    "oop",
    "programming",
    "algorithm",
    "database",
    "sql",
    "linux",
    "react",
    "javascript",
    "general knowledge",
    "history",
    "physics",
    "chemistry",
    "mathematics",
]

CONFIRMATION_TERMS = {
    "yes",
    "y",
    "yeah",
    "yep",
    "ok",
    "okay",
    "sure",
    "confirm",
    "confirmed",
    "go ahead",
    "proceed",
}


def route_query(query: str) -> QueryRoute:
    lowered = query.lower()
    insurer = None
    reasoning_parts: list[str] = []
    for candidate, needles in INSURER_KEYWORDS.items():
        matched = False
        for needle in needles:
            pattern = r"\b" + re.escape(needle) + r"\b"
            if re.search(pattern, lowered):
                insurer = candidate
                reasoning_parts.append(f"matched insurer keyword: {candidate}")
                matched = True
                break
        if matched:
            break

    intent = "general"
    for label, needles in INTENT_RULES.items():
        matched = False
        for needle in needles:
            pattern = r"\b" + re.escape(needle) + r"\b"
            if re.search(pattern, lowered):
                intent = label
                reasoning_parts.append(f"matched intent pattern: {label}")
                matched = True
                break
        if matched:
            break


    product_hint = extract_product_hint(query)
    if product_hint:
        reasoning_parts.append(f"product hint: {product_hint}")

    if not reasoning_parts:
        reasoning_parts.append("no special routing signal; use broad page search")

    return QueryRoute(
        insurer=insurer,
        product_hint=product_hint,
        intent=intent,
        reasoning="; ".join(reasoning_parts),
    )


def extract_product_hint(query: str) -> str | None:
    lowered = normalize_text(query).lower()
    candidates = [
        "smart protect plus",
        "click 2 achieve",
        "click 2 wealth",
        "group term life",
        "sampoorn nivesh plus",
        "guaranteed income insurance plan",
        "cancer care",
        "cardiac care",
        "health plus rider",
        "waiver of premium rider",
        "income benefit on accidental disability rider",
        "aajeevan growth nivesh and income",
        "arogya sanjeevani",
        "bharat griha raksha",
        "cyber shield",
        "cyber vault",
        "optima secure",
        "digi term",
    ]
    for candidate in candidates:
        if candidate in lowered:
            return candidate

    words = tokenize(query)
    if len(words) >= 3:
        return " ".join(words[:4])
    return None


def _has_keyword(query: str, terms: list[str] | set[str]) -> bool:
    lowered = normalize_text(query).lower()
    for term in terms:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, lowered):
            return True
    return False


def classify_query_scope(query: str, route: QueryRoute | None = None, file_name: str | None = None) -> tuple[str, str]:
    lowered = normalize_text(query).lower()
    if file_name:
        return "insurance", f"explicit file mention: {file_name}"
    if route and (route.insurer or route.intent != "general"):
        return "insurance", f"routing indicates insurance context: {route.reasoning}"
    if _has_keyword(lowered, INSURANCE_SCOPE_TERMS):
        return "insurance", "matched insurance vocabulary"
    if _has_keyword(lowered, OUT_OF_SCOPE_TERMS):
        return "out_of_scope", "matched out-of-domain vocabulary"
    return "out_of_scope", "no insurance signal found"


def is_confirmation_query(query: str) -> bool:
    cleaned = normalize_text(query).strip().lower()
    cleaned = re.sub(r"[.!?]+$", "", cleaned)
    return cleaned in CONFIRMATION_TERMS


ANSWER_CITATION_PATTERN = re.compile(r"\[[^\]]+?\.(?:pdf|zip|txt)\s+p\.?\s*\d+\]", re.IGNORECASE)
OUT_OF_SCOPE_REFUSAL_MESSAGE = (
    "This looks outside my scope as an insurance assistant. "
    "Could you ask me something about your insurance, policies, or claims instead?"
)
FALLBACK_PREFIX = "This is general information and not based on your uploaded policy documents:"


def answer_has_citations(answer: str) -> bool:
    return bool(ANSWER_CITATION_PATTERN.search(answer))


def normalize_fallback_answer(answer: str) -> str:
    stripped = answer.strip()
    if stripped.startswith(FALLBACK_PREFIX):
        return stripped
    return f"{FALLBACK_PREFIX} {stripped}"


def is_allowed_normal_mode_answer(answer: str, has_evidence: bool) -> bool:
    stripped = answer.strip()
    if stripped == OUT_OF_SCOPE_REFUSAL_MESSAGE:
        return True
    if has_evidence and answer_has_citations(stripped):
        return True
    return False


def build_rag_messages(query: str, context_snippets: list[str], mode: str = "insurance_rag") -> list[dict[str, str]]:
    context_text = "\n\n".join(context_snippets) if context_snippets else "NO POLICY SNIPPETS AVAILABLE."
    system_prompt = load_system_prompt(mode)
    user_prompt = (
        "Verified Policy Snippets:\n"
        f"{context_text}\n\n"
        f"User Query: {query}\n"
        "Answer:"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_groq_rag(query: str, context_snippets: list[str], mode: str = "insurance_rag") -> str | None:
    """Calls Groq API using the groq library to generate a response.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    messages = build_rag_messages(query, context_snippets, mode=mode)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        # Using llama-3.1-8b-instant
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.0,
            max_tokens=1024,
        )
        if completion.choices and completion.choices[0].message.content:
            return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[CoverIndex AI] Groq call failed: {e}. Trying fallback llama-3.3-70b-versatile...")
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.0,
                max_tokens=1024,
            )
            if completion.choices and completion.choices[0].message.content:
                return completion.choices[0].message.content.strip()
        except Exception as e2:
            print(f"[CoverIndex AI] Groq fallback failed: {e2}")
    return None


def call_gemini_rag(query: str, context_snippets: list[str], mode: str = "insurance_rag") -> str | None:
    """Calls Gemini API using the new google-genai library with legacy fallback.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    messages = build_rag_messages(query, context_snippets, mode=mode)
    prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

    # Try modern google-genai client
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        if response.text:
            return response.text.strip()
    except Exception as e:
        print(f"[CoverIndex AI] google-genai call failed: {e}. Trying legacy google-generativeai...")

    # Fallback to legacy google-generativeai client
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
    except Exception as e:
        print(f"[CoverIndex AI] legacy google-generativeai call failed: {e}")

    return None


def answer_query(index: PageIndex, query: str, file_name: str | None = None, mode: str = "insurance_rag") -> QueryResult:
    route = route_query(query)
    trace = [f"router: {route.reasoning}"]
    scope, scope_reasoning = classify_query_scope(query, route=route, file_name=file_name)
    trace.append(f"scope: {scope_reasoning}")

    if scope == "out_of_scope" and mode != "fallback_confirmed":
        trace.append("generator: refused out-of-scope query before retrieval")
        return QueryResult(
            answer=OUT_OF_SCOPE_REFUSAL_MESSAGE,
            confidence=0.0,
            route=route,
            sources=[],
            trace=trace,
        )

    # Auto-detect mentioned file name in query if not explicitly passed
    file_name_filter = file_name
    if not file_name_filter:
        lowered_query = query.lower().replace("_", " ")
        all_filenames = sorted(list({r.file_name for r in index.records}), key=len, reverse=True)
        for fname in all_filenames:
            fname_clean = fname.lower().replace("_", " ")
            fname_no_ext = fname_clean.rsplit(".", 1)[0]
            if fname_clean in lowered_query or (len(fname_no_ext) > 10 and fname_no_ext in lowered_query):
                file_name_filter = fname
                trace.append(f"router: auto-detected policy document mention in query: {fname}")
                break

    if file_name_filter:
        trace.append(f"retriever: search constrained to document: {file_name_filter}")
        hits = index.search(
            query,
            file_name_filter=file_name_filter,
            top_k=4,
        )
    else:
        # Use routed insurer or product name to filter search
        hits = index.search(
            query,
            insurer_filter=route.insurer,
            product_hint=route.product_hint,
            top_k=4,
        )

        if not hits and route.insurer is not None:
            trace.append("no direct match under insurer filter; falling back to broader search")
            hits = index.search(query, product_hint=route.product_hint, top_k=4)


    sources = []
    evidence_snippets: list[str] = []
    evidence_sentences: list[str] = []
    
    if hits:
        max_context_pages = 6 if file_name_filter else 2
        context_hits = index.expanded_context(hits, max_pages=max_context_pages)
        trace.append(f"retriever: selected {len(context_hits)} grounded pages")

        seen_sentences: set[str] = set()
        query_tokens = set(tokenize(query))

        for hit in context_hits:
            citation = f"{hit.record.source_name} p. {hit.record.page_number}"
            snippet_header = f"--- Source: {hit.record.source_name} (Page {hit.record.page_number}) ---"
            full_snippet = f"{snippet_header}\n{hit.record.text}"
            evidence_snippets.append(full_snippet)

            sources.append(
                {
                    "citation": citation,
                    "insurer": hit.record.insurer,
                    "product": hit.record.product,
                    "page_number": hit.record.page_number,
                    "score": round(hit.score, 3),
                    "snippet": hit.highlight,
                }
            )

            if len(evidence_sentences) < 4:
                for sentence in split_sentences(hit.record.text):
                    tokens = set(tokenize(sentence))
                    overlap = len(tokens.intersection(query_tokens))
                    if overlap == 0 and len(evidence_sentences) > 0:
                        continue
                    sentence = compact_whitespace(sentence, 220)
                    if sentence and sentence not in seen_sentences:
                        seen_sentences.add(sentence)
                        evidence_sentences.append(f"{sentence} [{citation}]")
                    if len(evidence_sentences) >= 4:
                        break

        
        confidence = min(0.98, round((hits[0].score / 8.0) + 0.25, 2))
    else:
        trace.append("retriever: no grounded pages found")
        confidence = 0.5

    # Try Groq generation first
    groq_answer = call_groq_rag(query, evidence_snippets, mode=mode)
    
    if groq_answer:
        if mode == "fallback_confirmed":
            answer = normalize_fallback_answer(groq_answer)
            trace.append("generator: synthesis completed using Groq API in fallback-confirmed mode")
        elif is_allowed_normal_mode_answer(groq_answer, bool(evidence_snippets)):
            answer = groq_answer
            trace.append("generator: synthesis completed using Groq API (grounding validated)")
        else:
            trace.append("generator: rejected Groq response without valid grounding")
            groq_answer = None
            answer = None

    if not groq_answer:
        # Try Gemini generation second
        gemini_answer = call_gemini_rag(query, evidence_snippets, mode=mode)
        if gemini_answer:
            if mode == "fallback_confirmed":
                answer = normalize_fallback_answer(gemini_answer)
                trace.append("generator: synthesis completed using Gemini API in fallback-confirmed mode")
            elif is_allowed_normal_mode_answer(gemini_answer, bool(evidence_snippets)):
                answer = gemini_answer
                trace.append("generator: synthesis completed using Gemini API (grounding validated)")
            else:
                trace.append("generator: rejected Gemini response without valid grounding")
                gemini_answer = None
                answer = None
                
        if not gemini_answer:
            # Fallback to local rule-based sentence synthesizer
            if evidence_sentences:
                trace.append("generator: no valid API answer; synthesized via local offline grounded extractor")
                answer_lines = [
                    "### Grounded Response (Local Synthesis Mode)",
                    "I couldn't generate a natural language summary, but here are the exact verified policy details matching your query:",
                    ""
                ]
                for sentence in evidence_sentences:
                    answer_lines.append(f"- {sentence}")
                answer_lines.append("")
                answer = "\n".join(answer_lines)
            else:
                trace.append("generator: insufficient retrieved context for a grounded answer")
                answer = OUT_OF_SCOPE_REFUSAL_MESSAGE

    return QueryResult(
        answer=answer,
        confidence=confidence,
        route=route,
        sources=sources,
        trace=trace,
    )
