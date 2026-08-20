import os
from groq import Groq
from dotenv import load_dotenv

from state import AgentState
from logger import logger

# 1. Mechanical tasks (whitelist) NEVER need research — force writer,even if the LLM second-guessed itself and picked researcher.
# 2. Non-mechanical tasks NEVER skip research — force researcher,even if the LLM picked writer.

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VALID_TASKS = {
    "summarize",
    "rewrite",
    "paraphrase",
    "format",
    "shorten",
    "expand",
    "explain",
    "compose",
    "write",
    "answer",
    "research",
    "other",
}
VALID_AGENTS = {"writer", "researcher"}

# The ONLY tasks where Writer is allowed to run without research first —

WRITER_ONLY_TASKS = {
    "summarize",
    "rewrite",
    "paraphrase",
    "format",
    "shorten",
    "expand",
    "compose",
}

SYSTEM_PROMPT = """
You are the Planner Agent of a multi-agent system with two downstream agents:

- WRITER: does the actual writing/editing. It has NO web access and no
  reliable topic expertise — think of it as someone who is decent at
  mechanical writing tasks (fixing grammar, rewriting, summarizing text
  that's already given, formatting, drafting a plain email) but is NOT
  knowledgeable enough to write accurately about a topic on its own.
- RESEARCHER: has a live web search tool. It looks things up and hands the
  findings + the original query to the Writer, which then produces the
  final answer using that research.

Route to WRITER ONLY if the task is purely mechanical and needs no topic
knowledge — the user already gave the content/text, or it's a short generic
message (like a basic email) that doesn't depend on facts about any subject:
- summarize (text is already given)
- rewrite / paraphrase (text is already given)
- format (content is already given)
- shorten / expand (text is already given)
- compose a short generic message (e.g. "write a mail asking for leave")

Route to RESEARCHER for everything else — this includes writing ANYTHING
that requires knowledge about a topic: blog posts, articles, social media
posts, reports, research papers, explanations of concepts, answering
questions, or any "write about X" / "write a post on X" style request.
Even if you think you already know the topic, treat the Writer as not
knowledgeable enough to be trusted alone — get it researched first so the
final output is grounded.

Possible task types:
summarize, rewrite, paraphrase, format, shorten, expand, explain, compose,
write, answer, research, other

Examples:

"Summarize this paragraph: [pasted text]"
TASK: summarize
NEXT_AGENT: writer

"Rewrite this email professionally: [pasted email]"
TASK: rewrite
NEXT_AGENT: writer

"Format these skills into a bullet list: Python, LangGraph, ChromaDB."
TASK: format
NEXT_AGENT: writer

"Write a mail to my manager asking for leave tomorrow."
TASK: compose
NEXT_AGENT: writer
(Short generic message, no topic knowledge required.)

"Explain how RAG works and describe its main components."
TASK: explain
NEXT_AGENT: researcher
(Needs accurate topic knowledge — Writer alone isn't trusted for this.)

"What is an AI agent?"
TASK: explain
NEXT_AGENT: researcher

"Write a blog post about productivity tips."
TASK: write
NEXT_AGENT: researcher
(Requires real content on a topic — Writer alone would just make things up.)

"What are the latest AI trends in 2026?"
TASK: research
NEXT_AGENT: researcher

"Find the latest news about AI agents and summarize the developments."
TASK: research
NEXT_AGENT: researcher

Return ONLY this format, nothing else:

TASK: <task>
NEXT_AGENT: writer/researcher
"""

FORMAT_REMINDER = (
    "Reply with ONLY the two lines: TASK: <task> and NEXT_AGENT: writer/researcher"
)


def _parse(output: str):
    """Pull TASK and NEXT_AGENT out of the model's reply. Returns (task, agent),
    either of which can be None if that line wasn't present/valid."""
    task = None
    agent = None
    for line in output.splitlines():
        if line.upper().startswith("TASK:"):
            candidate = line.split(":", 1)[1].strip().lower()
            if candidate in VALID_TASKS:
                task = candidate
        elif line.upper().startswith("NEXT_AGENT:"):
            candidate = line.split(":", 1)[1].strip().lower()
            if candidate in VALID_AGENTS:
                agent = candidate
    return task, agent


def _ask_planner(query: str, prior_output: str | None = None):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    if prior_output is not None:
        messages.append({"role": "assistant", "content": prior_output})
        messages.append({"role": "user", "content": FORMAT_REMINDER})

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def planner_node(state: AgentState) -> AgentState:

    query = state["messages"][-1].content if state["messages"] else ""
    state["query"] = query

    print("-" * 60)

    task, agent = None, None

    try:
        output = _ask_planner(query)
        task, agent = _parse(output)

        if task is None or agent is None:
            # instead of silently guessing which agent to use.
            logger.error(f"Planner: unparseable output, retrying. Got: {output!r}")
            retry_output = _ask_planner(query, prior_output=output)
            retry_task, retry_agent = _parse(retry_output)
            task = task or retry_task
            agent = agent or retry_agent

    except Exception as e:
        logger.error(f"Planner error: {e}")

    if task is None or agent is None:
        # Both attempts failed
        logger.error(
            "Planner: no valid decision after retry — defaulting to researcher due to failure, not policy."
        )
        task = task or "answer"
        agent = agent or "researcher"

    if task in WRITER_ONLY_TASKS and agent != "writer":
        logger.error(
            f"Planner: LLM picked researcher for mechanical task '{task}' — overriding to writer."
        )
        agent = "writer"
    elif task not in WRITER_ONLY_TASKS and agent != "researcher":
        logger.error(
            f"Planner: LLM picked writer for non-mechanical task '{task}' — overriding to researcher."
        )
        agent = "researcher"

    state["task"] = task
    state["next_agent"] = agent
    print(f"[PLANNER] Task: {task} | Next: {agent.upper()}")

    return state
