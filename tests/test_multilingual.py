from __future__ import annotations

import base64
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

from policy_rag import server as server_module
from policy_rag import tts as tts_module

from policy_rag.agent import (
    FIXED_TRANSLATIONS,
    INTERNET_SEARCH_PROMPT_MESSAGE,
    OUT_OF_SCOPE_REFUSAL_MESSAGE,
    build_rag_messages,
    classify_query_scope,
    is_confirmation_query,
    rewrite_query_with_history,
    route_query,
    translate_to_user_language,
)
from policy_rag.models import QueryResult
from policy_rag.utils import detect_script_language


class ScriptDetectionTests(unittest.TestCase):
    def test_detects_each_script(self) -> None:
        cases = {
            "What is the waiting period?": "en",
            "मेरी पॉलिसी में क्या कवर है?": "deva",
            "विमा पॉलिसीमध्ये काय समाविष्ट आहे?": "deva",
            "পলিসিতে কী কভার করা হয়?": "bn",
            "காப்பீட்டில் என்ன அடங்கும்?": "ta",
            "బీమాలో ఏమి కవర్ అవుతుంది?": "te",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(detect_script_language(text), expected)

    def test_romanized_hindi_is_not_treated_as_english(self) -> None:
        self.assertIsNone(detect_script_language("meri policy mein kya cover hai"))
        self.assertIsNone(detect_script_language("majhi policy kay cover karte ahe"))

    def test_unknown_script_returns_none(self) -> None:
        self.assertIsNone(detect_script_language("¿Qué cubre la póliza?"))


class QueryRewriteTests(unittest.TestCase):
    def test_english_query_without_history_skips_llm(self) -> None:
        with patch("groq.Groq") as groq_client:
            result = rewrite_query_with_history("What is the waiting period?", None)
        self.assertEqual(result, "What is the waiting period?")
        groq_client.assert_not_called()

    def test_raw_hindi_query_has_no_english_scope_signal(self) -> None:
        # Why the server must rewrite before the scope check: raw Hindi text matches no English keyword.
        scope, _ = classify_query_scope("मेरी पॉलिसी में प्रतीक्षा अवधि क्या है?")
        self.assertEqual(scope, "out_of_scope")


class AskEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.PolicyLensHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/ask"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _ask(self, payload: dict) -> tuple[int, dict]:
        request = urllib.request.Request(
            self.url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_hindi_insurance_query_is_answered_not_refused(self) -> None:
        # Regression: the server used to run the scope check on the raw Hindi text and refuse it.
        hindi_query = "मेरी HDFC पॉलिसी में प्रतीक्षा अवधि क्या है?"
        english_query = "What is the waiting period in my HDFC policy?"
        fake_result = QueryResult(answer="उत्तर", confidence=0.9, route=route_query(english_query), sources=[], trace=[])
        with patch.object(server_module, "ensure_index", return_value=None), \
                patch.object(server_module, "rewrite_query_with_history", return_value=english_query), \
                patch.object(server_module, "answer_query", return_value=fake_result) as answer_mock:
            status, body = self._ask({"query": hindi_query, "session_id": "hindi-test", "answer_language": "hi"})
        self.assertEqual(status, 200)
        self.assertEqual(body["query_scope"], "insurance")
        self.assertEqual(body["answer"], "उत्तर")
        kwargs = answer_mock.call_args.kwargs
        self.assertEqual(kwargs["search_query"], english_query)
        self.assertEqual(kwargs["answer_language"], "hi")

    def test_unsupported_answer_language_is_rejected(self) -> None:
        with patch.object(server_module, "ensure_index", return_value=None):
            status, body = self._ask({"query": "What is covered?", "answer_language": "xx"})
        self.assertEqual(status, 400)
        self.assertIn("answer_language", body["error"])


class AnswerLanguageTests(unittest.TestCase):
    def test_explicit_answer_language_adds_instruction(self) -> None:
        messages = build_rag_messages("What is covered?", [], answer_language="mr")
        self.assertIn("Respond in Marathi.", messages[-1]["content"])

    def test_auto_answer_language_adds_no_instruction(self) -> None:
        messages = build_rag_messages("What is covered?", [], answer_language="auto")
        self.assertNotIn("Respond in", messages[-1]["content"])

    def test_fixed_messages_use_stored_translation_without_llm(self) -> None:
        with patch("groq.Groq") as groq_client:
            translated = translate_to_user_language(OUT_OF_SCOPE_REFUSAL_MESSAGE, "What is Java?", "hi")
        self.assertEqual(translated, FIXED_TRANSLATIONS[OUT_OF_SCOPE_REFUSAL_MESSAGE]["hi"])
        groq_client.assert_not_called()

    def test_auto_target_resolves_from_unambiguous_script(self) -> None:
        translated = translate_to_user_language(INTERNET_SEARCH_PROMPT_MESSAGE, "காப்பீட்டில் என்ன அடங்கும்?")
        self.assertEqual(translated, FIXED_TRANSLATIONS[INTERNET_SEARCH_PROMPT_MESSAGE]["ta"])

    def test_english_target_returns_text_unchanged(self) -> None:
        self.assertEqual(translate_to_user_language(OUT_OF_SCOPE_REFUSAL_MESSAGE, "What is Java?"), OUT_OF_SCOPE_REFUSAL_MESSAGE)

    def test_every_fixed_message_has_all_languages(self) -> None:
        for message, translations in FIXED_TRANSLATIONS.items():
            with self.subTest(message=message):
                self.assertEqual(set(translations), {"hi", "mr", "ta", "te", "bn"})

    def test_native_confirmation_words(self) -> None:
        for word in ["हाँ", "हो।", "ஆம்", "అవును", "হ্যাঁ", "haan"]:
            with self.subTest(word=word):
                self.assertTrue(is_confirmation_query(word))



class TextToSpeechTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.PolicyLensHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/tts"
        tts_module._cache.clear()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _tts(self, payload: dict) -> tuple[int, bytes, str]:
        request = urllib.request.Request(
            self.url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as error:
            return error.code, error.read(), error.headers.get("Content-Type", "")

    def test_without_key_returns_503_so_client_uses_browser_voices(self) -> None:
        with patch.dict(os.environ, {"SARVAM_API_KEY": ""}):
            status, _, _ = self._tts({"text": "Hello", "language": "en-IN"})
        self.assertEqual(status, 503)

    def test_rejects_unsupported_language_and_oversized_text(self) -> None:
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test-key"}):
            bad_language, _, _ = self._tts({"text": "Hello", "language": "fr-FR"})
            too_long, _, _ = self._tts({"text": "a" * (tts_module.MAX_TTS_CHARS + 1), "language": "en-IN"})
        self.assertEqual(bad_language, 400)
        self.assertEqual(too_long, 400)

    def test_returns_mp3_audio(self) -> None:
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test-key"}), \
                patch.object(server_module, "synthesize_speech", return_value=b"ID3fake-mp3") as synth:
            status, body, content_type = self._tts({"text": "नमस्ते", "language": "hi-IN"})
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "audio/mpeg")
        self.assertEqual(body, b"ID3fake-mp3")
        synth.assert_called_once_with("नमस्ते", "hi-IN")

    def test_repeated_text_is_served_from_cache(self) -> None:
        fake_response = MagicMock()
        fake_response.__enter__.return_value.read.return_value = json.dumps(
            {"audios": [base64.b64encode(b"mp3-bytes").decode()]}
        ).encode()
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test-key"}), \
                patch("policy_rag.tts.urllib.request.urlopen", return_value=fake_response) as urlopen:
            first = tts_module.synthesize_speech("Hello", "en-IN")
            second = tts_module.synthesize_speech("Hello", "en-IN")
        self.assertEqual(first, b"mp3-bytes")
        self.assertEqual(second, b"mp3-bytes")
        self.assertEqual(urlopen.call_count, 1)

    def test_api_error_raises_tts_error(self) -> None:
        error = urllib.error.HTTPError(tts_module.SARVAM_TTS_URL, 429, "Too Many Requests", {}, None)
        error.read = lambda *args: b"quota exceeded"
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test-key"}), \
                patch("policy_rag.tts.urllib.request.urlopen", side_effect=error):
            with self.assertRaises(tts_module.TTSError):
                tts_module.synthesize_speech("Hello", "en-IN")


if __name__ == "__main__":
    unittest.main()
