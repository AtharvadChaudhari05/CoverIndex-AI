# CoverIndex AI 🛡️

**Your Personal Explainable AI Insurance Advisor**

Welcome to CoverIndex AI! Have you ever tried reading a 100-page insurance policy document? It's filled with confusing jargon, hidden clauses, and tiny text. CoverIndex AI was built to solve this exact problem. 

This project is a smart assistant that reads your complex insurance PDFs for you. You just ask it a question in plain English (like *"What are my maternity benefits?"* or *"Should I take this travel policy?"*), and it instantly gives you a clear, easy-to-understand answer with exact citations pointing to the page it found the information on.

---

## 📖 The Story of Our Project: From Start to Finish

We started this Capstone project with a simple goal: make insurance policies easy to understand. 

**Phase 1: The Basics**
Initially, we built a basic AI that could read documents, but we quickly realized that standard AI tools (like Vector Databases) were slow, expensive, and often "hallucinated" (made up fake answers). So, we scrapped the standard approach and built a custom **Vectorless Page-Indexed System**. Instead of complex math, our system acts like a super-smart `CTRL+F`, instantly finding the exact pages related to your query.

**Phase 2: A Beautiful Experience**
A great AI needs a great interface. We built a stunning, modern, glassmorphic dark-mode web application from scratch using HTML, CSS, and Vanilla JavaScript. We added dynamic typing effects, smooth animations, and interactive source citations.

**Phase 3: Chat History & Search**
We realized users need to save their conversations. We added a fully functioning Chat History sidebar that saves your sessions locally. We also built a "Search Conversations" feature so you can instantly filter through your past chats to find that one specific policy detail you asked about months ago.

**Phase 4: The Explainable AI Advisor & Internet Fallback**
Finally, we gave the AI a brain upgrade. We implemented an **Explainable AI Advisor mode**. If you ask for a recommendation (e.g., *"Should I take this policy?"*), it doesn't just say yes or no. It structures the answer into three stages: Policy Overview, Benefits/Exclusions, and a Final Recommendation explaining exactly *why*. 
Furthermore, if you ask a valid insurance question that isn't found in your uploaded documents, the AI won't just fail—it will politely ask you if you'd like it to search the live Internet, seamlessly blending document data with live web searches!

---

## ⚙️ How It Works (Technical, but in Human Language)

When you ask CoverIndex AI a question, here is what happens behind the scenes in a fraction of a second:

1. **Understanding the Query (Routing):** The AI reads your question and figures out what you want. Is it a question about a claim? Are you asking for a recommendation? Are you asking about an HDFC policy or an SBI policy?
2. **Vectorless Search (Retrieval):** The system scans through the thousands of pages in your uploaded PDFs. It scores pages based on how well they match your question using a custom lexical scoring algorithm. It grabs the top most relevant pages.
3. **Reading the Pages (Context):** The system takes those specific pages and hands them to a powerful AI model (using Groq and Gemini).
4. **Writing the Answer (Generation):** The AI reads the pages and generates a structured, easy-to-read response (using 5 to 7 numbered points). It is strictly forbidden from making things up. 
5. **Citations:** The system automatically attaches the exact document name and page number to the bottom of the answer so you can verify the truth yourself.
6. **Internet Fallback:** If the AI looks at the pages and realizes the answer isn't there, it triggers a fallback. It searches the live web (using DuckDuckGo), reads the websites, and gives you the answer with clickable web links as its sources!

---

## 📁 File Structure

Here is how the code is organized:

- **`/public`**: The Frontend. This folder contains the face of the application. 
  - `index.html`: The structure of the website.
  - `styles.css`: All the beautiful colors, glassmorphism effects, and animations.
  - `app.js`: The brain of the website (handles sending messages, saving chat history, and searching old chats).
- **`/policy_rag`**: The Backend (Python). This is the engine room.
  - `server.py`: The web server that receives messages from the frontend and sends back answers.
  - `agent.py`: The AI logic. It decides if a query is insurance-related, searches the documents, talks to Groq/Gemini, and handles the Internet fallback.
  - `index.py`: The system that chops PDFs into pages and creates our custom search index.
- **`/prompts`**: The instruction manuals for the AI. This contains the strict rules (like the 3-stage recommendation format) that tell the AI how to behave.
- **`/Policy Documents`**: The folder where you drop all the raw insurance PDFs you want the AI to learn.
- **`worker.js`**: The Cloudflare configuration that helps deploy our frontend to the global edge network.

---

## 🚀 How to Run Locally

If you want to run this project on your own computer instead of the live website:

1. **Install Dependencies:** Open your terminal and run:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the Backend Engine:**
   ```bash
   python app.py
   ```
3. **Open the App:** Open your web browser and go to `http://localhost:8000`. You're ready to chat!
