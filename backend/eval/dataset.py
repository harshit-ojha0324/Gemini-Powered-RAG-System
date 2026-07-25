"""Gold evaluation set over eval.corpus.

Each item labels the relevant passage id(s) and, for answerable questions, a
substring a grounded answer should contain. `answerable=False` marks questions
whose answer is NOT in the corpus — the system should abstain, not guess.
"""

GOLD = [
    {"question": "How many paid vacation days do full-time employees get?", "relevant_ids": ["pto"], "answer_substring": "20", "answerable": True},
    {"question": "Which days am I required to be in the office?", "relevant_ids": ["remote"], "answer_substring": "Tuesday", "answerable": True},
    {"question": "How much of a dependent's health premium does the company cover?", "relevant_ids": ["health"], "answer_substring": "60", "answerable": True},
    {"question": "What is the deadline to submit an expense for reimbursement?", "relevant_ids": ["expenses"], "answer_substring": "30 days", "answerable": True},
    {"question": "How long is parental leave?", "relevant_ids": ["parental"], "answer_substring": "16 weeks", "answerable": True},
    {"question": "What are the password requirements?", "relevant_ids": ["security"], "answer_substring": "14", "answerable": True},
    {"question": "When are performance reviews held?", "relevant_ids": ["reviews"], "answer_substring": "June", "answerable": True},
    {"question": "What home-office stipend do engineers receive?", "relevant_ids": ["equipment"], "answer_substring": "500", "answerable": True},
    {"question": "Where is the company headquarters located?", "relevant_ids": ["office"], "answer_substring": "Seattle", "answerable": True},

    # Out-of-scope: not covered by the handbook — the system should abstain.
    {"question": "What is the company's stock ticker symbol?", "relevant_ids": [], "answer_substring": None, "answerable": False},
    {"question": "Who won the FIFA World Cup in 2018?", "relevant_ids": [], "answer_substring": None, "answerable": False},
    {"question": "What is the recipe for a chocolate souffle?", "relevant_ids": [], "answer_substring": None, "answerable": False},
]
