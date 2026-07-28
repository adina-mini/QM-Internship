# LangGraph Tool-Calling AI Agent

A simple AI agent built with **LangGraph**, **LangChain**, and **Groq** that demonstrates graph-based agent orchestration with tool calling. The agent can have normal conversations and use external tools for weather lookup, mathematical calculations, and currency conversion when required.

## Features

- Conversational AI using Groq's Llama 3.3 70B model
- Graph-based workflow using LangGraph
- Tool calling through LangChain
- Weather information retrieval
- Mathematical expression evaluation
- Currency conversion
- Conditional routing between chatbot and tools
- Command-line interface (CLI)

---

## Project Structure

```
Week5_LangGraph/
│
├── main.py          
├── graph.py        
├── nodes.py         #graph nodes
├── tools.py         # Tool implementations
├── state.py         # Agent state definition
├── utils.py         # LLM initialization
├── .env             # Environment variables
├── requirements.txt
└── README.md
```

---

## Technologies Used

- Python
- LangGraph
- LangChain
- LangChain-Groq
- Groq API
- HTTPX
- python-dotenv

---

## Agent Workflow

```
User
   │
   ▼
main.py
   │
   ▼
AgentState
   │
   ▼
Chatbot Node
   │
   ├─────────────── No Tool Required ───────────────► Final Response
   │
   ▼
Tool Required
   │
   ▼
Tool Node
   │
   ▼
Execute Tool
   │
   ▼
Chatbot Node
   │
   ▼
Final Response
```

---

## Tools

### Weather Tool
Retrieves the current weather for a specified city.

Example:

```
Weather in Lahore
```

---

### Calculator Tool

Evaluates mathematical expressions.

Example:

```
25 * (4 + 6)
```

---

### Currency Converter

Converts an amount from one currency to another using live exchange rates.

Example:

```
Convert 100 USD to PKR
```

---

## State Management

The agent maintains conversation history using a custom `AgentState`.

```python
AgentState
└── messages
```

The state is passed between graph nodes, allowing the conversation context to persist throughout a single interaction.

---

## Graph Components

### Chatbot Node

- Receives conversation history
- Sends messages to the LLM
- Determines whether a tool is required

### Tool Node

- Executes requested tools
- Returns tool outputs to the chatbot

### Conditional Edge

Routes execution based on whether the latest AI message contains tool calls.

---

## Installation

Clone the repository

```bash
git clone <repository-url>
cd Week5_LangGraph
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GROQ_API_KEY=your_api_key_here
```

---

## Running the Project

```bash
python main.py
```

---

## Example Interaction

```
Ask: Hello

Hello! How can I assist you today?

Ask: Weather in Karachi

Current weather in Karachi...

Ask: Calculate 56 * 18

1008

Ask: Convert 100 USD to PKR

100 USD = ...
```

---

## Learning Objectives

This project demonstrates:

- Building graph-based AI agents
- Managing conversational state
- Integrating external tools with an LLM
- Conditional routing in LangGraph
- Basic agent orchestration using LangChain and Groq

---

## Future Improvements

- Persistent conversation memory
- Additional tools
- Better error handling
- Streaming responses
- Multi-step reasoning
- Web interface
- Conversation history storage

---

## Author

**Adina Rehman**

BS Artificial Intelligence  
Government Sadiq College Women University, Bahawalpur
