---
url: https://techcrunch.com/2024/05/04/why-rag-wont-solve-generative-ais-hallucination-problem/
title: Why RAG won't solve generative AI's hallucination problem | TechCrunch
domain: techcrunch.com
category: aigen
date_scanned: 2026-03-01T10:00:00.397174
word_count: 1255
paywall: True
cleaned_at: 2026-03-01T14:19:02.118767
cleaned_by: llm
quality_score: 8
---

url: https://techcrunch.com/2024/05/04/why-rag-wont-solve-generative-ais-hallucination-problem/
title: Why RAG won't solve generative AI's hallucination problem | TechCrunch
domain: techcrunch.com
category: aigen
date_scanned: 2026-03-01T10:00:00.397174
word_count: 1255
paywall: True
---

# Why RAG won't solve generative AI's hallucination problem | TechCrunch






---

Hallucinations — the lies generative AI models tell, basically — are a big problem for businesses looking to integrate the technology into their operations.

Because models have no real intelligence and are

simply predicting words, images, speech, music and other data according to a private schema

, they sometimes get it wrong. Very wrong. In a recent piece in The Wall Street Journal, a

source


As I wrote a while ago,

hallucinations

may be an unsolvable problem with today’s transformer-based model architectures. But a number of generative AI vendors suggest that they

can

be done away with, more or less, through a technical approach called retrieval augmented generation, or RAG.

Here’s how one vendor, Squirro,

pitches it

:

At the core of the offering is the concept of Retrieval Augmented LLMs or Retrieval Augmented Generation (RAG) embedded in the solution … [our generative AI] is unique in its promise of zero hallucinations. Every piece of information it generates is traceable to a source, ensuring credibility.

Here’s a

similar pitch

from SiftHub:

Using RAG technology and fine-tuned large language models with industry-specific knowledge training, SiftHub allows companies to generate personalized responses with zero hallucinations. This guarantees increased transparency and reduced risk and inspires absolute trust to use AI for all their needs.

RAG was pioneered by data scientist Patrick Lewis, researcher at Meta and University College London, and lead author of the 2020

paper


“When you’re interacting with a generative AI model like

ChatGPT

or

Llama

and you ask a question, the default is for the model to answer from its ‘parametric memory’ — i.e., from the knowledge that’s stored in its parameters as a result of training on massive data from the web,” David Wadden, a research scientist at AI2, the AI-focused research division of the nonprofit Allen Institute, explained. “But, just like you’re likely to give more accurate answers if you have a reference [like a book or a file] in front of you, the same is true in some cases for models.”

Techcrunch event

Disrupt 2026: The tech ecosystem, all in one room

Your next round. Your next hire. Your next breakout opportunity.

Find it at TechCrunch Disrupt 2026, where 10,000+ founders, investors, and tech leaders gather for three days of 250+ tactical sessions, powerful introductions, and market-defining innovation. Register now to save up to $400.

Save up to $300 or 30% to TechCrunch Founder Summit

1,000+

founders

and investors come together at

TechCrunch Founder Summit 2026

for a full day focused on growth, execution, and real-world scaling. Learn from founders and investors who have shaped the industry. Connect with peers navigating similar growth stages. Walk away with tactics you can apply immediately

Offer ends March 13.

San Francisco, CA

|

October 13-15, 2026

REGISTER NOW

RAG is undeniably useful — it allows one to attribute things a model generates to retrieved documents to verify their factuality (and, as an added benefit, avoid potentially copyright-infringing

regurgitation

). RAG also lets enterprises that don’t want their documents used to train a model — say, companies in highly regulated industries like healthcare and law — to allow models to draw on those documents in a more secure and temporary way.

But RAG certainly

can’t

stop a model from hallucinating. And it has limitations that many vendors gloss over.

Wadden says that RAG is most effective in “knowledge-intensive” scenarios where a user wants to use a model to address an “information need” — for example, to find out who won the Super Bowl last year. In these scenarios, the document that answers the question is likely to contain many of the same keywords as the question (e.g., “Super Bowl,” “last year”), making it relatively easy to find via keyword search.

Things get trickier with “reasoning-intensive” tasks such as coding and math, where it’s harder to specify in a keyword-based search query the concepts needed to answer a request — much less identify which documents might be relevant.

Even with basic questions, models can get “distracted” by