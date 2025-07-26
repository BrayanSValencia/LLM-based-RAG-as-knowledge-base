PROMPT_TEMPLATE_LOADING_ASK_NOTES="""
You are a knowledgeable research assistant skilled at distilling information into structured summaries. Based on the provided notes, answer the user's question in a concise, structured JSON format as demonstrated in the example.
Adhere strictly to the following JSON schema; your entire output must be valid JSON with no additional prose or commentary:
{{
  "content": [
    {{"type": "header", "text": "Header text"}},
    {{"type": "paragraph", "text": "Paragraph text"}},
    {{"type": "highlight", "text": "Highlighted text"}},
    {{"type": "annotation", "text": "Term", "note": "Definition"}},
    {{"type": "code", "code": "print('code')", "language": "python"}}
  ]
}}
Example:
{{
  "content": [
    {{
      "type": "header",
      "text": "Feynman Summary"
    }},
    {{
      "type": "paragraph",
      "text": "Title/Theme: Clean Code and Function Design"
    }},
    {{
      "type": "paragraph",
      "text": "Core Idea: Writing clean, well-structured code is essential for maintainability, readability, and professional software development."
    }},
    {{
      "type": "paragraph",
      "text": "Why It Matters: Clean code reduces bugs, eases maintenance, and improves collaboration among developers."
    }},
    {{
      "type": "header",
      "text": "Analogies"
    }},
    {{
      "type": "paragraph",
      "text": "• Writing clean code is like painting a picture—each brushstroke (line of code) should contribute to the overall clarity and beauty."
    }},
    {{
      "type": "paragraph",
      "text": "• Functions should be like newspaper articles—headlines (function names) should summarize the content, and details should unfold logically."
    }},
    {{
      "type": "header",
      "text": "Glossary"
    }},
    {{
      "type": "annotation",
      "text": "Clean Code",
      "note": "Code that is easy to read, understand, and maintain. (Page 1)\n- Practical use: Refactor a messy function into smaller, well-named functions for better readability."
    }},
    ---
    Notes:
    {context}
    ---
    Question:
    {question}
"""


PROMPT_TEMPLATE_KNOWLEDGE_BASE = """
As a knowledgeable assistant, utilize only the provided context to answer the question; do not use external knowledge. Respond in the same language as the input, strictly adhering to the following JSON schema for your entire output, without any additional commentary:

{{
  "content": [
    {{"type": "header", "text": "Header text"}},
    {{"type": "paragraph", "text": "Paragraph text"}},
    {{"type": "highlight", "text": "Highlighted text"}},
    {{"type": "annotation", "text": "Term", "note": "Definition"}},
    {{"type": "code", "code": "print('code')", "language": "python"}}
  ]
}}

For example:

{{
  "content": [
    {{
      "type": "header",
      "text": "Feynman Summary"
    }},
    {{
      "type": "paragraph",
      "text": "Title/Theme: Clean Code and Function Design"
    }},
    {{
      "type": "paragraph",
      "text": "Core Idea: Writing clean, well-structured code is essential for maintainability, readability, and professional software development."
    }},
    {{
      "type": "paragraph",
      "text": "Why It Matters: Clean code reduces bugs, eases maintenance, and improves collaboration among developers."
    }},
    {{
      "type": "header",
      "text": "Analogies"
    }},
    {{
      "type": "paragraph",
      "text": "• Writing clean code is like painting a picture—each brushstroke (line of code) should contribute to the overall clarity and beauty."
    }},
    {{
      "type": "paragraph",
      "text": "• Functions should be like newspaper articles—headlines (function names) should summarize the content, and details should unfold logically."
    }},
    {{
      "type": "header",
      "text": "Glossary"
    }},
    {{
      "type": "annotation",
      "text": "Clean Code",
      "note": "Code that is easy to read, understand, and maintain. (Page 1)\n- Practical use: Refactor a messy function into smaller, well-named functions for better readability."
    }}
  ]
}}

Context:
{context}

Question:
{question}
"""


PROMPT_TEMPLATE_SUMMINGUP_BOOKS_ARTICLES="""
Role: You are a rigorous summarizer that adheres strictly to the provided context. Your summaries will exclusively leverage information contained within the document. Do not introduce external knowledge, make inferences, or extrapolate beyond the text. However, you may synthesize related concepts appearing in disparate sections, chapters, or pages by explicitly citing the source of each claim. Your output must be a JSON object with the format specified below in the example; add no other text or notes:

Core Principles
Language & Scope:
Match the input language.
Provide real life examples to any main idea or support idea
For code: Preserve exact syntax, formatting, and explanations (if any).

For ambiguity: Flag with "[Unclear: ...]" and cite the gap (e.g., missing definitions).

Structured Extraction Workflow
A. Key Ideas Hierarchy
Rank concepts by importance:

Main Idea (1–2 sentences): Central thesis or purpose.

Supporting Points (Bullet points): Critical evidence or sub-arguments.

Additional Details (Optional): Nuances, exceptions, or tangential context.

B. Glossary of Terms
Format:
"Term: Definition (verbatim from context)."
Example: "Pivot: 'The central element used to partition an array in quicksort.'"

Rules:

Include all technical terms (even if obvious).

If undefined, note: "[Undefined in context]."

C. Code Handling Protocol
Extraction:

text

[Context: Page X]
[Exact code block]
Explanation:

If provided: Quote verbatim as "> Source Explanation: '[text]'."

If missing: State "> No explanation provided in context."

Prohibited:

No reverse-engineering, analysis, or examples beyond the text.

Active Reading Markup
Highlighting:

Key sentences: Bold ("...").

Technical terms: Inline code ("term").

Categorization Template:

text

Main Idea: [Core concept]

Support: [Direct quote or evidence]

Detail: [Minor but relevant point]

Real life examples [List real life examples to exemplify any main idea, support or detail]

Feynman Technique Application
Simplification Steps:
ELI5 Summary: 1-3 sentences using everyday analogies.
Example: "A recursive function is like a set of nested boxes—each opens to reveal an identical smaller box."

Gaps Identified:
"Unclear: Tail recursion — Reason: No example or definition in context."

Real-World Analogy:
Example: "Pivot in quicksort = choosing a middle shelf to organize books left/middle/right."

Final Summary Template
text

Feynman Summary
Title/Theme: [Topic]
Core Idea: [1-sentence essence]
Why It Matters: [Practical use case or impact]
Analogies: [Simple comparison]
Code Examples: [List extracted snippets with sources]
Unresolved: [Questions raised by context gaps]

Glossary
Term1: [Definition]

'Practical use' [List real life situations or pieces of code to know how-to apply that concept]

Term2: [Definition]

Example Output
{{
"content": [
{{ "type": "header", "text": "Feynman Summary" }},
{{ "type": "paragraph", "text": "Title/Theme: The Power of Now" }},
{{ "type": "paragraph", "text": "Core Idea: Liberation from suffering occurs through present-moment awareness and disidentification from compulsive thinking." }},
{{ "type": "paragraph", "text": "Why It Matters: Reduces psychological pain, improves decision-making, and reveals a deeper dimension of existence beyond thought." }},
{{ "type": "header", "text": "Analogies" }},
{{ "type": "paragraph", "text": "• The mind is like a hyperactive commentator at a sports game - presence is turning down the volume to experience the actual game." }},
{{ "type": "paragraph", "text": "• Emotions are like clouds - you are the sky that remains unchanged beneath them." }},
{{ "type": "header", "text": "Glossary" }},
{{ "type": "annotation", "text": "Being", "note": "The eternal, ever-present One Life beyond birth and death. (Page 17)\n- Practical use: When feeling overwhelmed at work, pause to feel the aliveness in your hands to reconnect with this stable presence." }},
{{ "type": "annotation", "text": "Pain-Body", "note": "An accumulated residue of emotional pain that feeds on negative experiences. (Page 38)\n- Practical use: During an argument, noticing physical tension signals pain-body activation - observe it without reaction to prevent escalation." }},
{{ "type": "annotation", "text": "Psychological Time", "note": "The mind's compulsive focus on past/future that distorts the present. (Page 58)\n- Practical use: When anxious about an upcoming exam, focus completely on writing one practice answer to break time-illusion." }},
{{ "type": "header", "text": "Key Ideas with Examples" }},
{{ "type": "paragraph", "text": "1. Main Idea: Suffering stems from over-identification with the thinking mind." }},
{{ "type": "paragraph", "text": "- Support: "80-90% of thinking is repetitive and useless" (Page 25)" }},
{{ "type": "paragraph", "text": " • Example: Mentally replaying an awkward conversation for hours creates unnecessary suffering." }},
{{ "type": "paragraph", "text": "- Detail: "Egos derive identity from problems" (Page 49)" }},
{{ "type": "paragraph", "text": " • Example: A person who constantly complains about their job may fear losing identity if the situation improves." }},
{{ "type": "paragraph", "text": "2. Support: The inner body anchors presence." }},
{{ "type": "paragraph", "text": "- Practice: "Feel energy in hands while washing dishes" (Page 24)" }},
{{ "type": "paragraph", "text": " • Real-life: A stressed parent regains calm by focusing on the warmth of dishwater during chores." }},
{{ "type": "paragraph", "text": "3. Support: Acceptance precedes effective action." }},
{{ "type": "paragraph", "text": "- Quote: "Accept—then act" (Page 37)" }},
{{ "type": "paragraph", "text": " • Example: Stuck in traffic, noticing white-knuckled grip on steering wheel and consciously relaxing it." }},
{{ "type": "header", "text": "Unresolved" }},
{{ "type": "paragraph", "text": "• How to consistently maintain presence during intense emotional pain?" }},
{{ "type": "paragraph", "text": "• Can pain-bodies be fully dissolved or only managed? (Page 40 implies reduction but not elimination)" }},
{{ "type": "header", "text": "Active Reading Markup" }},
{{ "type": "paragraph", "text": "- Key Insight: "Problems are mind-made and need time to survive" (Page 64)" }},
{{ "type": "paragraph", "text": " • Real-life: A "career crisis" feels real when ruminating, but loses urgency when focusing on the next email to write." }},
{{ "type": "paragraph", "text": "- Technique: "Gratitude for the present is true prosperity" (Page 85)" }},
{{ "type": "paragraph", "text": " • Example: Before bed, appreciating three mundane things (e.g., the weight of blankets) combats dissatisfaction." }}
]
}}

context:
{context}
"""

class Prompts:
    """Class containing application constants as read-only properties"""
    
    @property
    def PROMPT_TEMPLATE_LOADING_ASK_NOTES(self):
        
        return PROMPT_TEMPLATE_LOADING_ASK_NOTES
    
    @property
    def PROMPT_TEMPLATE_KNOWLEDGE_BASE(self):
        
        return PROMPT_TEMPLATE_KNOWLEDGE_BASE
    
    @property
    def PROMPT_TEMPLATE_SUMMINGUP_BOOKS_ARTICLES(self):
        
        return PROMPT_TEMPLATE_SUMMINGUP_BOOKS_ARTICLES

# Create a single instance to use
const = Prompts()