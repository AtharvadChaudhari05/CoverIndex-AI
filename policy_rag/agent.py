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
        ("advice", ["advice", "suggest", "suggestion", "recommend", "recommendation", "compare", "comparison", "better", "best"]),
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
    "bike",
    "car",
    "vehicle",
    "two wheeler",
    "four wheeler",
    "motorcycle",
    "copay",
    "deductible",
    "policy document",
    "policy pdf",
    "advice",
    "suggest",
    "suggestion",
    "recommend",
    "recommendation",
    "compare",
    "comparison",
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


ANSWER_CITATION_PATTERN = re.compile(
    r"("
    r"\[[^\]]+?\.(?:pdf|zip|txt)\s+p\.?\s*\d+\]"  # [file.pdf p. 4]
    r"|[\w._-]+\.(?:pdf|zip|txt)\s*\(?(?:p\.?|Page)\s*\d+\)?"  # file.pdf (Page 4) or file.pdf p. 4
    r"|https?://"
    r")",
    re.IGNORECASE,
)
OUT_OF_SCOPE_REFUSAL_MESSAGE = (
    "I cannot answer questions based on general knowledge. "
    "Please ask me something about your uploaded documents, insurance policies, or claims instead."
)
INTERNET_SEARCH_PROMPT_MESSAGE = (
    "I do not have sufficient information to answer this question. "
    "Do you want me to look up into some other sources or access the internet?"
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
        return True  # Scope classifier already handles refusals before LLM is called
    if "[NO_CONTEXT]" in stripped:
        return False
    # Relax strict citation check to avoid throwing away perfectly valid answers
    if has_evidence:
        return True
    return False


def build_rag_messages(query: str, context_snippets: list[str], mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    context_text = "\n\n".join(context_snippets) if context_snippets else "NO POLICY SNIPPETS AVAILABLE."
    system_prompt = load_system_prompt(mode)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        for msg in chat_history:
            if msg.get("role") in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})
                
    user_prompt = (
        "Verified Policy Snippets:\n"
        f"{context_text}\n\n"
        f"User Query: {query}\n"
        "Answer:"
    )
    messages.append({"role": "user", "content": user_prompt})
    return messages


def strip_think_tags(text: str) -> str:
    """Remove Qwen's internal <think>...</think> reasoning blocks from output."""
    import re
    # Remove complete <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Safety net: remove unclosed <think> block if closing tag was cut off by max_tokens
    text = re.sub(r'<think>.*$', '', text, flags=re.DOTALL)
    return text.strip()


def call_groq_rag(query: str, context_snippets: list[str], mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None) -> str | None:
    """Calls Groq API using the groq library to generate a response.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    messages = build_rag_messages(query, context_snippets, mode=mode, chat_history=chat_history)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        # Using openai/gpt-oss-120b (Groq recommended replacement for llama-3.3-70b-versatile)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.0,
            max_tokens=1500,
        )
        if completion.choices and completion.choices[0].message.content:
            return strip_think_tags(completion.choices[0].message.content)
    except Exception as e:
        print(f"[CoverIndex AI] Groq call failed: {e}. Trying fallback gpt-oss-120b...")
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.0,
                max_tokens=1500,
            )
            if completion.choices and completion.choices[0].message.content:
                return strip_think_tags(completion.choices[0].message.content)
        except Exception as e2:
            print(f"[CoverIndex AI] Groq fallback failed: {e2}")
    return None


def call_gemini_rag(query: str, context_snippets: list[str], mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None) -> str | None:
    """Calls Gemini API using the new google-genai library with legacy fallback.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    messages = build_rag_messages(query, context_snippets, mode=mode, chat_history=chat_history)
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


def rewrite_query_with_history(query: str, chat_history: list[dict[str, str]] | None) -> str:
    if not chat_history:
        # For a single query with no history, we still translate it if it's not English
        history_text = ""
    else:
        history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])
    
    system_prompt = (
        "You are an expert query understanding assistant. Your task is to process a user's query and output a standalone English search query. "
        "Rules:\n"
        "1. If the query is in any language other than English (e.g., Marathi, Hindi), you MUST translate it to English.\n"
        "2. If there is a chat history, use it to resolve any ambiguous references in the follow-up query (e.g., 'what are its benefits' -> 'what are the benefits of the HDFC life policy').\n"
        "3. Output ONLY the standalone English search query and absolutely nothing else."
    )
    user_prompt = f"Chat History:\n{history_text if history_text else 'None'}\n\nUser Query: {query}\n\nStandalone English Query:"
    
    api_key = os.getenv("GROQ_API_KEY")
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.0,
            max_tokens=2048,
        )
        rewritten = strip_think_tags(response.choices[0].message.content)
        if rewritten:
            return rewritten
    except Exception as e:
        print(f"[CoverIndex AI] Groq query rewrite failed: {e}")
        
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] Gemini query rewrite failed: {e}. Trying legacy google-generativeai...")

        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=gemini_key)
            model = legacy_genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] legacy google-generativeai call failed: {e}")

    return query

def translate_to_user_language(text: str, user_query: str) -> str:
    """Translates the given text into the language of the user_query using Groq with Gemini fallback."""
    system_prompt = (
        "You are a translation assistant. Your task is to detect the language of the provided 'User Query', "
        "and translate the 'Text to Translate' into that exact same language. "
        "Output ONLY the translated text and nothing else."
    )
    user_prompt = f"User Query: {user_query}\n\nText to Translate: {text}"
    
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="openai/gpt-oss-120b",
                temperature=0.0,
                max_tokens=2048,
            )
            translated = strip_think_tags(response.choices[0].message.content)
            if translated:
                return translated
        except Exception as e:
            print(f"[CoverIndex AI] Groq translation failed: {e}")
            
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] Gemini translation failed: {e}. Trying legacy google-generativeai...")
            
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=gemini_key)
            model = legacy_genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] legacy google-generativeai call failed: {e}")

    return text

def perform_internet_search(query: str) -> list[str]:
    """Searches the internet using ddgs and returns formatted snippet results."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        snippets = []
        for r in results:
            snippet = r.get("body", "")
            href = r.get("href", "")
            title = r.get("title", "")
            if snippet and href:
                snippets.append(f"Source [{href}]: {title} - {snippet}")
        return snippets
    except Exception as e:
        print(f"[CoverIndex AI] Internet search failed: {e}")
        return []

def answer_query(index: PageIndex, query: str, file_name: str | None = None, mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None) -> QueryResult:
    original_query = query
    search_query = rewrite_query_with_history(query, chat_history)

    route = route_query(search_query)
    trace = [f"router: original query: {original_query}"]
    if search_query != original_query:
        trace.append(f"router: rewrote/translated query to: {search_query}")
    
    trace.append(f"router: route reasoning: {route.reasoning}")
    scope, scope_reasoning = classify_query_scope(search_query, route=route, file_name=file_name)
    trace.append(f"scope: {scope_reasoning}")

    if scope == "out_of_scope" and mode != "fallback_confirmed":
        trace.append("generator: refused out-of-scope query before retrieval")
        translated_refusal = translate_to_user_language(OUT_OF_SCOPE_REFUSAL_MESSAGE, original_query)
        return QueryResult(
            answer=translated_refusal,
            confidence=0.0,
            route=route,
            sources=[],
            trace=trace,
        )

    # Auto-detect mentioned file name in query if not explicitly passed
    file_name_filter = file_name
    if not file_name_filter:
        lowered_query = search_query.lower().replace("_", " ")
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
            search_query,
            file_name_filter=file_name_filter,
            top_k=6,
        )
    else:
        # Use routed insurer or product name to filter search
        hits = index.search(
            search_query,
            insurer_filter=route.insurer,
            product_hint=route.product_hint,
            top_k=6,
        )

        if not hits and route.insurer is not None:
            trace.append("no direct match under insurer filter; falling back to broader search")
            hits = index.search(search_query, product_hint=route.product_hint, top_k=2)


    sources = []
    evidence_snippets: list[str] = []
    evidence_sentences: list[str] = []
    
    if hits:
        max_context_pages = 4
        context_hits = index.expanded_context(hits, max_pages=max_context_pages)
        trace.append(f"retriever: selected {len(context_hits)} grounded pages")

        seen_sentences: set[str] = set()
        query_tokens = set(tokenize(query))

        # Max 1800 chars per snippet to capture more relevant content while staying within Groq TPM limits
        MAX_SNIPPET_CHARS = 1800

        for hit in context_hits:
            citation = f"{hit.record.source_name} p. {hit.record.page_number}"
            snippet_header = f"--- Source: {hit.record.source_name} (Page {hit.record.page_number}) ---"
            truncated_text = hit.record.text[:MAX_SNIPPET_CHARS]
            full_snippet = f"{snippet_header}\n{truncated_text}"
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

    if mode == "fallback_confirmed":
        trace.append("generator: fallback confirmed; performing internet search")
        web_snippets = perform_internet_search(query)
        if web_snippets:
            # Prepend web snippets so the LLM sees them first
            evidence_snippets = web_snippets + evidence_snippets
            
            web_sources = []
            for i, snip in enumerate(web_snippets):
                href_start = snip.find("[") + 1
                href_end = snip.find("]")
                href = snip[href_start:href_end] if href_start > 0 and href_end > href_start else "Internet"
                web_sources.append({
                    "citation": href,
                    "insurer": "Web Search",
                    "product": "General",
                    "page_number": i+1,
                    "score": 1.0,
                    "snippet": snip,
                })
            # Prepend web sources so the auto-appender uses them
            sources = web_sources + sources

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
                trace.append("generator: strict rejection triggered for Gemini API response; falling back to raw context.")
                gemini_answer = None
                answer = None
                
        if not gemini_answer:
            # Only trigger internet search if there were NO evidence snippets at all
            if evidence_snippets:
                # We had documents but LLMs refused to answer — force a simple summary
                trace.append("generator: LLMs refused despite having evidence; constructing answer from snippets")
                summary_parts = []
                for s in sources[:3]:
                    if s.get('snippet'):
                        summary_parts.append(s['snippet'])
                answer = "Based on the retrieved policy documents:\n\n" + "\n\n".join(summary_parts) if summary_parts else None
            
            if not evidence_snippets or not answer:
                trace.append("generator: insufficient retrieved context for a grounded answer or LLM generation failed")
                answer = translate_to_user_language(INTERNET_SEARCH_PROMPT_MESSAGE, original_query) + " [NO_CONTEXT]"

    # Auto-append missing citations if the LLM forgot to include them
    if answer and "[NO_CONTEXT]" in answer:
        answer = answer.replace("[NO_CONTEXT]", "").strip()
        trace.append("generator: detected NO_CONTEXT tag; skipped appending citations")
    elif answer and answer != OUT_OF_SCOPE_REFUSAL_MESSAGE and sources:
        has_citations = answer_has_citations(answer)
        has_sources_section = bool(re.search(r'\*?\*?Sources:\*?\*?', answer, re.IGNORECASE))
        
        if has_citations or has_sources_section:
            # LLM already included sources — strip its version and replace with our clean format
            answer = re.sub(r'\n+\*?\*?Sources:?\*?\*?[\s\S]*$', '', answer, flags=re.IGNORECASE).strip()
            trace.append("generator: stripped LLM sources section to replace with clean format")
        
        # Always append our properly formatted sources
        sources_text = "\n\n**Sources:**\n"
        for s in sources[:3]:  # Top 3 sources
            if s['citation'].startswith("http"):
                sources_text += f"- [{s['citation']}]({s['citation']})\n"
            else:
                sources_text += f"- **{s['citation']}**\n"
        answer += sources_text
        trace.append("generator: appended clean formatted citations to the answer")

    return QueryResult(
        answer=answer,
        confidence=confidence,
        route=route,
        sources=sources,
        trace=trace,
    )
