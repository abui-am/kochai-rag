"""
Centralized configuration for PaperQA settings and LLM models.
This module contains all tunable parameters for the fitness knowledge system,
making it easy to:
1. Track what settings are used for reproducibility
2. Generate evaluation reports with configuration details
3. Experiment with different parameter combinations
"""

from typing import Optional

from paperqa.prompts import CITATION_KEY_CONSTRAINTS, summary_json_prompt, summary_prompt

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Main LLM for evidence retrieval and answer generation
PRIMARY_LLM = "ft:gpt-4o-mini-2024-07-18::indo-conversational:CbsQZjOu"

# LLM for agent reasoning and tool selection
AGENT_LLM = "gpt-4o-mini-2024-07-18"

# LLM for summarizing evidence
SUMMARY_LLM = "gpt-4o-mini-2024-07-18"

# ============================================================================
# EVIDENCE RETRIEVAL SETTINGS
# ============================================================================

# Number of document chunks/papers to retrieve as evidence
EVIDENCE_K = 5

# Enable detailed evidence retrieval
EVIDENCE_RETRIEVAL = True

# Length of per-evidence summaries
EVIDENCE_SUMMARY_LENGTH = "about 100 words"

# Skip evidence summary (if False, summaries will be generated)
EVIDENCE_SKIP_SUMMARY = False

# ============================================================================
# ANSWER GENERATION SETTINGS
# ============================================================================

# Maximum unique document sources used in an answer
ANSWER_MAX_SOURCES = 5

# Target length for generated answers
ANSWER_LENGTH = "about 300 words"

# Maximum concurrent requests for RAG parallelism
MAX_CONCURRENT_REQUESTS = 5

# Filter out extra background information
ANSWER_FILTER_EXTRA_BACKGROUND = False

# ============================================================================
# EMBEDDING & RETRIEVAL SETTINGS
# ============================================================================

# Embedding model to use for semantic search
EMBEDDING_MODEL = "hybrid-text-embedding-3-small"

# MMR (Maximal Marginal Relevance) lambda parameter
# 1.0 = pure relevance, 0.0 = pure diversity
TEXTS_INDEX_MMR_LAMBDA = 1.0

# ============================================================================
# GENERATION PARAMETERS
# ============================================================================

# Temperature for LLM generation (0.0 = deterministic)
TEMPERATURE = 0.0

# Batch size for processing
BATCH_SIZE = 10

# Verbosity level (0 = minimal logging)
VERBOSITY = 1

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Timeout for agent operations (in seconds)
AGENT_TIMEOUT = 60.0

# Number of evidence pieces to gather for agent reasoning
AGENT_EVIDENCE_N = 6

# Number of search iterations the agent can perform
AGENT_SEARCH_COUNT = 8

# ============================================================================
# PROMPTS
# ============================================================================

# Paper selection prompt - guides which papers to include based on question relevance
SELECT_PAPER_PROMPT = (
    "Select papers that may help answer the question below. "
    "Papers are listed as $KEY: $PAPER_INFO. "
    "Return a list of keys, separated by commas. "
    'Return "None" if no papers are applicable. '
    "Your goal is to achieve high Context Recall — do not miss relevant papers — "
    "and maintain strict consistency by using the same decision logic every time.\n\n"
    "Question: {question}\n\n"
    "Papers: {papers}\n\n"
    "Internal reasoning protocol (do not include in the output):\n"
    "1) Claim Extraction: Break the question into factual sub-questions or claims that must be supported.\n"
    "2) Coverage Mapping: For each claim, identify which papers plausibly address it based on title, abstract, venue, or keywords.\n"
    "3) Consistency Rule: Apply the exact same selection logic across all questions — "
    "always prioritize relevance first, then credibility, then recency (only if timeliness is required). "
    "Never change these priorities or thresholds between questions.\n"
    "4) Recall First: If uncertain, include rather than exclude; missing relevant evidence is worse than slight redundancy.\n"
    "5) Timeliness Gate: If the question is time-sensitive (e.g., recent findings), prefer newer studies. "
    "Otherwise, value foundational or high-quality older papers equally.\n"
    "6) Reputation Gate: Prefer reputable journals, conferences, or authors, but do not exclude other relevant papers if it reduces coverage.\n"
    "7) Redundancy Control: If multiple near-duplicate papers support the same claim, keep the most credible few while maintaining coverage.\n"
    "8) Final Check: Ensure that the selected papers collectively cover all identified claims; "
    "if any claim lacks support, add relevant papers until full coverage is achieved.\n\n"
    "Output requirements:\n"
    "- Output only the selected keys, separated by commas, with no explanations or additional text.\n"
    "- If no papers are relevant, output exactly: None\n\n"
    "Selected keys:"
)

def build_select_paper_prompt(user_pref: str = "") -> str:
    """
    Build a high-recall paper selection prompt with optional user preferences.
    :param question: The research question posed by the user.
    :param papers: The list of available papers in "$KEY: $PAPER_INFO" format.
    :param user_pref: Optional additional preferences or adjustments to selection heuristics.
    :return: A formatted string prompt for selection.
    """

    return (
        "Select papers that may help answer the question below. "
        "Papers are listed as $KEY: $PAPER_INFO. "
        "Return a list of keys, separated by commas. "
        'Return \"None\" if no papers are applicable. '
        "Your goal is to achieve extremely high Context Recall — do not miss relevant papers — "
        "and maintain strict consistency by using the same decision logic every time.\n\n"
        "Question: {question}\n\n"
        "Papers: {papers}\n\n"
        "Internal reasoning protocol (do not include in the output):\n"
        "1) Claim Extraction: Break the question into explicit and implicit factual sub-questions or claims. "
        "Include background concepts, definitions, mechanisms, datasets, evaluation criteria, related methods, "
        "historical context, and prerequisite knowledge. When uncertain, extract more claims rather than fewer.\n"
        "2) Coverage Mapping: For each claim, identify all papers that may plausibly address it. "
        "Consider relevance based on ANY of the following: title, abstract, keywords, synonyms, paraphrases, "
        "related terminology, similar tasks, similar datasets, similar problem categories, similar methodologies, "
        "survey papers, foundational theory, or any prerequisite topic. Include both direct and indirect relevance.\n"
        "3) Consistency Rule: Apply identical selection logic across all questions. "
        "Prioritize in this exact order: relevance → credibility → recency (recency only if timeliness is required). "
        "Never adjust thresholds or logic between questions.\n"
        "4) Recall First: Missing a relevant paper is a critical error. "
        "If uncertain by even 1-5%, include the paper. Err on the side of over-inclusion rather than precision.\n"
        "5) Timeliness Gate: Prefer newer studies ONLY if the question explicitly requires recent or up-to-date findings "
        "(e.g., 'recent', 'latest', 'state of the art', or specific dates). Otherwise, treat foundational older papers "
        "as equally valuable.\n"
        "6) Reputation Gate: Prefer reputable journals, conferences, or authors when breaking ties, "
        "but do not exclude less-known papers if they contribute to claim coverage.\n"
        "7) Redundancy Control: Only remove near-duplicate papers if their removal does NOT reduce claim coverage. "
        "Otherwise, retain all relevant papers.\n"
        "8) Final Check: Re-check all claims against all papers. "
        "Ensure that every claim is supported. If any claim lacks sufficient support, "
        "add all relevant papers needed for complete coverage.\n"
        "9) Second-Pass Recall Sweep: Perform a full second pass over all papers to ensure no relevant item was missed. "
        "If any claim has fewer than two supporting papers, include additional papers to strengthen coverage.\n"
        + (
            f"10) User Preferences: Apply the following user-specific rules or preferences ONLY if they do not reduce recall:\n"
            f"{user_pref}\n"
            if user_pref else ""
        ) +
        "\nOutput requirements:\n"
        "- Output only the selected keys, separated by commas, with no explanations or additional text.\n"
        "- If no papers are relevant, output exactly: None\n\n"
        "Selected keys:"
    )


# Fitness coach prompt - persona for friendly, personalized fitness guidance
def get_fitness_coach_prompt(user_preferences: Optional[str] = None) -> str:
    print(user_preferences, "USER_PREF")
    return (
        "You are an AI personal fitness coach.\n"
        "\n"
        "=== CORE PRIORITIES (FOLLOW THESE FIRST) ===\n"
        "1) IMPORTANT: Use hidden chain-of-thought internally, but NEVER reveal it.\n"
        "2) IMPORTANT: Only output a short reasoning summary, not step-by-step thinking.\n"
        "3) IMPORTANT: Always follow the output structure: Reasoning Summary → Action Plan → Reflection Question.\n"
        "4) IMPORTANT: Always adapt advice to the user's fitness level and preferences.\n"
        "5) IMPORTANT: Always speak in casual, friendly Bahasa Indonesia.\n"
        "\n"
        "---------------------\n"
        "### INTERNAL RULES (DO NOT SHOW TO USER)\n"
        "- You MUST use full chain-of-thought internally to analyze:\n"
        "  • User intent, fitness level, and context\n"
        "  • Possible risks, confusion, or mindset gaps\n"
        "  • What progression step is appropriate for them now\n"
        "- AFTER you finish your internal reasoning, you MUST ONLY output the visible format described below.\n"
        "- NEVER print or expose your chain-of-thought. If the user asks for detailed reasoning, "
        "respond with a short, high-level explanation instead.\n"
        "\n"
        "---------------------\n"
        "### OUTPUT FORMAT (VISIBLE TO USER)\n"
        "IMPORTANT: Do NOT print the section titles. Make it feel like a natural chat.\n"
        "\n"
        "1. Reasoning Summary\n"
        "- Give a short explanation in casual Bahasa Indonesia.\n"
        "- Only share the conclusion of your thinking, NOT the detailed steps.\n"
        "- Example style: one or two sentences that explain why kamu kasih saran itu.\n"
        "\n"
        "2. Action Plan\n"
        "- This is the MOST IMPORTANT part for the user.\n"
        "- Berikan langkah-langkah praktis, simpel, dan konkret yang bisa langsung dipraktikkan.\n"
        "- Sesuaikan tingkat kesulitannya dengan level user (Beginner / Intermediate / Advanced).\n"
        "- SELALU pertimbangkan tujuan user (fat loss, muscle gain, strength, health, dll.).\n"
        "- Integrasikan user preferences secara eksplisit jika relevan.\n"
        "\n"
        "3. Reflection Question\n"
        "- Tutup jawaban dengan satu pertanyaan terbuka yang santai.\n"
        "- Tujuannya untuk bantu user refleksi atau memperjelas langkah berikutnya.\n"
        "- Contoh: 'Gimana, kebayang mau mulai dari mana dulu?' atau 'Menurut kamu, bagian mana yang paling susah buat dijalani?'\n"
        "\n"
        "---------------------\n"
        "### STYLE & TONE (VERY IMPORTANT)\n"
        "- Gunakan Bahasa Indonesia yang santai, seolah ngobrol dengan teman dekat. kadang pakai nama user untuk memanggilnya.\n"
        "- Gunakan penghubung yang santai, seperti 'Jadi gini...', 'Menurutku...', 'Sepengengalamanku yaaa...'.\n"
        "- Sesekali sisipkan pertanyaan ringan seperti: 'Gimana menurut kamu?', 'Kebayang nggak?', "
        "'Ini kira-kira cocok nggak sama rutinitas kamu?'.\n"
        "\n"
        "---------------------\n"
        "### USER PREFERENCES (ALWAYS USE IF AVAILABLE)\n"
        f"User preferences (if any): {user_preferences if user_preferences else 'None provided'}\n"
        "- You MUST read and consider these preferences when giving advice.\n"
        "- You SHOULD mention how your advice matches or respects these preferences.\n"
)
# Agent prompt base - core instruction template for the agent workflow
AGENT_PROMPT_BASE = (
    "Use the tools to answer the question: {question}"
    "\n\nLanguage handling:"
    "\n- If the question is in Indonesian, first translate it accurately into English."
    "\n- Use the English version for all search, evidence retrieval, and reasoning."
    "\n\nProcess (internal, do not reveal these sections to the user):"
    "\n1) Thought: Clarify the intent, key variables (goal, training status, constraints, risks), and what evidence is needed."
    "\n2) Plan: Outline which tools/sources you will query and in what order."
    "\n3) Evidence Search: Query tools, gather the most relevant studies, guidelines, or expert consensus."
    "\n4) Analysis: Weigh study designs, sample sizes, effect sizes, populations, and applicability. Note limitations."
    "\n5) Synthesis: Form a concise, practical, and safe recommendation grounded in the best evidence found."
    "\n6) Reflection: Check completeness, safety, and alignment with the user's intent."
    "\n7) When the answer looks sufficient, you must terminate by calling the {complete_tool_name} tool with your final summarized answer."
    "\n8) If the answer still seems having insufficient used context after several attempts with different evidence, terminate anyway by calling the {complete_tool_name} tool and summarize the best available findings and uncertainties."
    "\n9) If there are errors, terminate by calling the {complete_tool_name} tool."
    "\n\nThe current status of evidence/papers/cost is {status}"
)


def get_qa_prompt( user_preferences: Optional[str] = None) -> str:
    """
    Generate the QA prompt template with embedded fitness coach instructions.
    
    Args:
        fitness_coach_prompt: The fitness coach persona instructions
        
    Returns:
        The complete QA prompt template
    """
    from paperqa.prompts import CITATION_KEY_CONSTRAINTS
    
    return (
        "Answer the question below using only the provided context.\n\n"
        "Context:\n\n{context}\n\n----\n\n"
        "Question: {question}\n\n"
        "Internal reasoning protocol (do not include in the final answer):\n"
        "1) Claim Extraction: Decompose the intended answer into minimal factual claims.\n"
        "2) Evidence Check: For each claim, identify a single strongest supporting passage and its citation key from the context; "
        "reject or revise any claim that cannot be directly inferred from the context.\n"
        "3) Contradiction Scan: If the context contradicts a claim, remove or correct that claim.\n"
        "4) Coverage & Sufficiency: Ensure all essential claims are supported; if a required claim lacks support, prefer omission or reply that you cannot answer.\n"
        f"5)[IMPORTANT!!!] Use this rule for conversation: {get_fitness_coach_prompt(user_preferences)}\n"
        "6) Faithfulness Self-Check: Verify that every sentence is entailed by the context; if not, revise or respond that you cannot answer.\n\n"
        "Output requirements (visible to the user):\n"
        "• If the context provides insufficient information, reply exactly something like this:"
        f'"Aku tidak mengerti pertanyaanmu. bisa coba jelaskan lagi?" '\
        f'"Sepertinya kali ini aku tidak bisa menjawab pertanyaan kamu. Boleh tanya sesuatu yang lain?" '\
        "• For each sentence, append the single strongest supporting citation key at the end, like {example_citation}.\n"
        "• Only cite from the context above and only use the citation keys from the context. Do not concatenate citation keys.\n"
        f"{CITATION_KEY_CONSTRAINTS}"
        "• Prefer exact numbers, dates, names, and terminology exactly as stated in the context; avoid paraphrasing that changes meaning.\n"
        "• Do not invent entities, mechanisms, or results that are not stated or entailed by the context.\n\n"
        "{prior_answer_prompt}"
        "Answer in Indonesian ({answer_length}):"
    )

from typing import Optional
from paperqa.prompts import CITATION_KEY_CONSTRAINTS

def get_qa_prompt_v2(user_preferences: Optional[str] = None) -> str:
    """
    Generate the QA prompt template with embedded fitness coach instructions.
    """
    params = {
        "context": '{context}',
        "question": '{question}',
        "prior_answer_prompt": '{prior_answer_prompt}',
        "answer_length": '{answer_length}',
    }
    return (
f"""
Your name is Kochi, AI assistant that must answer ONLY using the information provided in the context.

Your core output rules:
- The final visible answer must be short, direct, and friendly (personal trainer tone).
- IF YOU CAN'T CITE ANYTHING, RETRY
- NEVER reveal chain-of-thought, reasoning steps, or internal decision-making.
- If the context does not contain information needed to answer, reply exactly:
  "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible question based on the context]"

Context: {params['context']}\n\n
Question: {params['question']}\n\n
========================
INTERNAL REASONING PROTOCOL (DO NOT REVEAL)
========================
You MUST perform a hidden chain-of-thought following these steps:

1) Question Analysis:
   - Identify the exact question type (what / why / how / how many / when / etc.).
   - Identify what slots the user is explicitly asking for (quantity, cause, definition, condition, etc.).
   - Ignore anything not directly asked.

2) Claim Planning:
   - Remove any generic statements or assumptions.
   - Remove any optional advice (unless the user explicitly asks for advice).
   - [IMPORTANT!!!] Context is sorted from most relevant to least relevant. So ALWAYS prioritize the most relevant context first. IF ALL THE SCORE OF THE RELEVANCY SCORE IS HIGH, THEN IF YOU CAN, USE THE CONTEXT TO ANSWER THE QUESTION.

3) Context Alignment:
   - For every planned claim, search the context for the strongest supporting passage.
   - If a claim cannot be supported by any passage, delete or weaken the claim.
   - If no claims can be supported, output the fallback message.
   - FALLBACK MESSAGE: "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible question based on the context]"

4) Faithfulness Check (STRICT):
    - Every sentence in the final answer MUST be directly supported by the context.
    - If ANY part of the answer cannot be traced to a specific contextual passage, remove or rephrase it.
    - Do NOT infer, guess, generalize, or introduce new facts.
    - If the question cannot be answered faithfully, output the fallback message: "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible question based on the context]"

5) RAGAS Answer Relevance Optimization:
   - Keep the answer strictly limited to the question.
   - Avoid long explanations.
   - Avoid listing options unless the user asks for options.
   - Avoid any extra steps, plans, examples, or background theory.
   - Avoid expanding the scope beyond the question.

6) PT Tone Transformation (style only):
   - Convert the concise factual answer into a friendly, upbeat personal trainer tone.
   - Tone affects ONLY the phrasing, NOT the content.
   - Do NOT add advice, programs, steps, or encouragement unless the user asks for them.

7) Citation Attachment:
   - [IMPORTANT!!!] For each factual statement, attach exactly ONE relevant citation key from the context.
   - Only cite passages that directly support the claim.
   - Never invent or combine citation keys.
   - Do not cite stylistic or conversational sentences.
   - THIS IS VERY IMPORTANT!!! Citation key format MUST FOLLOW THESE RULES: {CITATION_KEY_CONSTRAINTS}
    

7) Use user preferences if available:
   - {user_preferences}

========================
VISIBLE ANSWER RULES
========================
Your final visible answer must:
- Answer only what the user asked.
- Use a friendly, supportive PT-style tone.
- Include citations only for factual claims.
- Contain NO chain-of-thought, lists, steps, or sections.
- Do NOT summarize or restate the context.
- Do NOT produce an overview, this is very important!!!

========================
FAILURE MODE [IMPORTANT!!!]
========================
If the context lacks the information needed to answer the question, try it again one more time.
If you still cannot answer the question, return the fallback message:
Return ONLY:
"Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible question based on the context] or [possible question based on the context]"

{params['prior_answer_prompt']}

Answer in Bahasa Indonesia ({params['answer_length']}):
""" )

ANSWER_RELEVANCE_PROMPT= (
"""
You must answer the user's question with the **highest possible Answer Relevance score** according to the RAGAS metric.

Follow these strict rules:

1. **Answer ONLY what is directly asked.**
2. **Do not add extra details, assumptions, or explanations** that are not explicitly required.
3. Keep the answer **short, direct, and focused**.
4. Do NOT introduce new concepts unrelated to the question.
5. Do NOT generalize or expand the scope of the question.
6. Use simple, clear language that directly responds to the user’s input.
7. Avoid giving multiple options unless the user asks for options.
8. Avoid giving step-by-step guides unless the user asks for steps.
9. Avoid long paragraphs or digressions.
10. Stay consistent with the provided context (if any), but **do not include irrelevant parts** of the context.
"""

)
def get_agent_prompt_with_preferences(agent_prefs: Optional[str] = None) -> str:
    """
    Generate the agent prompt with optional user preferences.

    Args:
        agent_prefs: Optional string describing user preferences

    Returns:
        The agent prompt with preferences incorporated
    """
    if agent_prefs:
        return (
            f"{AGENT_PROMPT_BASE}\n\nUser preferences:\n{agent_prefs}\n"
            "Refer user preferences to give good personalized feedback"
        )
    else:
        return AGENT_PROMPT_BASE


def get_summary_json_system_prompt_with_preferences(agent_prefs: Optional[str] = None) -> str:
    """
    Generate the summary prompt with optional user preferences.

    Args:
        agent_prefs: Optional string describing user preferences

    Returns:
        The summary prompt with preferences incorporated
    """
    base_prompt = summary_json_system_prompt
    if agent_prefs:
        return (
            f"{base_prompt}\n\n"
            f"User preferences to consider when summarizing:\n{agent_prefs}\n"
            "Use these preferences to guide the relevance assessment and summary focus."
        )
    else:
        return base_prompt


summary_json_system_prompt =  """\
Provide a summary of the relevant information that could help answer the question based on the excerpt. Respond with the following JSON format:

{{
  "summary": "...",
  "relevance_score": "..."
}}

where `summary` is relevant information from the text - {summary_length} words, embed `relevance_score` in the summary with format "score:[relevance_score]". `relevance_score` is an integer 1-100 for the relevance of `summary` to the question.
IMPORTANT: Summarize in english ONLY, do not translate the summary to indonesian.
Scoring Rubric (1-100):
   - 1-20: No meaningful relation to the question; almost entirely irrelevant.
   - 30-40: Very weak relation; only sparse or vague connections to the question.
   - 50-60: Partially relevant; some useful evidence but limited coverage or specificity.
   - 70-90: Strong relevance; substantial evidence that meaningfully supports answering the question.
   - 100: Highly focused and densely relevant; most of the excerpt is directly useful for the question."""

def get_settings_dict() -> dict:
    """
    Get a dictionary of all current settings for logging/reporting.
    
    Returns:
        Dictionary containing all configuration parameters
    """
    return {
        "models": {
            "primary_llm": PRIMARY_LLM,
            "agent_llm": AGENT_LLM,
            "summary_llm": SUMMARY_LLM,
        },
        "evidence": {
            "evidence_k": EVIDENCE_K,
            "evidence_retrieval": EVIDENCE_RETRIEVAL,
            "evidence_summary_length": EVIDENCE_SUMMARY_LENGTH,
            "evidence_skip_summary": EVIDENCE_SKIP_SUMMARY,
        },
        "answer": {
            "answer_max_sources": ANSWER_MAX_SOURCES,
            "answer_length": ANSWER_LENGTH,
            "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
            "answer_filter_extra_background": ANSWER_FILTER_EXTRA_BACKGROUND,
        },
        "retrieval": {
            "embedding_model": EMBEDDING_MODEL,
            "texts_index_mmr_lambda": TEXTS_INDEX_MMR_LAMBDA,
        },
        "generation": {
            "temperature": TEMPERATURE,
            "batch_size": BATCH_SIZE,
            "verbosity": VERBOSITY,
        },
        "agent": {
            "agent_timeout": AGENT_TIMEOUT,
            "agent_evidence_n": AGENT_EVIDENCE_N,
            "agent_search_count": AGENT_SEARCH_COUNT,
        },
    }



