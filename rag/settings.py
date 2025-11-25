"""
Centralized configuration for PaperQA settings and LLM models.
This module contains all tunable parameters for the fitness knowledge system,
making it easy to:
1. Track what settings are used for reproducibility
2. Generate evaluation reports with configuration details
3. Experiment with different parameter combinations
"""

from typing import Optional

from paperqa.prompts import CITATION_KEY_CONSTRAINTS, summary_prompt

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
ANSWER_LENGTH = "about 300 words, but can be longer"

# Maximum concurrent requests for RAG parallelism
MAX_CONCURRENT_REQUESTS = 10

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
    "\n8) If the answer still seems insufficient after several attempts with different evidence, terminate anyway by calling the {complete_tool_name} tool and summarize the best available findings and uncertainties."
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
    fitness_prompt = get_fitness_coach_prompt(user_preferences)

    return (
        "You are an AI assistant answering questions using ONLY the provided context.\n"
        "Your primary goals are:\n"
        "1) Answer the user's question directly and completely.\n"
        "2) Stay strictly faithful to the context.\n"
        "3) Use the fitness coach style ONLY for phrasing and tone, never to invent facts.\n\n"
        "Context:\n\n{context}\n\n"
        "----\n\n"
        "Question: {question}\n\n"
        "Internal reasoning protocol (do NOT include this in the final answer):\n"
        "1) Question Analysis:\n"
        "   - Identify the core intent of the question (e.g., 'berapa banyak', 'kapan', 'apa', 'mengapa', 'bagaimana').\n"
        "   - List the key slots the user is asking for (e.g., quantity, time, type, condition).\n"
        "   - Make sure your final answer explicitly fills these slots.\n"
        "\n"
        "2) Claim Extraction:\n"
        "   - Decompose your intended answer into minimal factual claims.\n"
        "   - Each claim must help answer the question; remove generic or redundant claims.\n"
        "\n"
        "3) Evidence Check:\n"
        "   - For each claim, identify ONE strongest supporting passage and its citation key from the context.\n"
        "   - Reject, weaken, or revise any claim that cannot be directly inferred from the context.\n"
        "\n"
        "4) Answer Relevancy Self-Check (IMPORTANT):\n"
        "   - If the answer is not relevant, revise or remove that sentence, or say that you cannot answer.\n"
        "   Use the following prompt to evaluate the relevance of the answer:\n"
        f"{ANSWER_RELEVANCE_PROMPT}\n"
        "\n"
        "5) Fitness Coach Persona (style only, not content):\n"
        "   - Use the following rules ONLY to shape tone, structure, and style of the visible answer, "
        "     but NEVER to override context or invent facts:\n"
        f"     {fitness_prompt}\n"
        "   - If there is any conflict between persona style and context faithfulness, ALWAYS follow the context and QA rules above.\n"
        "\n"
        "6) Faithfulness Self-Check (IMPORTANT):\n"
        "   - Verify that every sentence in your final answer is entailed by the context.\n"
        "   - If not entailed, revise or remove that sentence, or say that you cannot answer.\n\n"
        "• If the context provides broadly insufficient information, reply exactly:\n"
        f'  \"Aku tidak mengerti pertanyaan kamu. bisa coba jelaskan lagi?\" \n'
        "  and do NOT add anything else.\n"
        "• For each sentence that makes a factual claim, append the single strongest supporting citation key at the end, "
        "  like {example_citation}.\n"
        "• Only cite from the context above and only use the citation keys from the context. Do not concatenate citation keys.\n"
        f"{CITATION_KEY_CONSTRAINTS}"
        "• Prefer exact numbers, dates, names, and terminology exactly as stated in the context; avoid paraphrasing that changes meaning.\n"
        "• Do not invent entities, mechanisms, or results that are not stated or entailed by the context.\n\n"
        "{prior_answer_prompt}"
        "Answer in Indonesian ({answer_length}):"
    )


ANSWER_RELEVANCE_PROMPT= (
"""
You are evaluating the ANSWER RELEVANCE of a model's answer to a user's question.

Definition (based on RAGAS):
- An answer is relevant when it directly and appropriately addresses the original question.
- We do NOT consider factual correctness here.
- We penalize answers that are:
  • incomplete (missing key parts of the question)
  • off-topic
  • mostly generic or redundant
- Intuition: if the answer is good, you should be able to reconstruct the original question
  just from the answer.

Your task:
Given a QUESTION and an ANSWER, you must:
1) Infer what question someone might have asked to receive this answer.
2) Compare that inferred question to the original QUESTION.
3) Assign a relevance score between 0.0 and 1.0:
   - 1.0   → fully relevant, clearly answers all key parts.
   - 0.8-1 → mostly relevant, minor omissions or extra info.
   - 0.4-0.8 → partially relevant, only some aspects answered.
   - 0.0-0.4 → mostly irrelevant or generic.

Always respond in this JSON format (no extra text):
{{
  "inferred_question": "...",
  "analysis": "...",
  "score": <float between 0 and 1>
}}

====================
EXAMPLE 1 – LOW RELEVANCE
====================
QUESTION:
"Where is France and what is its capital?"

ANSWER:
"France is in western Europe."

YOUR EVALUATION:
{{
  "inferred_question": "Where is France located in Europe?",
  "analysis": "The answer only addresses the location of France, but completely ignores the part about its capital city. It answers only one of the two key slots: 'where' but not 'what capital'. This is incomplete and only partially relevant to the full question.",
  "score": 0.4
}}

====================
EXAMPLE 2 - HIGH RELEVANCE
====================
QUESTION:
"Where is France and what is its capital?"

ANSWER:
"France is located in western Europe, and its capital city is Paris."

YOUR EVALUATION:
{{
  "inferred_question": "Where is France located and what is the name of its capital city?",
  "analysis": "The answer directly addresses both parts of the question: the geographical location of France and the name of its capital. A reader could reconstruct the original question almost exactly from this answer.",
  "score": 0.98
}}

====================
EXAMPLE 3 - PARTIAL / MEDIUM RELEVANCE
====================
QUESTION:
"How much protein should I eat after a workout to support muscle growth?"

ANSWER:
"After a workout, it's important to eat a meal that supports recovery. You should focus on good nutrition and stay hydrated."

YOUR EVALUATION:
{{
  "inferred_question": "What should I do after a workout to recover better?",
  "analysis": "The answer talks about post-workout recovery in general (nutrition and hydration) but does not mention any specific amount of protein. It partially relates to the topic but fails to answer the key 'how much protein' slot.",
  "score": 0.5
}}
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


SUMMARIZATION_PROMPT  = (
    "Summarize the excerpt below to help answer a question.\n\n"
    "Excerpt from {citation}\n\n"
    "----\n\n{text}\n\n----\n\n"
    "Question: {question}\n\n"
    "Your task is NOT to answer the question directly. Instead, produce a detailed, "
    "evidence-focused summary that extracts all information from the excerpt that "
    "may help answer or reason about the question.\n\n"
    "summarize in english language\n"
    "Follow these rules:\n"
    "1) High Recall: Include every piece of potentially useful information, even if indirect. "
    "   Do not omit technical details, assumptions, equations, datasets, methods, limitations, or examples.\n"
    "2) Evidence Priority: Prefer direct quotes (use quotation marks) for claims, definitions, or key findings. "
    "   Include numerical values, metrics, thresholds, model sizes, datasets, or formulas whenever present.\n"
    "3) Structured Extraction: Capture relevant points such as objectives, methods, results, comparisons, "
    "   limitations, and contextual background if they relate to the question.\n"
    "4) Irrelevance Filter: If the excerpt has no content that could support answering the question, "
    '   respond with \"Not applicable\".\n'
    "5) Do NOT add external knowledge or assumptions—summarize only what is in the excerpt.\n"
    "6) Maintain neutrality; do not make conclusions or interpretations beyond the text.\n\n"
    "Internal reasoning protocol for relevance scoring (do not include in the output):\n"
    "1) Claim Extraction: Break the question into explicit and implicit claims or sub-questions.\n"
    "2) Evidence Mapping: For each claim, check whether the excerpt provides definitions, methods, results, "
    "   examples, background, or any information that could help address that claim.\n"
    "3) Overlap Assessment: Estimate how much of the excerpt is devoted to content related to the claims "
    "   (directly or indirectly) versus unrelated material.\n"
    "4) Strength Assessment: Consider how specific and actionable the evidence is (e.g., concrete numbers, "
    "   equations, empirical results, or precise definitions vs. only vague or high-level mentions).\n"
    "5) Scoring Rubric (1-10):\n"
    "   - 1-2: No meaningful relation to the question; almost entirely irrelevant.\n"
    "   - 3-4: Very weak relation; only sparse or vague connections to the question.\n"
    "   - 5-6: Partially relevant; some useful evidence but limited coverage or specificity.\n"
    "   - 7-8: Strong relevance; substantial evidence that meaningfully supports answering the question.\n"
    "   - 9-10: Highly focused and densely relevant; most of the excerpt is directly useful for the question.\n"
    "6) Final Check: Choose the score that best reflects both the amount and strength of relevant evidence, "
    "   being consistent with the rubric across all examples.\n\n"
    "At the end of your response:\n"
    "• First, provide the relevant information summary.\n"
    "• Then, on a new line, provide ONLY an integer relevance score from 1-10 (no explanation).\n\n"
    "Relevant Information Summary ({summary_length}):"
)
