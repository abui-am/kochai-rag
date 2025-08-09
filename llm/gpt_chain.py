"""
LangChain implementation for GPT-4 based response generation.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

SYSTEM_TEMPLATE = """You are an AI-powered fitness trainer assistant. Your role is to provide accurate, 
helpful fitness advice based on reliable sources. Always cite your sources when providing information.

When responding:
1. Be clear and concise
2. Use professional but friendly language
3. Include relevant source citations
4. Focus on factual, evidence-based information
5. Prioritize safety and proper form
6. Adapt advice for the user's level (beginner/intermediate/advanced)

PaperQA has found the following relevant information:

{context}

Question: {question}

Based on the context above, generate a helpful fitness answer. Make sure to:
1. Directly address the user's question
2. Include specific information from the sources
3. Cite sources when providing information
4. Add safety warnings when relevant
5. Suggest next steps or related topics if appropriate"""

def create_gpt_chain(model_name: str = "gpt-4o-mini") -> LLMChain:
    """
    Create a LangChain chain using GPT-4 for generating fitness responses.
    
    Args:
        model_name: The OpenAI model to use
        
    Returns:
        A configured LangChain LLMChain
    """
    # Initialize the language model
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=0.7
    )
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)
    
    # Create and return the chain
    return LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True
    )

def process_rag_response(
    chain: LLMChain,
    rag_result: Dict[str, Any],
    question: str
) -> Dict[str, Any]:
    """
    Process RAG results through the GPT chain to generate a final response.
    
    Args:
        chain: The LangChain LLMChain
        rag_result: Results from the RAG system
        question: Original user question
        
    Returns:
        Dict containing the final response and source information
    """
    # If PaperQA already provided an answer, use it
    if rag_result["answer"]:
        return {
            "response": rag_result["answer"],
            "source_context": rag_result["context"],
            "sources": rag_result["sources"]
        }
    
    # Otherwise, generate a response using GPT-4
    response = chain.invoke({
        "context": rag_result["context"],
        "question": question
    })
    
    return {
        "response": response["text"],
        "source_context": rag_result["context"],
        "sources": rag_result["sources"]
    }