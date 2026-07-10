# Week 3 – Memory-Enabled AI Agent

## Overview

This project extends the Week 2 Tool Calling Agent by implementing persistent memory capabilities inspired by modern Large Language Model (LLM) architectures. The agent is designed to remember previous conversations, retain important user information, summarize older interactions, and continue using external tools when required.

Instead of treating every interaction as a new conversation, the agent maintains different forms of memory to provide more contextual and personalized responses while efficiently managing the model's context window.

---

## Features

- Persistent conversation history
- Automatic conversation summarization using an LLM
- Long-term entity memory extraction
- Hybrid memory architecture (Recent Memory + Summary Memory + Entity Memory)
- Automatic memory management and trimming
- Persistent storage using JSON files
- Tool Calling support
  - Weather Information
  - Mathematical Calculations
  - Currency Conversion
- Memory inspection command (`memory`)
- Asynchronous architecture using Python AsyncIO

---

## Project Structure

```
Week3_Memory/
│
├── agent.py
├── .env
├── README.md
├── requirements.txt
│
├── chat_history.json
├── memory_state.json
└── entities.json
```

---

## Memory Architecture

The project implements three different types of memory.

### 1. Conversation History

Recent user and assistant messages are stored in `chat_history.json`.

This acts as the agent's short-term memory and allows it to remember the latest interactions across multiple sessions.

---

### 2. Summary Memory

When the conversation history exceeds the configured limit, older messages are automatically summarized by the LLM instead of simply deleting them.

The generated summary preserves important context while significantly reducing the number of tokens sent to the model. The summary is stored in `memory_state.json` and is included in future prompts.

---

### 3. Entity Memory

The agent automatically extracts long-term information about the user, such as:

- Name
- Location
- University
- Major
- Profession
- Preferences
- Goals

The extracted entities are stored in `entities.json` and reused in future conversations to provide more personalized responses.

---

## Tool Calling

The agent supports automatic function calling for specific tasks.

### Weather Tool

Retrieves current weather information for a requested location.

### Calculator Tool

Safely evaluates mathematical expressions.

### Currency Converter

Converts between currencies using live exchange rates.

The LLM automatically decides whether a tool should be used based on the user's request.

---

## Memory Workflow

```
User Prompt
      │
      ▼
Load Conversation Summary
      │
Load Entity Memory
      │
Load Recent Conversation History
      │
Send Context to LLM
      │
Tool Required?
      │
 ┌────┴────┐
 │         │
Yes        No
 │         │
Execute    Direct
Tool       Response
 │         │
 └────┬────┘
      ▼
Extract Entities
      │
Update Conversation History
      │
Manage Memory
      │
Generate Summary (if needed)
      │
Save Memory Files
```

---

## Technologies Used

- Python
- Groq API
- Llama 3.3 70B Versatile
- AsyncIO
- HTTPX
- JSON
- python-dotenv

---

## Installation

- Clone Repository
- Create Virtual Environment
- Install Dependencies
- Create `.env`
- Add Groq API Key
- Run the Application

---

## Usage

Run the application:

```bash
python agent.py
```

Special commands:

```
memory
```

Displays the current memory status, including:

- Conversation Summary
- Stored Entities
- Recent Conversation History

To exit the application:

```
exit
```

---

## Learning Outcomes

This project demonstrates practical implementation of:

- LLM Memory Systems
- Conversation Memory
- Summary Memory
- Entity Memory
- Context Window Management
- LLM-Based Summarization
- LLM-Based Entity Extraction
- Tool Calling
- Asynchronous Programming
- Persistent Storage using JSON

---

## Author

**Adina Rehman**

BS Artificial Intelligence  
Government Sadiq College Women University, Bahawalpur

AI/ML Intern — QM Logics