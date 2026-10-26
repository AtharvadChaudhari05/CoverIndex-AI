# Multilingual Feature: Implementation Plan

## Purpose

This document explains how we will add three multilingual features to CoverIndex AI:

1. The user selects the answer language.
2. The app reads answers aloud.
3. Non-English queries work reliably, and English queries run faster.

## Current State

CoverIndex AI already has some multilingual support:

- `rewrite_query_with_history` in `policy_rag/agent.py` translates a non-English query to English. The retriever then searches the English text.
- The system prompt tells the model to answer in the language of the query.
- Voice input supports six languages: English, Hindi, Marathi, Tamil, Telugu, and Bengali.
- `translate_to_user_language` translates the refusal message and the internet-search question.

## Problem

The `/api/ask` handler in `policy_rag/server.py` has a bug. It runs two checks on the original query before it translates the query:

- `route_query` finds the insurer and the intent.
- `classify_query_scope` decides if the query is about insurance.

Both checks look for English keywords only. A Hindi or Marathi query contains no English keywords. Thus the server can classify a valid insurance question as out of scope. The server then sends a refusal, and it sends the refusal in English.

A second problem is speed. The server sends every query to the LLM for a rewrite, even a plain English query with no chat history. That call adds time and cost, but it does not change the query.

## Language Codes

All parts of the system use one set of codes:

| Code     | Language                                 |
| -------- | ---------------------------------------- |
| `auto` | Same language as the query (the default) |
| `en`   | English                                  |
| `hi`   | Hindi                                    |
| `mr`   | Marathi                                  |
| `ta`   | Tamil                                    |
| `te`   | Telugu                                   |
| `bn`   | Bengali                                  |

## Step 1: Fix the Query Order (Backend)

1. Add `detect_script_language(text)` to `policy_rag/utils.py`. This function examines the Unicode ranges of the characters. It does not call an LLM. 
   - Devanagari characters return `deva`. Hindi and Marathi both use this script, so the LLM decides between them.
   - Bengali, Tamil, and Telugu characters return `bn`, `ta`, and `te`.
   - Plain ASCII text returns `en`.
   - Other text returns `None`, and the LLM decides.
   - Plain ASCII text that contains a common romanized Hindi or Marathi word (for example `kya`, `mein`, `hai`, `ahe`) returns `None`. Thus a Hinglish query still goes to the LLM rewrite.
2. Change `rewrite_query_with_history`. If the query is English and there is no chat history, the function returns the query unchanged. It does not call the LLM.
3. Change `/api/ask`. The handler rewrites the query first. Then it runs `route_query` and `classify_query_scope` on the English text.
4. Add an optional `search_query` parameter to `answer_query`. The server sends the rewritten query, so `answer_query` does not rewrite it a second time. Other callers do not change.
5. Translate the server-side refusal with `translate_to_user_language`. The internet-search question uses this function already.
6. Store fixed translations of the refusal and the internet-search question for the six languages. `translate_to_user_language` uses a stored translation when one exists. It calls the LLM only for other text or other languages.
7. Replace the retired model `gemini-1.5-flash` with `gemini-3.8-flash` in `policy_rag/agent.py`. Google retired the Gemini 1.5 and 2.5 Flash models, so the Gemini fallback did not work. The `GEMINI_MODEL` environment variable overrides the model name.

## Step 2: Let the User Select the Answer Language

### Backend

1. `/api/ask` accepts a new optional field, `answer_language`. The default value is `auto`. The server rejects values that are not in the language table.
2. `answer_query` sends the value to `build_rag_messages`. If the value is not `auto`, the prompt gets one more line: "Respond in {language name}."
3. Change the rule in `prompts/system_prompt_insurance_rag.md`. The new rule is: "Answer in the same language as the user's query, unless the prompt gives a response language."
4. Add an optional `target_language` parameter to `translate_to_user_language`.
   - If the caller gives a target, the function translates into that language.
   - If the caller gives no target, the function detects the language of the query, as it does now.
   - If the target is English, the function returns the text unchanged.
5. Fix a related bug in `call_gemini_rag`. The function builds its prompt from `messages[1]`. When chat history exists, `messages[1]` is an old message, not the current question. The fix uses `messages[-1]`.

### Frontend

1. Add an "Answer in" dropdown in `public/index.html`, next to the voice-language dropdown.
2. `public/app.js` saves the selection in `localStorage`, the same way it saves the voice language.
3. `public/app.js` sends `answer_language` in the body of the `/api/ask` request.

## Step 3: Read Answers Aloud (Frontend)

1. Add a speaker button to each assistant message in `public/app.js`.
2. When the user clicks the button, the browser speaks the answer with `window.speechSynthesis`.
3. The app sets the voice language from the answer language. For example, `hi` becomes `hi-IN`.
4. Before the browser speaks, the app removes Markdown symbols, citation markers, and the `[NO_CONTEXT]` tag.
5. A second click stops the speech. A new message also stops the speech.
6. If the browser has no voice for the language, the app shows a notice. It does not read the answer in the wrong voice.

## Step 3b: Natural Voices with Sarvam AI

The browser voices on Linux (espeak) are too robotic to understand. Thus the server generates the audio:

1. `policy_rag/tts.py` sends the text to the Sarvam AI text-to-speech API (model `bulbul:v3`, speaker `priya`). It returns MP3 audio.
2. The server keeps the last 64 audio clips in memory. A replay of the same answer does not call Sarvam again.
3. The new endpoint `POST /api/tts` takes `{"text", "language"}`. The text is at most 2,500 characters. The language is one of `en-IN`, `hi-IN`, `mr-IN`, `ta-IN`, `te-IN`, `bn-IN`.
4. The speaker button splits the answer into chunks of at most 1,200 characters. It plays each chunk in order, and it gets the next chunk while the current chunk plays.
5. If `SARVAM_API_KEY` is not set, the endpoint returns 503. The button then uses the browser voices.
6. The environment variables `SARVAM_TTS_MODEL` and `SARVAM_TTS_SPEAKER` change the model and the voice.

## Step 4: Tests

The new tests go in `tests/test_multilingual.py`. They use `unittest` and `unittest.mock.patch`, like the current tests.

| Test                                                        | Expected result                                |
| ----------------------------------------------------------- | ---------------------------------------------- |
| `detect_script_language` on text in each script           | The function returns the code for that script. |
| A Hindi insurance query, with the rewrite mocked to English | The scope check returns `insurance`.         |
| An English query with no chat history                       | The LLM rewrite is not called.                 |
| `build_rag_messages` with `answer_language="mr"`        | The prompt contains "Respond in Marathi."      |

Note: 11 of the 12 current tests in `tests/test_prompt_guardrails.py` fail before this work starts. The tests expect old prompt text. This plan does not fix those tests.

## Not in This Plan

- **Translated interface text.** Buttons and labels stay in English. A later change can add one JSON file for each language, for example `public/i18n/hi.json`.
- **Non-English search.** The retriever and the stemmer stay English-only. The system always searches the English translation of the query.

## Verification

1. Run the tests: `uv run python -m unittest discover tests`
2. Start the server with `./app.py`. Then send these requests with `curl`:
   - A Hindi query, for example "मेरी HDFC पॉलिसी में क्या कवर है?". The server returns an answer with sources, not a refusal.
   - An English query with `"answer_language": "mr"`. The server returns the answer in Marathi.
   - An English query with no chat history. The `trace` field shows no rewrite step.
3. In the browser, select "Answer in: Hindi" and ask a question in English. Click the speaker button. The browser speaks the answer in a Hindi voice.

## Progress

| Step | Status |
| --- | --- |
| Step 1: query order, script detection, stored translations, Gemini model | Done. Unit tests and live `curl` checks pass. |
| Step 2: answer language (backend and frontend) | Done. Live `curl` check returns Marathi. |
| Step 3: read answers aloud | Done. In Chrome, the button, play/stop toggle, and restored chats work. Audio is not confirmed, because the test browser on Linux has no speech voices. The app shows a notice in that case. |
| Step 3b: Sarvam AI voices | Done. All six languages return audio. In the browser, a click plays the Hindi answer and a second click stops it. |
| Step 4: tests in `tests/test_multilingual.py` | Done. 19 tests pass. |
| Gemini fallback with `gemini-3.8-flash` | The model name is accepted. A full answer is not confirmed, because the API returned "high demand" and "quota exceeded" errors. |
