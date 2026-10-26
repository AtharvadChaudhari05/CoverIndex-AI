from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

from policy_rag import agent
from policy_rag import server as server_module
from policy_rag.agent import (
    FALLBACK_PREFIX,
    FIXED_TRANSLATIONS,
    answer_query,
    classify_conversational,
    normalize_fallback_answer,
    resolve_query_scope,
)
from policy_rag.utils import guess_devanagari_language
from policy_rag.web import extract_text_blocks, is_public_http_url, read_pages, select_relevant_text

HISTORY = [
    {"role": "user", "content": "mala travel insurance policy baddal sanga"},
    {"role": "assistant", "content": "### प्रवास विमा कव्हरेज\n1. **पर्यटन व्यत्यय**: खर्च परतावा दिला जातो."},
]


def _empty_index() -> MagicMock:
    index = MagicMock()
    index.records = []
    index.search.return_value = []
    return index


class ConversationalClassifierTests(unittest.TestCase):
    def test_small_talk(self) -> None:
        for message in ["hello", "Hi there!", "thanks, that helped", "Thank you so much", "नमस्ते", "धन्यवाद", "bye"]:
            with self.subTest(message=message):
                self.assertEqual(classify_conversational(message, None), "small_talk")

    def test_greeting_followed_by_a_question_is_not_small_talk(self) -> None:
        self.assertIsNone(classify_conversational("hi what is the waiting period", None))
        self.assertIsNone(classify_conversational("thanks, what about claims?", None))

    def test_requests_about_an_earlier_reply(self) -> None:
        for message in [
            "now give me the answer of the above question in english",
            "translate your last answer to english",
            "make it shorter",
            "explain that again in simple words",
            "हे इंग्रजी मध्ये सांगा",
        ]:
            with self.subTest(message=message):
                self.assertEqual(classify_conversational(message, HISTORY), "followup")

    def test_followup_needs_an_earlier_reply(self) -> None:
        self.assertIsNone(classify_conversational("translate your last answer to english", None))

    def test_new_question_about_the_same_topic_uses_normal_pipeline(self) -> None:
        self.assertIsNone(classify_conversational("what is the waiting period in this policy?", HISTORY))


class ScopeTests(unittest.TestCase):
    def test_llm_widens_scope_when_no_keyword_matches(self) -> None:
        with patch.object(agent, "is_insurance_related_by_llm", return_value=True) as llm_check:
            scope, reason = resolve_query_scope("my flight got delayed, will I get money back")
        self.assertEqual(scope, "insurance")
        self.assertIn("LLM", reason)
        llm_check.assert_called_once()

    def test_clear_off_topic_terms_skip_the_llm(self) -> None:
        with patch.object(agent, "is_insurance_related_by_llm") as llm_check:
            scope, _ = resolve_query_scope("explain java oop")
        self.assertEqual(scope, "out_of_scope")
        llm_check.assert_not_called()

    def test_llm_can_keep_the_refusal(self) -> None:
        with patch.object(agent, "is_insurance_related_by_llm", return_value=False):
            scope, _ = resolve_query_scope("what is the capital of France")
        self.assertEqual(scope, "out_of_scope")


class AutomaticWebSearchTests(unittest.TestCase):
    def test_searches_web_when_documents_have_no_answer(self) -> None:
        web_snippet = "Source [https://example.com/travel]: Travel delay cover - Pays for delays over 6 hours."

        def fake_groq(query, snippets, mode="insurance_rag", chat_history=None, answer_language="auto"):
            return "Travel delay cover pays after 6 hours." if mode == "fallback_confirmed" else None

        with patch.object(agent, "call_groq_rag", side_effect=fake_groq), \
                patch.object(agent, "call_gemini_rag", return_value=None), \
                patch.object(agent, "perform_internet_search", return_value=[web_snippet]) as search:
            result = answer_query(
                _empty_index(), "Is flight delay covered?", search_query="Is flight delay covered?",
                scope=("insurance", "test"),
            )
        search.assert_called_once_with("Is flight delay covered?")
        self.assertTrue(result.answer.startswith(FALLBACK_PREFIX))
        self.assertIn("https://example.com/travel", result.answer)
        self.assertTrue(any("searching the web automatically" in step for step in result.trace))
        self.assertFalse(any("insufficient retrieved context" in step for step in result.trace))

    def test_no_answer_anywhere_returns_message_without_sources(self) -> None:
        with patch.object(agent, "call_groq_rag", return_value=None), \
                patch.object(agent, "call_gemini_rag", return_value=None), \
                patch.object(agent, "perform_internet_search", return_value=[]):
            result = answer_query(_empty_index(), "Is flight delay covered?", search_query="Is flight delay covered?", scope=("insurance", "test"))
        self.assertEqual(result.answer, agent.NO_ANSWER_MESSAGE)
        self.assertEqual(result.sources, [])

    def test_generator_receives_chat_history(self) -> None:
        with patch.object(agent, "call_groq_rag", return_value=None) as groq, \
                patch.object(agent, "call_gemini_rag", return_value=None), \
                patch.object(agent, "perform_internet_search", return_value=[]):
            answer_query(_empty_index(), "what about its waiting period?", chat_history=HISTORY, search_query="waiting period", scope=("insurance", "test"))
        self.assertEqual(groq.call_args_list[0].kwargs["chat_history"], HISTORY)

    def test_groq_no_context_verdict_skips_gemini(self) -> None:
        # Gemini once spent over 7 minutes retrying a question that Groq had already answered with [NO_CONTEXT]
        def fake_groq(query, snippets, mode="insurance_rag", chat_history=None, answer_language="auto"):
            return "Web answer." if mode == "fallback_confirmed" else "[NO_CONTEXT]"

        with patch.object(agent, "call_groq_rag", side_effect=fake_groq), \
                patch.object(agent, "call_gemini_rag") as gemini, \
                patch.object(agent, "perform_internet_search", return_value=[]):
            answer_query(_empty_index(), "LIC claim ratio 2025", search_query="LIC claim ratio 2025", scope=("insurance", "test"))
        gemini.assert_not_called()

    def test_web_search_tries_the_next_engine(self) -> None:
        fake_ddgs = MagicMock()
        fake_ddgs.return_value.text.side_effect = [Exception("No results found."), [{"href": "https://example.com", "title": "T", "body": "B"}]]
        with patch("ddgs.DDGS", fake_ddgs), patch.object(agent, "read_pages", return_value=["page"]) as read:
            self.assertEqual(agent.perform_internet_search("query"), ["page"])
        backends = [call.kwargs["backend"] for call in fake_ddgs.return_value.text.call_args_list]
        self.assertEqual(backends, ["yahoo", "bing"])
        read.assert_called_once()

    def test_web_answer_prefix_follows_answer_language(self) -> None:
        hindi_prefix = FIXED_TRANSLATIONS[FALLBACK_PREFIX]["hi"]
        self.assertEqual(normalize_fallback_answer("उत्तर", hindi_prefix), f"{hindi_prefix} उत्तर")


class AskEndpointConversationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.PolicyLensHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/ask"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _ask(self, payload: dict) -> dict:
        request = urllib.request.Request(
            self.url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())

    def test_followup_is_answered_from_the_conversation(self) -> None:
        with patch.object(server_module, "ensure_index", return_value=None), \
                patch.object(server_module, "rewrite_query_with_history") as rewrite, \
                patch.object(server_module, "answer_query") as rag, \
                patch.object(agent, "_call_llm", return_value="Travel insurance covers trip interruption.") as llm:
            body = self._ask({"query": "now give me the answer of the above question in english", "session_id": "conv", "chat_history": HISTORY})
        self.assertEqual(body["assistant_mode"], "conversational")
        self.assertEqual(body["answer"], "Travel insurance covers trip interruption.")
        rewrite.assert_not_called()
        rag.assert_not_called()
        sent_messages = llm.call_args.args[0]
        self.assertEqual(sent_messages[1:3], HISTORY)

    def test_greeting_works_without_llm(self) -> None:
        with patch.object(server_module, "ensure_index", return_value=None), \
                patch.object(agent, "_call_llm", return_value=None):
            body = self._ask({"query": "नमस्ते", "session_id": "greet"})
        self.assertEqual(body["assistant_mode"], "conversational")
        self.assertEqual(body["answer"], FIXED_TRANSLATIONS[agent.GREETING_MESSAGE]["hi"])


class WebPageReadingTests(unittest.TestCase):
    def test_extracts_article_text_and_skips_page_chrome(self) -> None:
        html = """<html><head><script>var tracking = 1;</script></head><body>
            <nav>Home About Contact Login and other menu links that are long enough to count</nav>
            <article><p>Travel insurance usually pays for flight delays longer than six hours, up to a fixed limit.</p>
            <p>Lost baggage claims need a property irregularity report from the airline and original receipts.</p></article>
            <footer>Copyright notice with enough characters to pass the length filter easily</footer></body></html>"""
        blocks = extract_text_blocks(html)
        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0].startswith("Travel insurance usually pays"))

    def test_selects_blocks_relevant_to_the_query(self) -> None:
        blocks = ["Our office is open on weekdays.", "Flight delay cover pays after six hours of delay.", "Contact us by email."]
        self.assertEqual(select_relevant_text(blocks, "flight delay cover"), "Flight delay cover pays after six hours of delay.")

    def test_rejects_internal_and_non_http_urls(self) -> None:
        for url in ["http://127.0.0.1:8000/", "http://localhost/admin", "http://10.0.0.5/", "file:///etc/passwd", "ftp://example.com/"]:
            with self.subTest(url=url):
                self.assertFalse(is_public_http_url(url))

    def test_unreadable_page_falls_back_to_snippet(self) -> None:
        results = [{"href": "https://example.com/a", "title": "A", "body": "Snippet text about delays."}]
        with patch("policy_rag.web.fetch_page_text", return_value=[]):
            sources = read_pages(results, "delays")
        self.assertEqual(sources, ["Source [https://example.com/a]: A - Snippet text about delays."])


class DevanagariLanguageTests(unittest.TestCase):
    def test_tells_marathi_from_hindi(self) -> None:
        self.assertEqual(guess_devanagari_language("मला प्रवास विमा बद्दल सांगा"), "mr")
        self.assertEqual(guess_devanagari_language("या पॉलिसीमध्ये काय आहे?"), "mr")
        self.assertEqual(guess_devanagari_language("मुझे यात्रा बीमा के बारे में बताओ"), "hi")
        self.assertEqual(guess_devanagari_language("इस पॉलिसी में क्या है?"), "hi")


if __name__ == "__main__":
    unittest.main()
