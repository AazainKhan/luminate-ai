# agents/planner_heuristics.py
import re
from typing import List, Dict

# Math-related patterns
MATH_TOKENS = [
    r"\bsolve\b", r"\bcompute\b", r"\bcalculate\b", r"\bevaluate\b",
    r"\bderivative\b", r"\bintegral\b", r"\blimit\b", r"\beigen(value|vector)s?\b",
    r"\bmatrix\b", r"\bgradient\b", r"\bmse\b", r"\bvariance\b", r"\bprobability\b",
    r"[=<>±≈∑∫√^]", r"\bfor x\s*=", r"\by\s*=", r"\bf\(x\)", r"\bP\(", r"\bE\(", r"\bVar\(",
    r"\bneural network\b", r"\bdeep learning\b", r"\bmachine learning\b", r"\bai\b"
]

# Concept explanation patterns
CONCEPT_TOKENS = [
    r"\bexplain\b", r"\bwhat is\b", r"\boverview\b", r"\bcompare\b", r"\bdifference between\b",
    r"\bintuition\b", r"\bconcept\b", r"\btheory\b", r"\bhow does\b", r"\bwhat are\b"
]

# Keywords for detecting off-topic queries
OFF_TOPIC_TOKENS = [
    # Food and recipes
    r'\bpizza\b', r'\bcoffee\b', r'\btea\b', r'\brecipe\b', r'\bcook\b',
    r'\bfood\b', r'\brestaurant\b', r'\bcooking\b', r'\bmeal\b',
    
    # Weather
    r'\bweather\b', r'\btemperature\b', r'\brain\b', r'\bsnow\b', r'\bsunny\b',
    r'\bforecast\b', r'\bhumid\b', r'\bstorm\b', r'\bwindy\b',
    
    # Sports
    r'\bsports\b', r'\bfootball\b', r'\bbasketball\b', r'\bsoccer\b',
    r'\btennis\b', r'\bgolf\b', r'\bbaseball\b', r'\bhockey\b',
    
    # Entertainment
    r'\bmovie\b', r'\bnetflix\b', r'\bdisney\b', r'\bprime video\b',
    r'\bcelebrity\b', r'\bactor\b', r'\bactress\b', r'\bhollywood\b',
    r'\btaylor swift\b', r'\bbeyonce\b', r'\bbts\b', r'\bartist\b',
    r'\bsinger\b', r'\bactor\b', r'\bactress\b', r'\bentertainment\b',
    r'\bmusic\b', r'\bsong\b', r'\balbum\b', r'\bconcert\b',
    
    # Greetings and small talk
    r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgood morning\b',
    r'\bgood afternoon\b', r'\bgood evening\b', r'\bgood night\b',
    r'\bhow are you\b', r'\bwhat\'?s up\b', r'\bhowdy\b',
    
    # Jokes and fun
    r'\bjoke\b', r'\bfunny\b', r'\blol\b', r'\blmao\b', r'\bhaha\b',
    
    # News and current events
    r'\bnews\b', r'\bheadline\b', r'\bcurrent event\b',
    
    # Games
    r'\bgame\b', r'\bgaming\b', r'\bplay\b', r'\bvideo game\b',
    r'\bplaystation\b', r'\bxbox\b', r'\bnintendo\b',
    
    # Time and date
    r'\bwhat time is it\b', r'\bwhat day is it\b',
    
    # Social media
    r'\binstagram\b', r'\btwitter\b', r'\btiktok\b', r'\bfacebook\b',
    
     # Shopping
    r'\bshop\b', r'\bbuy\b', r'\bpurchase\b', r'\bamazon\b', r'\bebay\b',
    
    # Personal
    r'\bhow old are you\b', r'\bwho made you\b', r'\bwho created you\b'
]

# Chat/meta patterns
CHAT_TOKENS = [
    r"\bwho are you\b", r"\bwhat can you do\b", r"\bhelp\b", r"\bhow do i use\b",
    r"\bhi\b|\bhello\b|\bhey\b", r"\bthanks\b|\bthank you\b"
]

# This section intentionally left blank - using the comprehensive OFF_TOPIC_TOKENS defined above

MATH_RE = re.compile("|".join(MATH_TOKENS), re.IGNORECASE)
CONCEPT_RE = re.compile("|".join(CONCEPT_TOKENS), re.IGNORECASE)
CHAT_RE = re.compile("|".join(CHAT_TOKENS), re.IGNORECASE)
EQUATION_RE = re.compile(r"[a-zA-Z]\s*=\s*[-+*/()\d.a-zA-Z]")

def heuristic_route(query: str) -> Dict:
    q = query.strip()
    hits: List[str] = []
    
    # Compile the off-topic regex
    OFF_TOPIC_RE = re.compile("|".join(OFF_TOPIC_TOKENS), re.IGNORECASE)
    
    # Check for off-topic queries first
    is_off_topic = bool(OFF_TOPIC_RE.search(q))
    if is_off_topic:
        print(f"[Heuristic] Detected off-topic query: {q}")
        return {
            "subtasks": [{
                "task": "reject",
                "payload": {
                    "type": "reject",
                    "reason": "This appears to be outside the scope of COMP 237 course material."
                }
            }],
            "rules_triggered": ["off_topic_regex"],
            "router_confidence": 0.9,
            "reasoning": "Query detected as off-topic based on keyword matching.",
            "llm_used": False
        }
    
    # Check for math, concept, and chat patterns
    is_math = bool(MATH_RE.search(q) or EQUATION_RE.search(q))
    is_concept = bool(CONCEPT_RE.search(q))
    is_chat = bool(CHAT_RE.search(q))

    if is_math:
        hits.append("math_regex")
    if is_concept:
        hits.append("concept_regex")
    if is_chat:
        hits.append("chat_regex")

    # Handle chat-only queries
    if is_chat and not (is_math or is_concept):
        return {
            "subtasks": [{
                "task": "chat", 
                "payload": {
                    "type": "chat",
                    "message": "meta/small-talk"
                }
            }],
            "rules_triggered": hits,
            "router_confidence": 0.9,
            "reasoning": "Query identified as chat/small-talk.",
            "llm_used": False
        }

    # Handle mixed explain + solve queries
    if is_math and is_concept:
        return {
            "subtasks": [
                {
                    "task": "explain", 
                    "payload": {
                        "type": "explain",
                        "topic": q
                    }
                },
                {
                    "task": "solve", 
                    "payload": {
                        "type": "solve",
                        "problem": q
                    }
                }
            ],
            "rules_triggered": hits,
            "router_confidence": 0.75,
            "reasoning": "Query contains both conceptual and problem-solving elements.",
            "llm_used": False
        }

    if is_math:
        return {
            "subtasks": [{
                "task": "solve",
                "payload": {
                    "type": "solve",
                    "problem": q
                }
            }],
            "rules_triggered": hits, 
            "router_confidence": 0.8,
            "reasoning": "Query identified as a problem to solve.",
            "llm_used": False
        }

    if is_concept:
        return {
            "subtasks": [{
                "task": "explain",
                "payload": {
                    "type": "explain",
                    "topic": q
                }
            }],
            "rules_triggered": hits, 
            "router_confidence": 0.8,
            "reasoning": "Query identified as a concept to explain.",
            "llm_used": False
        }

    # default to explain if unknown
    return {
        "subtasks": [{
            "task": "explain",
            "payload": {
                "type": "explain",
                "topic": q
            }
        }],
        "rules_triggered": hits, 
        "router_confidence": 0.55,
        "reasoning": "Defaulting to explanation as fallback.",
        "llm_used": False
    }
