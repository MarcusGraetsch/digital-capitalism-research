---
url: https://towardsdatascience.com/how-i-use-chatgpt-as-a-data-scientist-0730fa1e21c2
title: How I Use ChatGPT As A Data Scientist | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:03:25.977903
word_count: 1651
paywall: True
cleaned_at: 2026-03-01T14:19:09.285837
cleaned_by: llm
quality_score: 8
---

url: https://towardsdatascience.com/how-i-use-chatgpt-as-a-data-scientist-0730fa1e21c2
title: How I Use ChatGPT As A Data Scientist | Towards Data Science
domain: towardsdatascience.com
category: aigen
date_scanned: 2026-03-01T10:03:25.977903
word_count: 1651
paywall: True
---

# How I Use ChatGPT As A Data Scientist | Towards Data Science






---

Artificial Intelligence

How I Use ChatGPT As A Data Scientist

How ChatGPT improved my productivity as a data scientist

Egor Howell

Jun 2, 2024

8 min read

Share

Photo by Shantanu Kumar:

https://www.pexels.com/photo/chatgpt-webpage-open-on-iphone-16474955/

The whole world has heard of ChatGPT, yet according to a recent

news

study

, only 2% of people use it daily.

I use it every day as a data scientist for so many things. It has honestly 2x my productivity in some areas.

In this article, I want to explain how I use ChatGPT, and hopefully, it can give you some new ideas on how to use it more regularly to improve your output, regardless if you are a data scientist or not.

Studying & Learning

One of my favourite prompts is the “explain like I’m 5” (ELI5). It basically makes ChatGPT explain a topic to me in such a simple way, often better than many online resources.

For example, if we run “explain to me recurrent neural networks like I’m 5 years old.”

Example output from ChatGPT.

The analogy is excellent and really builds the intuition behind recurrent neural networks.


The principal value here is that I use ChatGPT like a personal tutor who can explain things to me in so many different ways that I can choose. This is really powerful and may save you a lot of time searching the internet for that one explanation that clicks for you. Try it out and let me know how you get on!

Unit Tests

It’s no secret that most tech professionals don’t like writing unit tests. They are very tedious but need to be done as they ensure your code is robust and build confidence when deploying it to production.

ChatGPT can greatly expedite this process by providing a testing template that you can tweak to test your code’s edge cases.

Let’s consider a function that calculates the Fibonacci sequence:

def fibonacci_sequence(n):

if n <= 0:

return []

elif n == 1:

return [0]

elif n == 2:

return [0, 1]

sequence = [0, 1]

for i in range(2, n):

next_fibonacci_number = sequence[-1] + sequence[-2]

sequence.append(next_fibonacci_number)

return sequence

Let’s input this into ChatGPT, asking it to write unit tests for our function:

Asking ChatGPT to write unit tests for us.

This is the full output for the tests generated from ChatGPT:

import unittest

def fibonacci_sequence(n):

if n <= 0:

return []

elif n == 1:

return [0]

elif n == 2:

return [0, 1]

sequence = [0, 1]

for i in range(2, n):

next_fibonacci_number = sequence[-1] + sequence[-2]

sequence.append(next_fibonacci_number)

return sequence

class TestFibonacciSequence(unittest.TestCase):

def test_negative_input(self):

self.assertEqual(fibonacci_sequence(-1), [])

def test_zero_input(self):

self.assertEqual(fibonacci_sequence(0), [])

def test_one_input(self):

self.assertEqual(fibonacci_sequence(1), [0])

def test_two_input(self):

self.assertEqual(fibonacci_sequence(2), [0, 1])

def test_five_input(self):

self.assertEqual(fibonacci_sequence(5), [0, 1, 1, 2, 3])

def test_ten_input(self):

self.assertEqual(fibonacci_sequence(10), [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])

if __name__ == '__main__':

unittest.main()

I can confirm this works after running it in my PyCharm IDE.

PyCharm terminal output.

I can’t tell you how much time this saves me. Just setting up the test alone takes a good proportion of time. This approach lets me focus on the essential parts: finding those edge cases that may break my function.


Pytest Tutorial: An Introduction To Unit Testing

Creating Visualisations

Creating plots is often quite lengthy, particularly if you are adding multiple lines and labels and trying to make the graph look nice overall. I have spent hours smashing my keyboard, getting Matplotlib to give me what I want. It’s not fun, and I don’t recommend it.

Before GPT-4 and GPT-4o, I would use ChatGPT-3.5 to generate the Python code to plot my graph by running it in an IDE. However, now it’s even easier, as they have something called Advanced Analytics. You literally hand it your data, and it creates the plot for you and outputs it to the screen with the associated code.

For example, let’s use the data I got from Kaggle, which contains

Netflix Movies and TV Shows

(CC0 licence). All I do is drag into ChatGPT, and I can ask it to explain the data for me:

The input data

Output from ChatGPT.

It also provides the Python code it used to load the dat