---
url: https://towardsdatascience.com/how-i-studied-llms-in-two-weeks-a-comprehensive-roadmap-e8ac19667a31
title: How I Studied LLMs in Two Weeks: A Comprehensive Roadmap | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:00:04.230259
word_count: 1734
paywall: True
cleaned_at: 2026-03-01T14:19:10.310163
cleaned_by: llm
quality_score: 8
---

url: https://towardsdatascience.com/how-i-studied-llms-in-two-weeks-a-comprehensive-roadmap-e8ac19667a31
title: How I Studied LLMs in Two Weeks: A Comprehensive Roadmap | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:00:04.230259
word_count: 1734
paywall: True
---

# How I Studied LLMs in Two Weeks: A Comprehensive Roadmap | Towards Data Science






---

Data Science

How I Studied LLMs in Two Weeks: A Comprehensive Roadmap

A day-by-day detailed LLM roadmap from beginner to advanced, plus some study tips

Hesam Sheikh

Oct 18, 2024

8 min read

Share

Image created by Midjourney.

Stuck behind a paywall?

Read for Free!

Understanding how LLMs operate under the hood is becoming an

essential


understand

,

create

, or lead to AGI, the first step is

understanding what they are

.


Why I Started This Journey

I am obsessed with going deeper into concepts, even if I already know them. I could already read and understand the research on LLMs, I could build agents or fine-tune models. But it didn’t seem enough to me.

I wanted to know how large language models work mathematically and intuitively, and why they behave the way they do.

I was already familiar with this field, so I knew my knowledge gaps exactly. The fact that I have a background in machine learning and this field specifically has helped me big time in doing this in

two weeks

, otherwise this would take more than a month.

My Learning Material

I wanted to do this learning journey not just for LLMs, but many other topics in my interest (Quantum Machine Learning, Jax, etc.) So to document all this and keep it tidy, I started my

ml-retreat

GitHub repository

.

The idea was that sometimes we need to sit back from our typical work and reflect on the things we think we know and fill in the gaps.

ml-retreat Repository.

The repository was received much more positively than I expected. At the time of writing this article, it has been starred ⭐

330

times and increasing. There were many people out there looking for something I noticed, a

single comprehensive roadmap of all the best resources out there

.

All of the materials I used so far are free, you don’t need to pay anything.

I studied LLMs majorly in

three steps

:

1. Build an LLM from Scratch

This would conclude the fundamentals of language models. Token and positional embeddings, self-attention, transformer architectures, the original "Attention is All You Need" paper and the basics of fine-tuning. While I have used numerous resources for each topic, a crucial resource for this was

Build a Large Language Model (From Scratch)

by Sebastian Raschka (you can read it for free online). The book beautifully uncovers each of these topics to make them as accessible as possible.

My notes on the fundamentals of LLMs. (

Source

)

The Challenge

of this stage in my opinion was

self-attention

– not what it is, but how it works. How does self-attention map the context of each token in relation to other tokens? What do

Q

uery,

K

ey, and

V

alue represent, and why are they crucial? I suggest taking as much time as needed for this part, as it is essentially the core of how LLMs function.

Image by Author.

2. LLM Hallucination

For the second part of my studies, I wanted to understand what hallucination is and

why LLMs hallucinate

. This was more of a personal question lurking in my mind, but it also enabled me to understand some aspects of the language models.


positional bias


exposure bias

which implies in the inference phase, predicting a wrong token could derail the generation process for the next tokens like a snowball effect. I also learned how

Data

,

Training

, and

Inference

each contribute to this hallucination dilemma.

My notes on LLM Hallucination. (

Source

)

Hallucination is a big pain in the head for both researchers and those who build applications with LLM. I strongly suggest you take the time to study why this happens and also methods to mitigate it.

3. LLM Edge: beyond attention

The last two stages show you how LLMs work. There are some techniques however that are not so basic but have become mainstream in building LLMs. So I studied:

Pause tokens

that give LLMs more time to "think".

Infini-attention

which allows LLMs to have very big context windows (like Gemini’s 1M context window) by leveraging a sort of memory of previous tokens.