import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graph import app
from test_cases import test_cases
from langchain_core.messages import HumanMessage
from judge import judge_response

EVAL_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_logs")
os.makedirs(EVAL_LOG_DIR, exist_ok=True)


async def run_test(test_case):
    query = test_case["query"]
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "",
        "query": "",
        "task": "",
        "research_data": None,
        "final_answer": None,
    }

    final_state = await app.ainvoke(initial_state)
    return final_state


def check_assertions(test_case, final_state):
    """Compare actual output against expected_workflow + assertions.
    Returns (passed: bool, failures: list[str])."""
    failures = []
    final_answer = final_state.get("final_answer", "") or ""
    word_count = len(final_answer.split())

    # research usage: inferred from whether research_data got populated
    actual_research = final_state.get("research_data") is not None
    expected_research = test_case.get("expected_workflow", {}).get("expected_research")
    if expected_research is not None and actual_research != expected_research:
        failures.append(
            f"expected_research={expected_research} but got research_data_present={actual_research}"
        )

    assertions = test_case.get("assertions", {})

    if "max_length_words" in assertions and word_count > assertions["max_length_words"]:
        failures.append(
            f"max_length_words={assertions['max_length_words']} but got {word_count} words"
        )

    if "min_length_words" in assertions and word_count < assertions["min_length_words"]:
        failures.append(
            f"min_length_words={assertions['min_length_words']} but got {word_count} words"
        )

    for phrase in assertions.get("must_contain", []):
        if phrase.lower() not in final_answer.lower():
            failures.append(f"must_contain '{phrase}' — not found in output")

    for phrase in assertions.get("must_not_contain", []):
        if phrase.lower() in final_answer.lower():
            failures.append(f"must_not_contain '{phrase}' — found in output")

    return (len(failures) == 0), failures


async def main():
    print("EVALUATION")
    print("\n")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(EVAL_LOG_DIR, f"eval_{timestamp}.log")

    results = []

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"EVALUATION RUN — {timestamp}\n")
        log_file.write("=" * 60 + "\n\n")

        for test_case in test_cases:
            test_id = test_case["test_id"]
            category = test_case["category"]
            print(f"Running test case {test_id} of category {category}")

            try:
                final_state = await run_test(test_case)
                final_answer = final_state.get("final_answer", "")
                task = final_state.get("task", "")
                research_data = final_state.get("research_data")
                research_used = research_data is not None

                passed, failures = check_assertions(test_case, final_state)
                status = "PASS" if passed else "FAIL"

                judge_scores = judge_response(
                    query=test_case["query"],
                    task=task,
                    research_data=research_data,
                    final_answer=final_answer,
                )

                print(f"Result: {status}")
                print(
                    f"Judge — Hallucination: {judge_scores['hallucination']}/10 | "
                    f"Relevance: {judge_scores['relevance']}/10 | "
                    f"Task Adherence: {judge_scores['task_adherence']}/10"
                )
                print(final_answer)
                print("\n")

                results.append((test_id, category, status, judge_scores))

                log_file.write(f"[{test_id}] {category} — {status}\n")
                log_file.write(f"Query: {test_case['query']}\n")
                log_file.write(f"Task: {task} | Research used: {research_used}\n")
                if failures:
                    log_file.write("Failures:\n")
                    for f in failures:
                        log_file.write(f"  - {f}\n")
                log_file.write(
                    f"Judge Scores — Hallucination: {judge_scores['hallucination']}/10 | "
                    f"Relevance: {judge_scores['relevance']}/10 | "
                    f"Task Adherence: {judge_scores['task_adherence']}/10\n"
                )
                log_file.write(f"Judge Reason: {judge_scores['reason']}\n")
                log_file.write(f"Output:\n{final_answer}\n")
                log_file.write("-" * 60 + "\n\n")

            except Exception as e:
                print(f"ERROR: {e}")
                results.append((test_id, category, "ERROR", None))
                log_file.write(f"[{test_id}] {category} — ERROR: {e}\n")
                log_file.write("-" * 60 + "\n\n")

        passed_count = sum(1 for _, _, s, _ in results if s == "PASS")
        total = len(results)

        judged = [r for r in results if r[3] is not None and r[3]["hallucination"] >= 0]
        avg_hallucination = (
            sum(r[3]["hallucination"] for r in judged) / len(judged) if judged else 0
        )
        avg_relevance = (
            sum(r[3]["relevance"] for r in judged) / len(judged) if judged else 0
        )
        avg_task_adherence = (
            sum(r[3]["task_adherence"] for r in judged) / len(judged) if judged else 0
        )

        summary = f"\nSUMMARY: {passed_count}/{total} passed\n"
        for test_id, category, status, judge_scores in results:
            score_str = ""
            if judge_scores:
                score_str = (
                    f" | H:{judge_scores['hallucination']} "
                    f"R:{judge_scores['relevance']} "
                    f"T:{judge_scores['task_adherence']}"
                )
            summary += f"  {test_id} ({category}): {status}{score_str}\n"

        summary += (
            f"\nAverage Judge Scores (out of 10):\n"
            f"  Hallucination:   {avg_hallucination:.1f}\n"
            f"  Relevance:       {avg_relevance:.1f}\n"
            f"  Task Adherence:  {avg_task_adherence:.1f}\n"
        )

        print(summary)
        log_file.write(summary)

    print(f"Eval log saved to: {log_path}")


if __name__ == "__main__":
    asyncio.run(main())
