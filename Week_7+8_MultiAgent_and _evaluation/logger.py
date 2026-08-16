import logging
import os
from datetime import datetime

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

os.makedirs(log_dir, exist_ok=True)


logger = logging.getLogger("MultiAgent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.NullHandler())


def log_interaction(user_query: str, final_answer: str):
    """SAVE QUERY AND ANSWER IN SPERATE LOG FILE EVERY TIME"""

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        log_filename = os.path.join(log_dir, f"interaction_{timestamp}.log")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write(f"{current_time} - Info - User Query: \n {user_query}\n")
            log_file.write(f"{current_time} - Info - Final Answer: \n {final_answer}\n")

            log_file.write(f"Agent Execution compelted ")

    except Exception as e:
        raise RuntimeError(f"Failed to save log interaction for error :{e}")
