#!/usr/bin/env python3
"""
Script to populate dataset.json with RAG answers for questions from question.json.
Supports optional user preference injection to mirror personalized responses.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the current directory to Python path to import local modules
sys.path.append(str(Path(__file__).parent))

from rag.agentic_workflow import FitnessKnowledgeSystem
from rag.vanilla_workflow import VanillaFitnessSystem, create_vanilla_fitness_system
from rag.evaluation.ragas.adapters import extract_answer_and_contexts
from rag.evaluation.preferences import load_preferences

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_questions(question_file: Path) -> List[str]:
    """Load questions from JSON file."""
    try:
        with open(question_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            questions = data.get('questions', [])
            logger.info(f"Loaded {len(questions)} questions from {question_file}")
            return questions
    except Exception as e:
        logger.error(f"Error loading questions from {question_file}: {e}")
        return []

def load_existing_dataset(dataset_file: Path) -> List[Dict[str, Any]]:
    """Load existing dataset if it exists."""
    if dataset_file.exists():
        try:
            with open(dataset_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading existing dataset {dataset_file}: {e}")

    logger.info("Creating new dataset file")
    return []

async def query_system(
    system, question: str, preferences: Optional[str] = None, vanilla: bool = False
) -> Dict[str, Any]:
    """Query the system (RAG or vanilla) for a single question."""
    try:
        if vanilla:
            # Vanilla system returns dict directly
            answer_response = await system.query(question, preferences=preferences)
            answer_text = answer_response.get("answer", "")

            return {
                "question": question,
                "ground_truth": answer_text,
                "status": "success",
                "preferences": preferences,
            }
        else:
            # RAG system returns AnswerResponse object
            answer_response = await system.query(question, preferences=preferences)

            if answer_response and hasattr(answer_response, 'session') and answer_response.session:
                answer_text, contexts, context_ids = extract_answer_and_contexts(answer_response)

                return {
                    "question": question,
                    "ground_truth": answer_text,
                    "contexts": contexts,
                    "context_ids" : context_ids,
                    "status": "success",
                    "preferences": preferences,
                }
            else:
                logger.warning(f"No valid response for question: {question}")
                return {
                    "question": question,
                    "ground_truth": "Tidak dapat menghasilkan jawaban untuk pertanyaan ini.",
                    "contexts": [],
                    "context_ids": [],
                    "status": "error",
                    "preferences": preferences,
                }

    except Exception as e:
        logger.error(f"Error querying system for '{question}': {e}")
        error_msg = f"Error: {str(e)}"
        if vanilla:
            return {
                "question": question,
                "ground_truth": error_msg,
                "status": "error",
                "preferences": preferences,
            }
        else:
            return {
                "question": question,
                "ground_truth": error_msg,
                "contexts": [],
                "context_ids": [],
                "status": "error",
                "preferences": preferences,
            }

async def populate_dataset(
    questions: List[str],
    dataset_file: Path,
    preferences: Optional[str] = None,
    vanilla: bool = False,
) -> None:
    """Populate dataset with answers for all questions."""
    if vanilla:
        # Initialize vanilla system
        logger.info("Initializing Vanilla Fitness System...")
        system = await create_vanilla_fitness_system()
    else:
        # Initialize RAG system
        logger.info("Initializing Fitness Knowledge System...")
        system = FitnessKnowledgeSystem(
            docs_dir="./data/sources/processed",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            auto_index=True
        )

        # Build index if needed
        if system.has_documents():
            logger.info("Building index...")
            await system.build_index()

    # Load existing dataset
    existing_data = load_existing_dataset(dataset_file)

    # Check for duplicate questions
    existing_questions = {item.get("question") for item in existing_data if item.get("question")}

    # Query each question
    results = []
    for i, question in enumerate(questions, 1):
        logger.info(f"Processing question {i}/{len(questions)}: {question[:50]}...")

        # Skip if question already exists
        if question in existing_questions:
            logger.info(f"Question already exists, skipping: {question}")
            continue

        result = await query_system(system, question, preferences=preferences, vanilla=vanilla)
        results.append(result)

    # Combine existing data with new results
    all_data =  [*existing_data, *results]

    # Save to file
    try:
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Successfully saved {len(all_data)} entries to {dataset_file}")
        logger.info(f"Added {len(results)} new entries")

    except Exception as e:
        logger.error(f"Error saving dataset to {dataset_file}: {e}")
        raise

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate evaluation dataset with optional user preferences.")
    parser.add_argument("--questions-file", type=Path, default=Path("./data/evaluation/question.json"), help="Path to input questions JSON.")
    parser.add_argument("--dataset-file", type=Path, default=Path("./data/evaluation/dataset.json"), help="Path to output dataset JSON.")
    parser.add_argument("--preferences-text", type=str, help="Inline user preference block applied to every question.")
    parser.add_argument("--preferences-file", type=str, help="Path to a JSON or plain text file describing preferences.")
    parser.add_argument("--use-default-preferences", action="store_true", help="Apply the bundled dummy preference profile.")
    parser.add_argument("--vanilla", action="store_true", help="Use vanilla (non-RAG) queries instead of RAG queries.")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    # Ensure directories exist
    args.dataset_file.parent.mkdir(parents=True, exist_ok=True)

    # Load questions
    questions = load_questions(args.questions_file)
    if not questions:
        logger.error("No questions found. Exiting.")
        return

    preferences = load_preferences(
        preferences_text=args.preferences_text,
        preferences_file=args.preferences_file,
        use_default_preferences=args.use_default_preferences,
    )

    output_dataset = args.dataset_file
    if preferences:
        output_dataset = output_dataset.with_name(
            f"{output_dataset.stem}-preferenced{output_dataset.suffix}"
        )
    if args.vanilla:
        output_dataset = output_dataset.with_name(
            f"{output_dataset.stem}-vanilla{output_dataset.suffix}"
        )

    if preferences:
        logger.info("Applying shared user preferences to all questions:\n%s", preferences)
    else:
        logger.info("Running without user preferences (baseline).")

    if args.vanilla:
        logger.info("Using vanilla (non-RAG) queries.")
    else:
        logger.info("Using RAG queries.")

    # Run the population
    logger.info("Writing dataset to %s", output_dataset)
    asyncio.run(populate_dataset(questions, output_dataset, preferences=preferences, vanilla=args.vanilla))

if __name__ == "__main__":
    main()
