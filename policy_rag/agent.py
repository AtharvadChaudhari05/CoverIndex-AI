from __future__ import annotations

import os
import re
from collections import OrderedDict

from .config import load_system_prompt, require_fallback_confirmation
from .index import PageIndex
from .models import QueryResult, QueryRoute
from .web import read_pages
from .utils import compact_whitespace, detect_script_language, guess_devanagari_language, normalize_text, split_sentences, tokenize

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
    # Hindi
    "हाँ", "हां", "हा", "ठीक है", "haan", "han", "haa", "theek hai", "thik hai",
    # Marathi
    "हो", "होय", "ठीक आहे", "ho", "hoy",
    # Tamil
    "ஆம்", "சரி", "aam", "sari",
    # Telugu
    "అవును", "సరే", "avunu", "sare",
    # Bengali
    "হ্যাঁ", "হাঁ", "ঠিক আছে",
}

# Answer languages the client may request. "auto" means: reply in the language of the query.
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
}
SUPPORTED_ANSWER_LANGUAGES = {"auto", *LANGUAGE_NAMES}

# Override with the GEMINI_MODEL env var when Google retires this model.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Gemini is only a fallback; without a limit its SDK retried "high demand" errors for over 7 minutes
GEMINI_TIMEOUT_SECONDS = 20


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
    cleaned = re.sub(r"[.!?।]+$", "", cleaned)
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
NO_ANSWER_MESSAGE = (
    "I could not find an answer to this question in your policy documents or on the web. "
    "Please try asking it in a different way."
)
GREETING_MESSAGE = "Hello! I can help you with insurance policies, claims, and coverage. What would you like to know?"

# Stored translations of the fixed system messages, so they need no LLM call.
FIXED_TRANSLATIONS = {
    OUT_OF_SCOPE_REFUSAL_MESSAGE: {
        "hi": "मैं सामान्य ज्ञान पर आधारित प्रश्नों का उत्तर नहीं दे सकता। कृपया इसके बजाय अपने अपलोड किए गए दस्तावेज़ों, बीमा पॉलिसियों या दावों के बारे में पूछें।",
        "mr": "मी सामान्य ज्ञानावर आधारित प्रश्नांची उत्तरे देऊ शकत नाही. कृपया त्याऐवजी तुमच्या अपलोड केलेल्या कागदपत्रांबद्दल, विमा पॉलिसींबद्दल किंवा दाव्यांबद्दल विचारा.",
        "ta": "பொது அறிவு சார்ந்த கேள்விகளுக்கு என்னால் பதிலளிக்க முடியாது. அதற்குப் பதிலாக, நீங்கள் பதிவேற்றிய ஆவணங்கள், காப்பீட்டுக் கொள்கைகள் அல்லது கோரிக்கைகள் பற்றி கேளுங்கள்.",
        "te": "సాధారణ జ్ఞానం ఆధారంగా ఉన్న ప్రశ్నలకు నేను సమాధానం ఇవ్వలేను. దయచేసి మీరు అప్‌లోడ్ చేసిన పత్రాలు, బీమా పాలసీలు లేదా క్లెయిమ్‌ల గురించి అడగండి.",
        "bn": "আমি সাধারণ জ্ঞানের উপর ভিত্তি করে প্রশ্নের উত্তর দিতে পারি না। অনুগ্রহ করে এর পরিবর্তে আপনার আপলোড করা নথি, বীমা পলিসি বা দাবি সম্পর্কে জিজ্ঞাসা করুন।",
    },
    INTERNET_SEARCH_PROMPT_MESSAGE: {
        "hi": "इस प्रश्न का उत्तर देने के लिए मेरे पास पर्याप्त जानकारी नहीं है। क्या आप चाहते हैं कि मैं अन्य स्रोतों में खोजूँ या इंटरनेट का उपयोग करूँ?",
        "mr": "या प्रश्नाचे उत्तर देण्यासाठी माझ्याकडे पुरेशी माहिती नाही. मी इतर स्रोतांमध्ये शोधावे किंवा इंटरनेट वापरावे असे तुम्हाला वाटते का?",
        "ta": "இந்தக் கேள்விக்கு பதிலளிக்க என்னிடம் போதுமான தகவல் இல்லை. நான் வேறு ஆதாரங்களில் தேட வேண்டுமா அல்லது இணையத்தைப் பயன்படுத்த வேண்டுமா?",
        "te": "ఈ ప్రశ్నకు సమాధానం ఇవ్వడానికి నా వద్ద తగినంత సమాచారం లేదు. నేను ఇతర వనరులలో వెతకాలా లేదా ఇంటర్నెట్‌ను ఉపయోగించాలా?",
        "bn": "এই প্রশ্নের উত্তর দেওয়ার জন্য আমার কাছে যথেষ্ট তথ্য নেই। আপনি কি চান আমি অন্য উৎসে খুঁজি বা ইন্টারনেট ব্যবহার করি?",
    },
    FALLBACK_PREFIX: {
        "hi": "यह सामान्य जानकारी है और आपके अपलोड किए गए पॉलिसी दस्तावेज़ों पर आधारित नहीं है:",
        "mr": "ही सामान्य माहिती आहे आणि तुमच्या अपलोड केलेल्या पॉलिसी कागदपत्रांवर आधारित नाही:",
        "ta": "இது பொதுவான தகவல், நீங்கள் பதிவேற்றிய பாலிசி ஆவணங்களை அடிப்படையாகக் கொண்டது அல்ல:",
        "te": "ఇది సాధారణ సమాచారం, మీరు అప్‌లోడ్ చేసిన పాలసీ పత్రాల ఆధారంగా లేదు:",
        "bn": "এটি সাধারণ তথ্য এবং আপনার আপলোড করা পলিসি নথির উপর ভিত্তি করে নয়:",
    },
    NO_ANSWER_MESSAGE: {
        "hi": "मुझे इस प्रश्न का उत्तर आपके पॉलिसी दस्तावेज़ों में या इंटरनेट पर नहीं मिला। कृपया इसे किसी दूसरे तरीके से पूछें।",
        "mr": "मला या प्रश्नाचे उत्तर तुमच्या पॉलिसी कागदपत्रांमध्ये किंवा इंटरनेटवर सापडले नाही. कृपया हा प्रश्न वेगळ्या पद्धतीने विचारा.",
        "ta": "இந்தக் கேள்விக்கான பதிலை உங்கள் பாலிசி ஆவணங்களிலோ இணையத்திலோ என்னால் கண்டுபிடிக்க முடியவில்லை. தயவுசெய்து வேறு விதமாகக் கேளுங்கள்.",
        "te": "ఈ ప్రశ్నకు సమాధానం మీ పాలసీ పత్రాలలో గానీ ఇంటర్నెట్‌లో గానీ నాకు దొరకలేదు. దయచేసి వేరే విధంగా అడగండి.",
        "bn": "আমি এই প্রশ্নের উত্তর আপনার পলিসি নথিতে বা ইন্টারনেটে খুঁজে পাইনি। অনুগ্রহ করে অন্যভাবে জিজ্ঞাসা করুন।",
    },
    GREETING_MESSAGE: {
        "hi": "नमस्ते! मैं बीमा पॉलिसियों, दावों और कवरेज के बारे में आपकी मदद कर सकता हूँ। आप क्या जानना चाहेंगे?",
        "mr": "नमस्कार! मी विमा पॉलिसी, दावे आणि कव्हरेजबद्दल तुमची मदत करू शकतो. तुम्हाला काय जाणून घ्यायचे आहे?",
        "ta": "வணக்கம்! காப்பீட்டுக் கொள்கைகள், கோரிக்கைகள் மற்றும் காப்பீட்டு வரம்பு பற்றி நான் உங்களுக்கு உதவ முடியும். நீங்கள் என்ன தெரிந்துகொள்ள விரும்புகிறீர்கள்?",
        "te": "నమస్కారం! బీమా పాలసీలు, క్లెయిమ్‌లు మరియు కవరేజ్ గురించి నేను మీకు సహాయం చేయగలను. మీరు ఏమి తెలుసుకోవాలనుకుంటున్నారు?",
        "bn": "নমস্কার! আমি বীমা পলিসি, দাবি এবং কভারেজ সম্পর্কে আপনাকে সাহায্য করতে পারি। আপনি কী জানতে চান?",
    },
}

# Small talk: a greeting or thanks, optionally followed only by filler words
SMALL_TALK_PHRASES = {
    "hi", "hii", "hiii", "hello", "hey", "namaste", "namaskar", "good morning", "good afternoon", "good evening",
    "good night", "thanks", "thank you", "thank u", "thx", "ty", "ok", "okay", "ok thanks", "okay thanks", "cool",
    "great", "nice", "bye", "goodbye", "see you", "dhanyavad", "dhanyawad", "shukriya",
    "नमस्ते", "नमस्कार", "धन्यवाद", "शुक्रिया", "आभार", "வணக்கம்", "நன்றி", "నమస్కారం", "ధన్యవాదాలు", "নমস্কার", "ধন্যবাদ",
}
SMALL_TALK_FILLER = {
    "there", "bot", "so", "much", "a", "lot", "that", "this", "helped", "it", "was", "is", "helpful", "again", "sir",
    "madam", "ji", "bro", "dear", "coverindex", "ai", "everyone", "all", "you", "very", "for", "the", "help", "info",
}
# Requests that act on an earlier reply (translate, shorten, ...) rather than ask for new information
FOLLOWUP_PATTERNS = [
    re.compile(r"\b(translate|translation|shorter|shorten|summari[sz]e|simpler|simplify|rephrase|reword|repeat)\b"),
    re.compile(r"\bin (english|hindi|marathi|tamil|telugu|bengali|bangla)\b"),
    re.compile(r"\b(above|previous|last|your|that) (answer|reply|response|message|question)\b"),
    re.compile(r"\b(say|explain) (that|it|this) again\b"),
    re.compile(r"\bin simple (words|terms|language)\b"),
    re.compile(r"\b(as|in) (a )?(table|bullet points|points)\b"),
]
FOLLOWUP_NATIVE_TERMS = [
    "अनुवाद", "इंग्रजी", "इंग्लिश", "अंग्रेज़ी", "अंग्रेजी", "थोडक्यात", "सोप्या", "संक्षेप", "आसान भाषा", "छोटा करके",
    "english madhe", "english mein", "english me",
]


def answer_has_citations(answer: str) -> bool:
    return bool(ANSWER_CITATION_PATTERN.search(answer))


def normalize_fallback_answer(answer: str, prefix: str = FALLBACK_PREFIX) -> str:
    stripped = answer.strip()
    if stripped.startswith(prefix):
        return stripped
    return f"{prefix} {stripped}"


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


def build_rag_messages(query: str, context_snippets: list[str], mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None, answer_language: str = "auto") -> list[dict[str, str]]:
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
    )
    if answer_language in LANGUAGE_NAMES:
        user_prompt += f"Respond in {LANGUAGE_NAMES[answer_language]}.\n"
    user_prompt += "Answer:"
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


def _gemini_client(api_key: str):
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=GEMINI_TIMEOUT_SECONDS * 1000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def call_groq_rag(query: str, context_snippets: list[str], mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None, answer_language: str = "auto") -> str | None:
    """Calls Groq API using the groq library to generate a response.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    messages = build_rag_messages(query, context_snippets, mode=mode, chat_history=chat_history, answer_language=answer_language)

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


def call_gemini_rag(query: str, context_snippets: list[str], mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None, answer_language: str = "auto") -> str | None:
    """Calls Gemini API using the new google-genai library with legacy fallback.
    Returns None if no API key is available or the request fails.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    messages = build_rag_messages(query, context_snippets, mode=mode, chat_history=chat_history, answer_language=answer_language)
    prompt = _flatten_messages(messages)

    # Try modern google-genai client
    try:
        from google import genai
        client = _gemini_client(api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
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
        model = legacy_genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt, request_options={"timeout": GEMINI_TIMEOUT_SECONDS})
        if response.text:
            return response.text.strip()
    except Exception as e:
        print(f"[CoverIndex AI] legacy google-generativeai call failed: {e}")
    return None


def rewrite_query_with_history(query: str, chat_history: list[dict[str, str]] | None) -> str:
    # Plain English with nothing to resolve from history: the LLM rewrite would return the same query.
    if not chat_history and detect_script_language(query) == "en":
        return query
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
            client = _gemini_client(gemini_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] Gemini query rewrite failed: {e}. Trying legacy google-generativeai...")

        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=gemini_key)
            model = legacy_genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}", request_options={"timeout": GEMINI_TIMEOUT_SECONDS})
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] legacy google-generativeai call failed: {e}")

    return query

def translate_to_user_language(text: str, user_query: str, target_language: str | None = None) -> str:
    """Translates the given text into target_language, or into the language of the user_query when no
    target is given. Uses stored translations when available, else Groq with Gemini fallback."""
    if target_language not in LANGUAGE_NAMES:
        detected = detect_script_language(user_query)
        if detected == "deva":
            # Hindi and Marathi share the Devanagari script; tell them apart by common words
            detected = guess_devanagari_language(user_query)
        target_language = detected if detected in LANGUAGE_NAMES else None
    if target_language == "en":
        return text
    if target_language and text in FIXED_TRANSLATIONS:
        return FIXED_TRANSLATIONS[text][target_language]

    if target_language:
        system_prompt = (
            f"You are a translation assistant. Translate the 'Text to Translate' into {LANGUAGE_NAMES[target_language]}. "
            "Output ONLY the translated text and nothing else."
        )
    else:
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
            client = _gemini_client(gemini_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] Gemini translation failed: {e}. Trying legacy google-generativeai...")
            
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=gemini_key)
            model = legacy_genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}", request_options={"timeout": GEMINI_TIMEOUT_SECONDS})
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] legacy google-generativeai call failed: {e}")

    return text

def _flatten_messages(messages: list[dict[str, str]]) -> str:
    """Gemini takes one prompt string, so join the system prompt and the conversation."""
    parts = []
    for message in messages:
        if message["role"] == "system":
            parts.append(message["content"])
        else:
            parts.append(f"{message['role'].capitalize()}: {message['content']}")
    return "\n\n".join(parts)


def _call_llm(messages: list[dict[str, str]], max_tokens: int = 1500) -> str | None:
    """Sends messages to Groq, with Gemini as fallback. Returns None when both fail."""
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.0,
                max_tokens=max_tokens,
            )
            if completion.choices and completion.choices[0].message.content:
                text = strip_think_tags(completion.choices[0].message.content)
                if text:
                    return text
        except Exception as e:
            print(f"[CoverIndex AI] Groq call failed: {e}")

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = _gemini_client(gemini_key)
            response = client.models.generate_content(model=GEMINI_MODEL, contents=_flatten_messages(messages))
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[CoverIndex AI] Gemini call failed: {e}")
    return None


def is_insurance_related_by_llm(query: str) -> bool:
    """Second opinion for queries without insurance keywords, such as "my flight got delayed, will I get money back"."""
    system_prompt = (
        "You classify messages sent to an insurance assistant. Answer YES if the message is about insurance, "
        "or about a situation that insurance commonly covers: health or hospital costs, accidents, vehicles, "
        "travel problems such as delays, cancellations, or lost baggage, death, disability, property damage, "
        "theft, or loans. Otherwise answer NO. Output only YES or NO."
    )
    verdict = _call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": query}], max_tokens=512)
    return bool(verdict) and verdict.strip().upper().startswith("YES")


def resolve_query_scope(query: str, route: QueryRoute | None = None, file_name: str | None = None) -> tuple[str, str]:
    scope, reasoning = classify_query_scope(query, route=route, file_name=file_name)
    # Only ask the LLM when no keyword matched either way; clear off-topic terms stay refused
    if scope == "out_of_scope" and reasoning == "no insurance signal found" and is_insurance_related_by_llm(query):
        return "insurance", "LLM judged the query to be insurance-related"
    return scope, reasoning


def classify_conversational(query: str, chat_history: list[dict[str, str]] | None) -> str | None:
    """Returns "small_talk" for greetings and thanks, "followup" for a request that acts on an earlier
    reply (translate, shorten, ...), or None for a normal question."""
    cleaned = re.sub(r"[.,!?।:;'\"()]+", " ", normalize_text(query).lower())
    words = cleaned.split()
    if not words:
        return None

    if len(words) <= 6 and not _has_keyword(cleaned, INSURANCE_SCOPE_TERMS):
        for length in (3, 2, 1):
            if " ".join(words[:length]) in SMALL_TALK_PHRASES and set(words[length:]) <= SMALL_TALK_FILLER:
                return "small_talk"

    has_earlier_reply = any(message.get("role") == "assistant" for message in chat_history or [])
    if has_earlier_reply and (
        any(pattern.search(cleaned) for pattern in FOLLOWUP_PATTERNS)
        or any(term in cleaned for term in FOLLOWUP_NATIVE_TERMS)
    ):
        return "followup"
    return None


def answer_conversational(query: str, chat_history: list[dict[str, str]] | None, kind: str, answer_language: str = "auto") -> QueryResult | None:
    """Answers small talk and requests about earlier replies from the conversation alone, without retrieval.
    Returns None for a follow-up the LLM could not handle, so the caller can use the normal pipeline."""
    route = route_query(query)
    trace = [f"router: original query: {query}", f"router: conversational message ({kind}); skipped document search"]

    messages = [{"role": "system", "content": load_system_prompt("conversational")}]
    for message in chat_history or []:
        if message.get("role") in ("user", "assistant"):
            messages.append({"role": message["role"], "content": message["content"]})
    user_prompt = query
    if answer_language in LANGUAGE_NAMES:
        user_prompt += f"\n\n(Default response language: {LANGUAGE_NAMES[answer_language]}. If my message asks for another language, use that language.)"
    messages.append({"role": "user", "content": user_prompt})

    answer = _call_llm(messages)
    if answer:
        trace.append("generator: conversational reply generated")
    elif kind == "small_talk":
        answer = translate_to_user_language(GREETING_MESSAGE, query, answer_language)
        trace.append("generator: LLM unavailable; used the stored greeting")
    else:
        return None
    return QueryResult(answer=answer, confidence=0.0, route=route, sources=[], trace=trace)


def perform_internet_search(query: str) -> list[str]:
    """Searches the web with ddgs, then reads the result pages and keeps the passages relevant to the query.
    A page that cannot be read falls back to its search snippet."""
    from ddgs import DDGS

    # Any single engine can block scraping without warning, so try them in order
    for backend in os.getenv("WEB_SEARCH_BACKENDS", "yahoo,bing,yandex,duckduckgo").split(","):
        try:
            results = DDGS().text(query, max_results=3, backend=backend.strip())
        except Exception as e:
            print(f"[CoverIndex AI] Internet search via {backend.strip()} failed: {e}")
            continue
        if results:
            return read_pages(results, query)
    return []

def answer_query(index: PageIndex, query: str, file_name: str | None = None, mode: str = "insurance_rag", chat_history: list[dict[str, str]] | None = None, search_query: str | None = None, answer_language: str = "auto", scope: tuple[str, str] | None = None) -> QueryResult:
    original_query = query
    if search_query is None:
        search_query = rewrite_query_with_history(query, chat_history)

    route = route_query(search_query)
    trace = [f"router: original query: {original_query}"]
    if search_query != original_query:
        trace.append(f"router: rewrote/translated query to: {search_query}")
    
    trace.append(f"router: route reasoning: {route.reasoning}")
    scope, scope_reasoning = scope or resolve_query_scope(search_query, route=route, file_name=file_name)
    trace.append(f"scope: {scope_reasoning}")

    if scope == "out_of_scope" and mode != "fallback_confirmed":
        trace.append("generator: refused out-of-scope query before retrieval")
        translated_refusal = translate_to_user_language(OUT_OF_SCOPE_REFUSAL_MESSAGE, original_query, answer_language)
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
        web_snippets = perform_internet_search(search_query)
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

    fallback_prefix = translate_to_user_language(FALLBACK_PREFIX, original_query, answer_language) if mode == "fallback_confirmed" else FALLBACK_PREFIX

    # Try Groq generation first
    groq_answer = call_groq_rag(query, evidence_snippets, mode=mode, chat_history=chat_history, answer_language=answer_language)
    
    # "[NO_CONTEXT]" is a real answer ("the documents do not cover this"), not a failure, so Gemini need not retry it
    groq_found_no_context = bool(groq_answer) and "[NO_CONTEXT]" in groq_answer
    if groq_answer:
        if mode == "fallback_confirmed":
            answer = normalize_fallback_answer(groq_answer, fallback_prefix)
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
        gemini_answer = None if groq_found_no_context else call_gemini_rag(query, evidence_snippets, mode=mode, chat_history=chat_history, answer_language=answer_language)
        if gemini_answer:
            if mode == "fallback_confirmed":
                answer = normalize_fallback_answer(gemini_answer, fallback_prefix)
                trace.append("generator: synthesis completed using Gemini API in fallback-confirmed mode")
            elif is_allowed_normal_mode_answer(gemini_answer, bool(evidence_snippets)):
                answer = gemini_answer
                trace.append("generator: synthesis completed using Gemini API (grounding validated)")
            else:
                trace.append("generator: strict rejection triggered for Gemini API response; falling back to raw context.")
                gemini_answer = None
                answer = None
                
        if not gemini_answer and mode == "fallback_confirmed":
            trace.append("generator: no answer from the web search either")
            answer = translate_to_user_language(NO_ANSWER_MESSAGE, original_query, answer_language)
            sources = []
        elif not gemini_answer and not require_fallback_confirmation():
            trace.append("generator: no grounded answer in the policy documents; searching the web automatically")
            web_result = answer_query(
                index, original_query, file_name=file_name, mode="fallback_confirmed", chat_history=chat_history,
                search_query=search_query, answer_language=answer_language, scope=(scope, scope_reasoning),
            )
            web_result.trace[:0] = trace
            return web_result
        elif not gemini_answer:
            trace.append("generator: insufficient retrieved context for a grounded answer or LLM returned NO_CONTEXT. Triggering internet search fallback.")
            answer = translate_to_user_language(INTERNET_SEARCH_PROMPT_MESSAGE, original_query, answer_language) + " [NO_CONTEXT]"

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
