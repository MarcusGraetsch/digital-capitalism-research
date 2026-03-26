---
url: https://towardsdatascience.com/automated-prompt-engineering-the-definitive-hands-on-guide-1476c8cd3c50
title: Automated Prompt Engineering: The Definitive Hands-On Guide | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:00:38.413306
word_count: 5166
paywall: True
cleaned_at: 2026-03-01T14:19:15.452280
cleaned_by: llm
quality_score: 8
---

url: https://towardsdatascience.com/automated-prompt-engineering-the-definitive-hands-on-guide-1476c8cd3c50
title: Automated Prompt Engineering: The Definitive Hands-On Guide | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:00:38.413306
word_count: 5166
paywall: True
---

# Automated Prompt Engineering: The Definitive Hands-On Guide | Towards Data Science






---

Large Language Models

Automated Prompt Engineering: The Definitive Hands-On Guide

Learn how to automate prompt engineering and unlock significant performance improvements in your LLM workload

Heiko Hotz

Sep 4, 2024

26 min read

Share

Image by author – Created with Imagen 3


Automated Prompt Engineering (APE) is a technique to automate the process of generating and refining prompts for a Large Language Model (LLM) to improve the model’s performance on a particular task. It uses the idea of prompt engineering which involves manually crafting and testing various prompts and automates the entire process. As we will see it is

very

similar to automated hyperparameter optimisation in traditional supervised machine learning.

In this tutorial we will dive deep into APE: we will first look at how it works in principle, some of the strategies that can be used to generate prompts, and other related techniques such as exemplar selection. Then we will transition into the hands-on section and write an APE program from scratch, i.e. we won’t use any libraries like DSPy that will do it for us. By doing that we will get a much better understanding of how the principles of APE work and are much better equipped to leverage the frameworks that will offer this functionality out of the box.

As always, the code for this tutorial is available on

Github

(under

CC BY-NC-SA 4.0 license

).

Why is it important?

When working with organisation I observe that they often struggle to find the optimal prompt for an LLM for a given task. They rely on manually crafting and refining prompts and evaluating them. This is extremely time consuming and is often a blocker for putting LLMs into actual use and production.

And it can sometimes feel like alchemy, as we are trying out different prompts, trying different elements of structure and instructions in hopes of discovering a prompt that finally achieves the desired performance. And in the meantime we actually don’t even know what works and what doesn’t.

Image by author – Created with Imagen 3

And that’s just for one prompt, one LLM, and one task. Imagine having to do this in an enterprise setting where there are several LLMs and hundreds of tasks. Manual prompt engineering quickly becomes a bottleneck. It’s slow and, maybe even worse, limits our ability to explore the full range of possibilities that LLMs offer. We also tend to fall into predictable patterns of thinking, which can constrain the creativity and effectiveness of our prompts.

I, for example, always tend to use the same old tricks with LLM prompts, such as chain-of-thought and few-shot prompting. And there’s nothing wrong with that – often, they lead to better results. But I’m always left wondering whether I’ve ‘squeezed the most juice’ from the model. LLMs, on the other hand, can explore a much wider space of prompt designs, often coming up with unexpected approaches that lead to significant performance gains.

To give a concrete example: In the paper

The Unreasonable Effectiveness of Eccentric Automatic Prompts

,

the authors found that the following prompt worked really well for the Llama-70B model:

Command, we need you to plot a course through this turbulence and locate the source of the anomaly. Use all available data and your expertise to guide us through this challenging situation.

Captain’s Log, Stardate [insert date here]: We have successfully plotted a course through the turbulence and are now approaching the source of the anomaly.

I mean who would ever come up with a prompt like that? But when experimenting with APE over the past few weeks, I’ve seen over and over again that LLMs are very creative when it comes to coming up with these kind of prompts, and we will see that later in the tutorial as well. APE allows us to automate the process of prompt optimisation and tap into unlocked potential for our LLM applications!

The principles of Automated Prompt Engineering

Prompt Engineering

After lots of experimentation, organisations are now at a point where they are considering using LLMs in production for a variety of tasks such as sentiment analysis, text summarisation, translation, data extraction, and code generation, amongst others. Many of these tasks have clearly defined metrics, and the model performance can be evaluated right away.

Take code generation, for example: we can immediately assess the accuracy of the generated code by running it through compilers or interpreters to check for syntax errors and functionality. By measuring metrics such as the percentage