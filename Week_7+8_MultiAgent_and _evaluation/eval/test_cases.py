test_cases = [
    {
        "test_id": "tc_001",
        "category": "summarization",
        "query": "Summarize the text: 'Life is an unpredictable journey defined by chance, surprise, and sudden changes where much of our existence unfolds through random moments—a brief meeting, a sudden challenge, or an unpredicted joy—reminding us that while we try to control our path, true beauty often lies in learning to adapt to the chaos.'",
        "expected_workflow": {
            "agents_invoked": ["planner", "writer"],
            "expected_research": False,
        },
        "assertions": {
            "max_length_words": 50,
            "must_contain": ["unpredictable", "adapt", "chaos"],
        },
        "expected_behavior": "Should produce a concise summary without triggering the research agent.",
    },
    {
        "test_id": "tc_002",
        "category": "email_writing",
        "query": "Write a professional email to a company asking about an AI/ML internship opportunity.",
        "expected_workflow": {
            "agents_invoked": ["planner", "writer"],
            "expected_research": False,
        },
        "assertions": {
            "must_contain": ["Dear", "internship"],
            "must_not_contain": ["research data"],
        },
        "expected_behavior": "Should write a professional internship inquiry email without using external research.",
    },
    {
        "test_id": "tc_003",
        "category": "rewrite",
        "query": "Rewrite this sentence professionally: 'I want this internship because I need experience and I really want to learn AI.'",
        "expected_workflow": {
            "agents_invoked": ["planner", "writer"],
            "expected_research": False,
        },
        "assertions": {
            "max_length_words": 50,
            "must_contain": ["experience", "AI", "Artificial Intelligence"],
        },
        "expected_behavior": "Should improve the wording while preserving the original meaning.",
    },
    {
        "test_id": "tc_004",
        "category": "formatting",
        "query": "Format these skills into a professional bullet-point list: Python, LangGraph, LangChain, ChromaDB, Tavily.",
        "expected_workflow": {
            "agents_invoked": ["planner", "writer"],
            "expected_research": False,
        },
        "assertions": {
            "must_contain": ["Python", "LangGraph", "LangChain", "ChromaDB", "Tavily"]
        },
        "expected_behavior": "Should preserve all the provided skills and format them as a clear list.",
    },
    {
        "test_id": "tc_005",
        "category": "shortening",
        "query": "Shorten this text: 'Artificial intelligence is transforming many industries by helping organizations automate repetitive tasks, analyze large amounts of data, improve decision making, and create new products and services.'",
        "expected_workflow": {
            "agents_invoked": ["planner", "writer"],
            "expected_research": False,
        },
        "assertions": {
            "max_length_words": 30,
            "must_contain": ["artificial intelligence"],
        },
        "expected_behavior": "Should make the text significantly shorter while preserving its main meaning.",
    },
    {
        "test_id": "tc_006",
        "category": "current_research",
        "query": "What are the latest AI trends in 2026?",
        "expected_workflow": {
            "agents_invoked": ["planner", "researcher", "writer"],
            "expected_research": True,
        },
        "assertions": {"min_length_words": 30, "must_contain": ["AI"]},
        "expected_behavior": "Should use the research agent because the query asks for current information.",
    },
    {
        "test_id": "tc_007",
        "category": "latest_news",
        "query": "Find the latest news about AI agents and summarize the important developments.",
        "expected_workflow": {
            "agents_invoked": ["planner", "researcher", "writer"],
            "expected_research": True,
        },
        "assertions": {"min_length_words": 30, "must_contain": ["AI", "agents"]},
        "expected_behavior": "Should research current information and then provide a concise summary of the findings.",
    },
    {
        "test_id": "tc_008",
        "category": "research_and_writing",
        "query": "Research the latest developments in AI agent frameworks and write a short report about them.",
        "expected_workflow": {
            "agents_invoked": ["planner", "researcher", "writer"],
            "expected_research": True,
        },
        "assertions": {"min_length_words": 50, "must_contain": ["AI", "agent"]},
        "expected_behavior": "Should first gather current information and then use the research to produce a structured report.",
    },
    {
        "test_id": "tc_009",
        "category": "general_question",
        "query": "What is an AI agent?",
        "expected_workflow": {
            "agents_invoked": ["planner", "researcher", "writer"],
            "expected_research": True,
        },
        "assertions": {"min_length_words": 30, "must_contain": ["AI", "agent"]},
        "expected_behavior": "Should provide a clear explanation using research before generating the final answer.",
    },
    {
        "test_id": "tc_010",
        "category": "explanation",
        "query": "Explain how RAG works and describe its main components.",
        "expected_workflow": {
            "agents_invoked": ["planner", "researcher", "writer"],
            "expected_research": True,
        },
        "assertions": {"min_length_words": 40, "must_contain": ["RAG"]},
        "expected_behavior": "Should research the topic and provide a clear explanation of RAG and its main components.",
    },
]
