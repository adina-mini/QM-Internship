import os
from groq import Groq
from dotenv import load_dotenv
from langsmith import traceable
from logger import logger

load_dotenv()

judge_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

JUDGE_MODEL = "llama-3.3-70b-versatile"  # same model as Writer — best judging
# quality. Note: this means a full
# 10/10 eval run doubles total token
# usage (10 generation + 10 judge
# calls), so it can hit Groq's free
# tier daily token cap faster.

JUDGE_PROMPT = """
You are a strict evaluation judge for an AI multi-agent system's output.
Score the final answer on these three dimensions, each 0-10:

1. HALLUCINATION: How well every claim, fact, number, or name in the answer
   is traceable to the research data (or is safe general/stable knowledge
   when no research was used). 10 = fully grounded, nothing invented.
   0 = contains fabricated specifics not supported by the research data.

2. RELEVANCE: How directly the answer addresses the actual query. 10 = fully
   on-topic and answers what was asked. 0 = off-topic or ignores the query.

3. TASK_ADHERENCE: How well the answer follows the requested task type and
   format (e.g. if asked to "shorten," is it actually shorter; if asked to
   "format as bullets," is it bulleted). 10 = perfectly matches the requested
   task. 0 = ignores the task instruction entirely.

Be strict — do not give high scores just because the answer sounds fluent
or professional. Only judge based on grounding, relevance, and instruction-
following.

Query: {query}
Task: {task}
Research Data Used: {research_data}
Final Answer: {final_answer}

Return ONLY this exact format, nothing else:
HALLUCINATION: <score>
RELEVANCE: <score>
TASK_ADHERENCE: <score>
REASON: <one short sentence explaining the lowest score>
"""


def _parse_score(line: str) -> int:
    try:
        return int(line.split(":", 1)[1].strip())
    except (ValueError, IndexError):
        return -1  # unparseable, flagged downstream rather than assumed


@traceable(name="Judge", run_type="chain")
def judge_response(query: str, task: str, research_data, final_answer: str) -> dict:
    """Score a single agent output on hallucination, relevance, and task
    adherence using an LLM judge. Returns a dict of scores + reason.
    On any failure, scores are -1 (not 0) so failures are visibly distinct
    from genuinely bad answers."""

    prompt = JUDGE_PROMPT.format(
        query=query,
        task=task or "unknown",
        research_data=(
            research_data
            if research_data
            else "None (no research was used for this task)"
        ),
        final_answer=final_answer or "(empty)",
    )

    result = {
        "hallucination": -1,
        "relevance": -1,
        "task_adherence": -1,
        "reason": "Judge call failed or was unparseable.",
    }

    try:
        response = judge_client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        output = response.choices[0].message.content.strip()

        for line in output.splitlines():
            if line.upper().startswith("HALLUCINATION:"):
                result["hallucination"] = _parse_score(line)
            elif line.upper().startswith("RELEVANCE:"):
                result["relevance"] = _parse_score(line)
            elif line.upper().startswith("TASK_ADHERENCE:"):
                result["task_adherence"] = _parse_score(line)
            elif line.upper().startswith("REASON:"):
                result["reason"] = line.split(":", 1)[1].strip()

    except Exception as e:
        logger.error(f"Judge error: {e}")
        result["reason"] = f"Judge call raised an exception: {e}"

    return result
