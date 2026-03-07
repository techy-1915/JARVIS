"""Intelligent routing of prompts to appropriate AI models."""

import logging
import re

logger = logging.getLogger(__name__)

# Keywords for routing
CODE_KEYWORDS = [
    "code","coding","program","script","snippet","example code","complete code",
    "write code","generate code","implement","implementation","build","develop",

    # programming constructs
    "function","class","method","variable","loop","recursion","pointer",
    "array","linked list","stack","queue","tree","graph","structure",

    # debugging
    "debug","bug","error","fix","issue","crash","stacktrace","traceback",
    "segmentation fault","syntax error","runtime error","compile error",

    # software development
    "algorithm","data structure","logic implementation",
    "refactor","optimize code","performance","memory leak",

    # languages
    "python","javascript","typescript","java","c++","cpp","c language",
    "golang","go","rust","php","ruby","kotlin","swift","sql","bash",

    # dev ecosystem
    "api","endpoint","backend","frontend","database",
    "framework","library","sdk","package","module","dependency",

    # common coding terms
    "import","export","build system","compile","run program",
    "repository","git","commit","branch","pull request",

    # ai dev terms (important for your project)
    "vector database","embedding","token","prompt","llm",
    "transformer","model inference","fine tuning","dataset",
]

REASONING_KEYWORDS = [
    "analyze","analysis","reason","reasoning","logic","logical",
    "think","thought","consider","evaluate","assess",

    # explanation triggers
    "explain","why","how","how does","how can","what happens",
    "clarify","describe","elaborate","interpret",

    # comparison / evaluation
    "compare","contrast","difference","versus","vs",
    "advantages","disadvantages","pros and cons","trade-offs",

    # decision making
    "decide","choose","which is better","recommend",
    "suggest","best approach","best method","strategy",

    # planning / architecture
    "plan","planning","strategy","roadmap","design",
    "architecture","system design","workflow","process",

    # logical inference
    "infer","deduce","derive","conclude","justify",
    "argument","rationale","perspective",

    # scenario thinking
    "what if","scenario","hypothetical","prediction",
    "predict","future outcome","implication","consequence",

    # improvement / optimization reasoning
    "improve","optimize","enhance","better solution",

    # ai / research thinking
    "insight","observation","analysis of","explanation of",
]

CHAT_KEYWORDS = [
    "hello","hi","hey","thanks","thank you",
    "who are you","what can you do",
    "tell me","talk about","conversation",
    "opinion","thoughts"
]

CODE_PATTERNS = [
    r"```",
    r"\bdef\b",
    r"\bclass\b",
    r"\bfunction\b",
    r"\bimport\b",
    r"\breturn\b",
    r"\bfor\b",
    r"\bwhile\b",
    r"\{.*\}",
    r";",
    r"=",
    r"\(",
]
FORCE_CODE_KEYWORDS = [
    "write a program",
    "write code",
    "generate code",
    "debug this",
    "fix this code",
    "implement this",
    "complete code",
]


def classify_prompt(prompt: str) -> str:
    """Classify a prompt to determine which model should handle it.

    Args:
        prompt: User input text

    Returns:
        Model identifier: "phi3", "deepseek-coder", or "mistral"
    """
    prompt_lower = prompt.lower()
    #force code routing
    for kw in FORCE_CODE_KEYWORDS:
        if kw in prompt_lower:
            logger.info("Routing → deepseek-coder (force keyword: '%s')", kw)
            return "deepseek-coder"
    # debug override
    if "debug" in prompt_lower or "error" in prompt_lower:
        logger.info("Routing → deepseek-coder (debug override)")
        return "deepseek-coder"


    # Check for code-related requests
    code_score = sum(
        1 for kw in CODE_KEYWORDS if kw in prompt_lower
        
    )

    # Check for reasoning-related requests
    reasoning_score = sum(1 for kw in REASONING_KEYWORDS if kw in prompt_lower 
    )

    chat_score = sum(
        1 for kw in CHAT_KEYWORDS if kw in prompt_lower
    )

    has_code_pattern = any(
        re.search(pattern, prompt_lower) for pattern in CODE_PATTERNS
    )
    # Check for code patterns (backticks, file extensions, etc.)
    has_file_extension = bool(
        re.search(r"\.(py|js|java|cpp|rs|go|c|h|php|rb|kt|swift|sql)\b", prompt_lower)
    )

    # Routing logic
    if code_score >= 2 or has_code_pattern or has_file_extension:
        logger.info(
            "Routing → deepseek-coder (code_score=%d)", code_score
        )
        return "deepseek-coder"
    elif reasoning_score >= 2:
        logger.info(
            "Routing → mistral (reasoning_score=%d)",  reasoning_score
        )
        return "mistral"
    elif chat_score >= 1:
        logger.info(
            "Routing → phi3 (chat detected)")
        return "phi3"
    else:
        logger.info("Routing → phi3 (general chat)")
        return "phi3"
    
def get_system_prompt(model_type: str) -> str:
    """Get appropriate system prompt for the model.

    Args:
        model_type: One of "phi3", "deepseek-coder", "mistral".

    Returns:
        System prompt string.
    """
    prompts = {
        "phi3": (
            "You are JARVIS, an intelligent AI assistant designed to help users with "
            "general questions, explanations, and everyday conversations.\n\n"

            "Your responsibilities:\n"
            "- Respond clearly, concisely, and helpfully.\n"
            "- Use natural conversational language.\n"
            "- Explain concepts in a simple and structured way.\n"
            "- When relevant, provide examples to make explanations easier to understand.\n"
            "- If code is required, format it using proper markdown code blocks.\n\n"

            "Guidelines:\n"
            "- Be friendly and professional.\n"
            "- Avoid unnecessary verbosity.\n"
            "- Structure longer answers using headings or bullet points.\n"
            "- If the user asks something unclear, ask clarifying questions.\n\n"

            "Your goal is to provide helpful, accurate, and easy-to-understand responses."
        ),
        "deepseek-coder": (
            "You are JARVIS, an expert software engineer and programming assistant.\n\n"

            "Your responsibilities:\n"
            "- Write clean, correct, and efficient code.\n"
            "- Always follow best programming practices.\n"
            "- Provide complete and runnable code whenever possible.\n"
            "- Explain complex parts of the code clearly.\n\n"

            "Coding guidelines:\n"
            "- Use proper formatting and indentation.\n"
            "- Always wrap code inside markdown code blocks with the correct language tag.\n"
            "- Prefer readability and maintainability over clever tricks.\n"
            "- If debugging, identify the root cause before suggesting fixes.\n"
            "- If multiple solutions exist, briefly mention the best approach.\n\n"

            "When responding:\n"
            "1. Briefly explain the solution.\n"
            "2. Provide the code.\n"
            "3. Add comments where necessary.\n"
            "4. Mention important implementation details if relevant.\n\n"

            "Your goal is to produce production-quality programming solutions."
        ),
        "mistral": (
            "You are JARVIS, an analytical AI assistant specialized in reasoning, "
            "problem solving, and structured analysis.\n\n"

            "Your responsibilities:\n"
            "- Analyze problems carefully before answering.\n"
            "- Provide logical explanations and structured reasoning.\n"
            "- Break down complex ideas step by step.\n"
            "- Consider multiple perspectives when appropriate.\n\n"

            "Guidelines:\n"
            "- Organize responses using headings or bullet points.\n"
            "- Explain the reasoning behind conclusions.\n"
            "- When comparing ideas, clearly list advantages and disadvantages.\n"
            "- When proposing solutions, explain why they work.\n\n"

            "Your goal is to deliver clear, logical, and well-structured analysis."
        ),
    }
    return prompts.get(model_type, prompts["phi3"])
