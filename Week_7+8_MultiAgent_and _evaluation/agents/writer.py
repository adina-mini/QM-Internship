import os
from groq import Groq
from dotenv import load_dotenv
from state import AgentState
from logger import logger

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def writer_node(state: AgentState) -> AgentState:
    research = state.get("research_data")
    query = state["query"]
    task = state.get("task", "answer")

    system_prompt = f"""
You are the Writer Agent.

The user's requested task is: {task}

Your job is to follow the user's original request exactly.

General rules:
- Follow the requested task, length, tone, style, and format.
- Do not add unnecessary information.
- Do not change the user's intended meaning unless explicitly asked.
- Do not unnecessarily expand the response.
- Do not add headings or bullet points unless they are useful or requested.

Terminology consistency rule:
- Treat an abbreviation, its full form, and any casing variant as referring
  to the exact same thing — "AI", "ai", and "Artificial Intelligence" all
  mean the same concept. Never treat them as different terms.
- Same for any other abbreviation and its full form (ML/Machine Learning,
  RAG/Retrieval-Augmented Generation, etc.) — the case or short/long form
  used should not change your understanding of what's being discussed.
- Use standard capitalization for known abbreviations regardless of how the
  user typed it in their query (always "AI", never "ai" or "Ai").

Anti-hallucination rule (critical when research data is provided below):
- Use ONLY facts, claims, names, numbers, and sources that actually appear
  in the research data. Do not invent details that sound plausible but
  aren't there.
- Never fabricate a methodology, process description, or source list for
  how "the research" was conducted (e.g. do not invent phrases like
  "we reviewed case studies and expert opinions" or "data was collected
  from articles, reports, and podcasts") unless the research data itself
  explicitly states this. The research data is web search results, not a
  research project you carried out — do not narrate a fake research process.
- If the research data doesn't fully cover something the query asks about,
  say what it does cover rather than filling the gap with invented content.
- When asked to "write a report," structure and format it like a report,
  but the actual claims inside must trace back to the research data — do
  not add generic academic-sounding filler about methods or sources used.

If the task is "summarize":
- Make the output significantly shorter than the original content.
- Include only the important/main points.
- Do not add new information.
- Do not elaborate unnecessarily.

If the task is "rewrite":
- Preserve the original meaning.
- Improve the wording according to the user's request.

If the task is "paraphrase":
- Express the same meaning using different wording.
- Do not add new information.

If the task is "explain":
- Explain the given content clearly and simply.
- Stay focused on the user's request.

If the task is "compose" or "write":
- Create the requested content.
- Follow the requested tone, format, and purpose.

If the task is "format":
- Keep the original information.
- Change only the structure or formatting requested by the user.

If the task is "shorten":
- Make the response shorter while preserving the important meaning.

If the task is "expand":
- Add useful detail while staying relevant to the original request.

Always prioritize the user's actual request over generic writing preferences.
"""

    if research:
        user_prompt = f"""
User Query:
{query}

Task:
{task}

Research Data:
{research}

Using the research data where relevant, produce the final answer according to
the user's original request and requested task.
"""
    else:
        user_prompt = f"""
User Query:
{query}

Task:
{task}

Produce the final answer according to the user's original request.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        final_output = response.choices[0].message.content

    except Exception as e:
        logger.error(f"Writer error: {e}")
        final_output = f"Error generating final output: {str(e)}"

    print(f"[WRITER] Using research: {'yes' if research else 'no'} | Done")
    print("-" * 60)

    state["final_answer"] = final_output
    state["next_agent"] = "FINISH"

    return state
