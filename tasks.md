# Bookly Roadmap

## Feature-1: implement Bookly branding on chainlit UI

- [x] T1: work with Claude to come up with branding assets like icons 
- [x] T2: update the chainlit config and associated files to use those assets


## Feature-2: implement router for initial question. User can use the the chat bot for 3 types of interactions:
    -   Order status inquiries
    -   Return/refund requests
    -   General questions about shipping, policies, password reset, etc.

- [x] T3: Implement a router to route the questions. investigate simple ways to do this
- [x] T4: investigate which model to use, since this is simple oepration may be use a low cost model like Haiku, instead of Sonnet
- [x] T5: update the README.md file based on this change
- [x] T6: provide instructions for testing 


## Feature-3: Add additional docs to the policies folder to demonstrate the use case-3: "General questions about shipping, policies, password reset, etc."

- [x] T7: Create docs for shipping, policy,  password reset procedures- create .md files and store them in the policies folder
- [x] T8: think about other common & frequently asked questions for a book shop business and add them to a faq.md file in the policies folder


## Chore: Should I move the policies from prompts.py to policies folder and then reference them in the prompts.pyWhat are the pros and Cons? Think deeply and think step-by-step

## Chore: investigate if it makes sense to divide the prompt.py into multiple prompt files by category? What are the pros and Cons? Think deeply and think step-by-step  

