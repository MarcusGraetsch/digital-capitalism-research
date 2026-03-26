---
url: https://towardsdatascience.com/17-advanced-rag-techniques-to-turn-your-rag-app-prototype-into-a-production-ready-solution-5a048e36cdc8
title: 17 (Advanced) RAG Techniques to Turn Your LLM App Prototype into a Production-Ready Solution | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:01:50.037167
word_count: 6070
paywall: False
cleaned_at: 2026-03-01T14:19:15.454215
cleaned_by: llm
quality_score: 8
---

url: https://towardsdatascience.com/17-advanced-rag-techniques-to-turn-your-rag-app-prototype-into-a-production-ready-solution-5a048e36cdc8
title: 17 (Advanced) RAG Techniques to Turn Your LLM App Prototype into a Production-Ready Solution | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:01:50.037167
word_count: 6070
paywall: False
---

# 17 (Advanced) RAG Techniques to Turn Your LLM App Prototype into a Production-Ready Solution | Towards Data Science






---

Artificial Intelligence

17 (Advanced) RAG Techniques to Turn Your LLM App Prototype into a Production-Ready Solution

A collection of RAG techniques to help you develop your RAG app into something robust that will last

Dominik Polzer

Jun 26, 2024

30 min read

Share

The speed at which people are evolving into GenAI experts these days is remarkable. And each of them proclaims that GenAI will bring the next industrial evolution.

It’s a big promise, but I agree, I think it’s true this time. AI will finally revolutionize the way we work and live. I can’t imagine sliding into the next

AI winter

.

LLMs and multimodal models are simply too useful and "relatively" easy to implement into existing processes. A vector database, a few lines of code to process the raw data, and a few API calls.

That’s it. – At least in theory.

Although it sounds quite straightforward, the real progress in the industry is probably better described by one of

Matt Turck’s recent LinkedIn posts:

2023: "I hope Generative AI doesn’t kill us all!"

2024: "I hope Generative AI goes from proof of concept experiment at my company to small production deployment to read PDFs in the next 12–18 months!"

Matt Turck

Building a Prototype is easy. Turning it into something production-ready is hard.

The following post is for everybody who spent the last month building their first LLM apps and started productizing them. We will look at 17 techniques you should try to mitigate some of the pitfalls along the RAG process and gradually develop your application into a powerful and robust solution that will last.

To understand where we have opportunities to improve the standard RAG process, I will briefly recap what components we need to create a simple RAG app. Feel free to skip this part, to get directly to the

"Advanced" techniques.

Table of Contents

Naive RAG – A Brief Recap

How to make RAG better?

1.RAW data preparation

(1) Preparing (or processing) the data

2. Indexing / Chunking

(2) Chunk Optimization – Sliding Windows / Recursive Structure Aware Splitting / Structure Aware Splitting / Content-Aware Splitting

(3) Enhancing data quality – Abbreviations / technical terms / links

(4) Adding Metadata

(5) Optimization indexing structure – Full Search vs. Approximate Nearest Neighbor, HNSW vs. IVFPQ

(6) Choose the right embedding model

3. Retrieval Optimization – Query Translation / Query Rewriting / Query Extension

(7) Query Expansion with generated answers – HyDE and co.

(8) Multiple System Prompts

(9) Query Routing

(10) Hybrid Search

4. Post-Retrieval

(11) Sentence Window Retrieval

(12) Auto-merging Retriever (aka Parent Document Retriever)

5. Generation / Agents

(13) Picking the right LLM and provider – Open Source vs. Closed Source, Services vs Self-Hosted, Small model vs. huge model

(14) Agents

6. Evaluation – Evaluate our RAG system

(15) LLM-as-a-judge

(16) RAGAs

(17) Continued data collection from the app and users

What do we need for a production-ready solution?

That LLMs are getting more and more powerful is one thing, but if we are honest with each other, the bigger lever to improve the RAG performance is again the less fancy stuff:

Data quality – data preparation – data processing.

During the runtime of the app or when preparing the raw data, we process data, classify data and gain insights from the data to steer the outcome in the right direction.

It is illusory to simply wait for bigger and bigger models in the hope that they will solve all our problems without us working on our data and processes.

Maybe one day we’ll get to the point where we feed all the crappy raw data into a single model and it somehow makes something useful out of it. But even if we reach that point, I doubt it will make sense from a cost and performance perspective.

The RAG concept has come to stay.

In his talk at

Sequoia Capital’s AI Ascent

, Andrew Ng showed how GPT-3.5 can beat far more powerful models by using an agent-based approach. The image below compares the accuracy of GPT-4 (zero-shot prompting) to GPT-3.5 + agentic workflow.

I explain the idea behind Agents in one of my recent articles. You can find it

here

.

Coding Benchmark (HumanEval) – Image by the author (data by [

Andre Ng, 2024

])

With all these capabilities that the big Transformer models have brought us, AGI (Artificial General Intelligence) is no longer just something for science fiction films.

At the same time, I doubt that we will rea