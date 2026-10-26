from __future__ import annotations

import re
import unicodedata
from collections import Counter


STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "but",
    "by",
    "can",
    "company",
    "doc",
    "document",
    "explain",
    "find",
    "for",
    "from",
    "get",
    "had",
    "has",
    "have",
    "herein",
    "hereof",
    "how",
    "i",
    "if",
    "in",
    "info",
    "information",
    "insurance",
    "insured",
    "into",
    "is",
    "it",
    "life",
    "master",
    "may",
    "me",
    "member",
    "not",
    "of",
    "on",
    "or",
    "our",
    "pdf",
    "plan",
    "please",
    "policy",
    "shall",
    "should",
    "show",
    "subject",
    "table",
    "tell",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "you",
    "your",
}




TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+/.-]*", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def stem(word: str) -> str:
    word = word.lower()
    if len(word) <= 3:
        return word
    if word.endswith("sses"):
        word = word[:-2]
    elif word.endswith("ies"):
        word = word[:-3] + "y"
    elif word.endswith("s") and not word.endswith("ss") and not word.endswith("us") and not word.endswith("is") and not word.endswith("as"):
        word = word[:-1]
    if word.endswith("eed"):
        pass
    elif word.endswith("ed"):
        word = word[:-2]
        if word.endswith("i"):
            word = word[:-1] + "y"
    elif word.endswith("ing"):
        word = word[:-3]
        if word.endswith("i"):
            word = word[:-1] + "y"
    if word.endswith("ance") or word.endswith("ence"):
        word = word[:-4]
    if word.endswith("er") or word.endswith("or"):
        if len(word) > 5:
            word = word[:-2]
    if word.endswith("e") and len(word) > 4:
        word = word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text.lower())]
    cleaned = []
    for token in tokens:
        t = token.strip(".,/-+()'")
        if t not in STOPWORDS and len(t) > 1:
            cleaned.append(stem(t))
    return cleaned



def token_counts(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def split_sentences(text: str) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    parts = SENTENCE_RE.split(cleaned)
    sentences = [part.strip() for part in parts if part.strip()]
    return sentences


def compact_whitespace(text: str, limit: int = 260) -> str:
    cleaned = normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def choose_title_from_text(text: str, fallback: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return fallback

    for line in lines[:8]:
        lowered = line.lower()
        if len(line) > 10 and "page" not in lowered and "table of contents" not in lowered:
            if sum(1 for char in line if char.isalpha()) >= 6:
                return line
    return fallback


def top_terms(text: str, limit: int = 12) -> list[str]:
    counts = token_counts(text)
    return [term for term, _ in counts.most_common(limit)]


SCRIPT_RANGES = [
    ("deva", re.compile(r"[ऀ-ॿ]")),  # Hindi, Marathi
    ("bn", re.compile(r"[ঀ-৿]")),
    ("ta", re.compile(r"[஀-௿]")),
    ("te", re.compile(r"[ఀ-౿]")),
]


# Common romanized Hindi/Marathi words. Plain ASCII queries containing them still need the LLM rewrite.
ROMANIZED_INDIC_WORDS = {
    "kya", "kaise", "kaun", "kitna", "kitne", "mein", "mera", "meri", "mere", "hai", "hain",
    "nahi", "kab", "aur", "ka", "ki", "ke", "ko", "se", "bhi", "chahiye", "milega",
    "ahe", "aahe", "kay", "majha", "majhi", "mala", "kasa", "kashi", "pahije",
}


def detect_script_language(text: str) -> str | None:
    """Cheap script check: returns "en" for plain Latin text, a script/language code
    for a known Indic script, or None when the script is unknown (let the LLM decide)."""
    for code, pattern in SCRIPT_RANGES:
        if pattern.search(text):
            return code
    if all(ord(ch) < 128 for ch in text):
        words = set(re.findall(r"[a-z]+", text.lower()))
        if words & ROMANIZED_INDIC_WORDS:
            return None
        return "en"
    return None


MARATHI_WORDS = {"आहे", "आहेत", "नाही", "आणि", "काय", "मला", "तुम्ही", "तुमच्या", "माझ्या", "कसे", "करा", "सांगा", "मध्ये", "होते", "केले", "पण"}
HINDI_WORDS = {"है", "हैं", "नहीं", "और", "क्या", "मुझे", "आप", "आपके", "मेरे", "कैसे", "करें", "बताओ", "बताइए", "में", "के", "की", "का", "था", "लेकिन"}


def guess_devanagari_language(text: str) -> str:
    """Tells Hindi from Marathi by common function words; the letter ळ is frequent in Marathi only.
    Returns "hi" on a tie, since Hindi is the more common of the two."""
    words = re.findall(r"[ऀ-ॿ]+", text)
    marathi = sum(word in MARATHI_WORDS or word.endswith(("च्या", "मध्ये")) for word in words) + text.count("ळ")
    hindi = sum(word in HINDI_WORDS for word in words)
    return "mr" if marathi > hindi else "hi"
