from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from policy_rag import agent
from policy_rag.agent import DOCUMENT_MISSING_MESSAGE, answer_query, classify_conversational
from policy_rag.index import PageIndex
from policy_rag.models import PageRecord
from policy_rag.utils import token_counts

HISTORY = [
    {"role": "user", "content": "What is the waiting period?"},
    {"role": "assistant", "content": "The waiting period is 30 days. [HDFC Life Click 2 Protect p. 4]"},
]


def _page(file_name: str, page_number: int, text: str, source_dir: str = "uploaded") -> PageRecord:
    return PageRecord(
        doc_id=f"{source_dir}-{file_name}",
        source_name=file_name,
        source_path=f"{source_dir}/{file_name}",
        file_name=file_name,
        insurer="Unknown",
        product="Unknown",
        document_type="policy",
        page_number=page_number,
        title=file_name,
        text=text,
        token_counts=dict(token_counts(text)),
        token_count=len(text.split()),
    )


def _index(records: list[PageRecord]) -> PageIndex:
    return PageIndex(
        records=list(records), signature="test", source_path=Path("."), document_count=1,
        avg_doc_length=10.0, document_frequency={},
    )


class AddDocumentTests(unittest.TestCase):
    def test_uploading_the_same_file_again_replaces_its_pages(self) -> None:
        index = _index([])
        index.add_document([_page("my_policy.pdf", 1, "cover page"), _page("my_policy.pdf", 2, "old dental cover text")])
        index.add_document([_page("my_policy.pdf", 1, "cover page"), _page("my_policy.pdf", 2, "new maternity cover text")])
        self.assertEqual(len(index.records), 2)
        self.assertEqual(index.document_frequency.get("dental", 0), 0)
        self.assertEqual(index.search("maternity", file_name_filter="my_policy.pdf")[0].record.page_number, 2)


class UploadedDocumentAnswerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = _index([])
        self.index.add_document([_page("hdfc_term.pdf", 1, "Term plan with a death benefit of 1 crore.", "policies")])
        self.index.add_document([
            _page("my_policy.pdf", 1, "Star Health Family Floater. Hospitalisation is covered up to 5 lakh."),
            _page("my_policy.pdf", 2, "Maternity expenses are covered after a waiting period of 24 months."),
        ])

    def _answer(self, query: str, file_name: str | None = "my_policy.pdf"):
        with patch.object(agent, "call_groq_rag", return_value="Answer from the PDF. [my_policy.pdf p. 2]") as groq, \
                patch.object(agent, "call_gemini_rag", return_value=None), \
                patch.object(agent, "perform_internet_search", return_value=[]):
            result = answer_query(self.index, query, file_name=file_name, search_query=query, scope=("insurance", "test"))
        return result, groq.call_args.args[1] if groq.called else []

    def test_question_is_answered_only_from_the_uploaded_pdf(self) -> None:
        result, snippets = self._answer("maternity waiting period")
        self.assertTrue(snippets)
        self.assertTrue(all("my_policy.pdf" in snippet for snippet in snippets))
        self.assertEqual(result.sources[0]["page_number"], 2)

    def test_whole_document_question_uses_the_first_pages(self) -> None:
        # "summarize this" shares no keywords with any page, so search alone finds nothing
        result, snippets = self._answer("summarize this")
        self.assertEqual(len(snippets), 2)
        self.assertTrue(any("using its first 2 pages" in step for step in result.trace))
        self.assertFalse(any("searching the web" in step for step in result.trace))

    def test_missing_upload_asks_the_user_to_attach_it_again(self) -> None:
        result, snippets = self._answer("maternity waiting period", file_name="lost_after_restart.pdf")
        self.assertEqual(result.answer, DOCUMENT_MISSING_MESSAGE)
        self.assertEqual(result.sources, [])
        self.assertEqual(snippets, [])


class DocumentFollowupTests(unittest.TestCase):
    def test_summarizing_the_document_is_not_a_followup(self) -> None:
        self.assertIsNone(classify_conversational("summarize this document", HISTORY, file_name="my_policy.pdf"))

    def test_summarizing_the_last_answer_is_still_a_followup(self) -> None:
        self.assertEqual(classify_conversational("summarize your last answer", HISTORY, file_name="my_policy.pdf"), "followup")


if __name__ == "__main__":
    unittest.main()
