from __future__ import annotations

import os
import re
from collections import OrderedDict

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


def call_groq_rag(query: str, context_snippets: list[str]) -> str | None:
    """Calls Groq API using the groq library to generate a response.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    context_text = "\n\n".join(context_snippets) if context_snippets else "NO POLICY SNIPPETS AVAILABLE."
    prompt = f"""You are a highly precise and verified AI insurance assistant for CoverIndex AI.
Your goal is to answer the query below.

INSTRUCTIONS:
1. Synthesize a cohesive, natural response to the user's query in your own words, strictly based on the provided verified policy document snippets below when they contain the relevant information. Formulate your response in clear, fluent sentences rather than listing raw quotes or copy-pasting verbatim text.
2. For every fact or detail you mention from the policy snippets, you MUST cite the source file name and page number exactly as provided in the snippets in square brackets (e.g. [policy_bond.pdf p. 4]).
3. If the snippets do not contain any relevant information to answer the query, or if context is empty, you should answer the query using your own general knowledge. In this case, please begin your response by stating that the answer is based on general knowledge rather than the policy documents.

Verified Policy Snippets:
{context_text}

User Query: {query}
Answer:"""

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        # Using llama-3.1-8b-instant
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful insurance assistant. Prioritize answering using the provided verified policy snippets. If the snippets do not contain the answer, use your own general knowledge and state that the answer is based on general knowledge."},
                {"role": "user", "content": prompt}
            ],
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
                messages=[
                    {"role": "system", "content": "You are a helpful insurance assistant. Prioritize answering using the provided verified policy snippets. If the snippets do not contain the answer, use your own general knowledge and state that the answer is based on general knowledge."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1024,
            )
            if completion.choices and completion.choices[0].message.content:
                return completion.choices[0].message.content.strip()
        except Exception as e2:
            print(f"[CoverIndex AI] Groq fallback failed: {e2}")
    return None


def call_gemini_rag(query: str, context_snippets: list[str]) -> str | None:
    """Calls Gemini API using the new google-genai library with legacy fallback.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    context_text = "\n\n".join(context_snippets) if context_snippets else "NO POLICY SNIPPETS AVAILABLE."
    prompt = f"""You are a highly precise and verified AI insurance assistant for CoverIndex AI.
Your goal is to answer the query below.

INSTRUCTIONS:
1. Synthesize a cohesive, natural response to the user's query in your own words, strictly based on the provided verified policy document snippets below when they contain the relevant information. Formulate your response in clear, fluent sentences rather than listing raw quotes or copy-pasting verbatim text.
2. For every fact or detail you mention from the policy snippets, you MUST cite the source file name and page number exactly as provided in the snippets in square brackets (e.g. [policy_bond.pdf p. 4]).
3. If the snippets do not contain any relevant information to answer the query, or if context is empty, you should answer the query using your own general knowledge. In this case, please begin your response by stating that the answer is based on general knowledge rather than the policy documents.

Verified Policy Snippets:
{context_text}

User Query: {query}
Answer:"""

    # Try modern google-genai client
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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


def answer_query(index: PageIndex, query: str, file_name: str | None = None) -> QueryResult:
    route = route_query(query)
    trace = [f"router: {route.reasoning}"]

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
    groq_answer = call_groq_rag(query, evidence_snippets)

    if groq_answer:
        answer = groq_answer
        trace.append("generator: synthesis completed using Groq API (100% grounded)")
    else:
        # Try Gemini generation second
        gemini_answer = call_gemini_rag(query, evidence_snippets)
        if gemini_answer:
            answer = gemini_answer
            trace.append("generator: synthesis completed using Gemini API (100% grounded)")
        else:
            # Fallback to local rule-based sentence synthesizer
            trace.append("generator: no API key found; synthesized via local offline grounded extractor")
            answer_lines = [
                "### Grounded Response (Local Offline Mode)",
                "No active LLM API key detected, but here are the exact verified policy details matching your query:",
                ""
            ]
            for sentence in evidence_sentences:
                answer_lines.append(f"- {sentence}")
            answer_lines.append("")
            answer_lines.append("> [!NOTE]\n> To enable natural language summaries, configure a `GROQ_API_KEY` or `GEMINI_API_KEY` in your `.env` file.")
            answer = "\n".join(answer_lines)

    return QueryResult(
        answer=answer,
        confidence=confidence,
        route=route,
        sources=sources,
        trace=trace,
    )
