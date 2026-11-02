
# Interview Project Prep Brief

**How to use:** Put this file in the project folder (or its parent), open Claude Code there, and say:
`Read interview-project-prep.md and start with Step 0.`
Do one project at a time. Add `interview-prep/` to `.gitignore`.

---

## Context (for Claude Code)

I am a final-year IT student. This is my first interview ever: Capgemini Software Engineer / Analyst, virtual, 15 to 25 minutes, technical and HR in one round. The interviewer will likely ask about 2 of my 3 projects, may ask for a screen-share demo, and will cross-question me. I do not feel confident about my projects. Goal: understand each project well enough to pitch it in 60 seconds, demo it, and handle follow-up questions honestly.

My projects:

1. RAG project (live, I will demo it). Priority: 50% of my time.
2. Next.js project. Priority: 30%.
3. Research project (half finished, still worth presenting). Priority: 20%.

## Rules for you

1. **Read the real code first**: README, config, dependencies, main files, git log. Do not guess.
2. **Never invent** features, metrics, results, or challenges. If you cannot verify something, write `UNVERIFIED - ask user` and ask me.
3. Use simple language and short sentences. Offer a deeper explanation only when I ask.
4. **Do not change my source code.** Write all outputs to `interview-prep/` in this project.
5. **Teach me, do not just give answers.** After each step, ask me to explain it back in my own words and correct me.
6. If parts of the project were written with AI help, list them and tell me which ones I must be able to explain. I will say so honestly in the interview.
7. After each step, stop and wait for me.

## Step 0: Setup

Ask me: (a) which project this is, (b) the interview date, (c) what I remember about building it (my role, what was hard). Detect the project type: RAG, Next.js, research, or other, and use the matching module in Step 4.

## Step 1: Understand the project -> `interview-prep/01-overview.md`

- Plain-English summary: the problem, who it is for, and what it does.
- Main features.
- Tech stack, with one line on why each tool was likely chosen. Mark guesses as UNVERIFIED and ask me.
- Folder and file map: what each important file does.
- **One request traced end to end**, naming files and functions (screen -> code -> data -> screen).
- How to run it: setup commands and environment variables (names only, no secrets).
- Known weak points and limitations an interviewer could probe.
- "Concepts this project touches" (for example OOP, SQL/DBMS, REST, authentication) so I can link them to fundamentals questions.

## Step 2: Pitch -> `interview-prep/02-pitch.md`

- 30-second, 60-second, and 2-minute versions.
- Structure: problem -> what I built -> how -> my role -> one challenge -> what I would improve.
- **One challenge story** (situation, what I did, result, what I learned). Base it on evidence in the repo or git history, or on what I tell you. Do not make one up.
- A line for "which part did you personally build?" (ask me, do not assume).

## Step 3: Cross-questions -> `interview-prep/03-cross-questions.md`

Write 25 likely interview questions with model answers grounded in THIS code. Groups:

- Basics ("explain your project")
- Design choices ("why this and not that?")
- Scale ("what if 1,000 users?")
- Bugs and testing
- Security and data
- "Which part did you write?"
- Improvements
  Add 5 "I don't know" answer templates, for example "I'm not sure, but I would check X."

## Step 4: Module for this project type

### RAG module -> `04-demo-script.md`

- Pipeline in plain words: ingest -> chunk -> embed -> store -> retrieve -> generate with citations.
- Exact values and reasons: chunk size and overlap, embedding model, vector store, top-k, prompt, LLM.
- How hallucination is reduced. What happens when the answer is not in the documents.
- How quality was checked. If it was not, suggest 10 test questions with expected answers.
- Cost, latency, and failure cases.
- **Demo script:** 3 queries (one simple, one needing several documents, one the system should refuse), with expected outputs and what to say while clicking.
- **Backup plan:** a screenshot set or a short recording in case the live app or network fails.
- **Pre-demo checklist:** app running, API keys valid, internet tested, sample documents loaded.

### Next.js module

- Rendering used (SSR, SSG, CSR) and where. Routing (app or pages router) and API routes.
- Data fetching, state management, authentication and sessions, database, environment variables, deployment.
- React basics through my own code: hooks, state vs props, virtual DOM.
- One feature traced end to end.
- Performance or security issues in the code.

### Research module

- Research question, method, data, baseline, metrics.
- **Results so far: only what is real.** Label early results as preliminary.
- Limitations and next steps.
- How to present it as honest work in progress (about 30 seconds in my introduction, 2 minutes if asked).
- If code or notes are missing, ask me for the paper, notebook, or results instead of guessing.

## Step 5: Mock cross-questioning (interactive)

Act as a Capgemini interviewer.

1. Ask **one question at a time** and wait for my answer.
2. Score my answer 1 to 5 on clarity, correctness, and depth.
3. Show a better version, and what I should add.
4. Ask the follow-up an interviewer would ask.
5. Go from easy to hard. Include some questions I cannot answer, to practise saying so calmly.
6. After 10 questions, write my weak topics to `interview-prep/05-weak-topics.md` and suggest what to study.

## Step 6: One-page cheat sheet -> `interview-prep/06-cheatsheet.md`

My 60-second pitch, the tech stack and reasons, 5 key facts or numbers (verified only), my challenge story, and one-line answers to the top 10 questions.

## Suggested order

Step 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6. Do the RAG project first, then Next.js, then the research project.
