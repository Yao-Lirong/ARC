# ARC
An attempt to solve the [Abstraction and Reasoning Corpus](https://github.com/fchollet/ARC) using program synthesis. 

Current work is on building [an interpreter](./GARC/interpreter_log.py) to detect objects in the problem.

Previously, we did

- [Variational Homoencoder](./vhe/) to generate new input output pair, but the result didn't meet expectation. 
- [Generative ARC](./GARC/): building API for writing programs that can generate both input and output at the same time. The idea is that if we have a model that can learn to generate ARC programs, it should be able to solve the ARC problem easily too. 

One can reference [this log](./log.md) for a complete development process. 



## What this Work is About

François Chollet commented on [this kaggle discussion](https://www.kaggle.com/c/abstraction-and-reasoning-challenge/discussion/130360): 

If you don't know how to get started, I would suggest the following template:

- Take a bunch of tasks from the training or evaluation set -- around 10.
- For each task, write by hand a simple program that solves it. It  doesn't matter what programming language you use -- pick what you're  comfortable with.
- Now, look at your programs, and ponder the following:

1) Could they be expressed more naturally in a different medium (what we call a DSL, a domain-specific language)?
1) What would a search process that outputs such programs look like (regardless of conditioning the search on the task data)?
1) How could you simplify this search by conditioning it on the task data?
1) Once you have a set of generated candidates for a solution program, how do you pick the one most likely to generalize?

You will not find tutorials online on how to do any of this. The best you can do is read past literature on program synthesis, which will  help with step 3). But even that may not be that useful :)

This challenge is something new. You are expected to think on your  own and come up with novel, creative ideas. It's what's fun about it!

