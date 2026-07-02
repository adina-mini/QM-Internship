# Groq Tool Calling Agent

A simple AI assistant built using the **Groq API** that demonstrates **native LLM tool calling** without relying on frameworks such as LangChain or LangGraph.

The agent intelligently decides when to use external tools instead of answering directly. It currently supports weather lookup, mathematical calculations, and currency conversion.

---

## Features

* Native Groq tool calling
* Weather lookup
* Calculator
* Currency conversion
* Automatic tool selection by the LLM
* Asynchronous tool execution
* Retry logic with exponential backoff
* Rate limit handling
* Environment variable configuration

---

## Technologies Used

* Python 3.10+
* Groq API
* httpx
* asyncio
* python-dotenv

---

## Project Structure

```text
.
├── main.py
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## How It Works

The application follows the native tool-calling workflow provided by the Groq API.

1. The user enters a prompt.
2. The prompt and available tool definitions are sent to the LLM.
3. The LLM analyzes the request and decides whether a tool is needed.
4. If required, the LLM returns the tool name and arguments.
5. Python executes the selected tool.
6. The tool result is sent back to the LLM.
7. The LLM generates a natural-language response for the user.

### Example Flow

**User**

```text
Convert 100 USD to PKR
```

↓

**LLM selects**

```text
convert_currency
```

↓

**Python executes the tool**

↓

**Tool returns the conversion**

↓

**LLM generates the final response**

---

## Available Tools

### Weather

Returns the current weather for a specified city.

Example:

```bash
python main.py "What's the weather in Lahore?"
```

---

### Calculator

Evaluates mathematical expressions.

> **Note:** For this educational project, mathematical expressions are evaluated using Python's `eval()` with restricted built-ins and input validation. In production, a dedicated safe expression parser should be used instead.

Example:

```bash
python main.py "Calculate (25 + 5) * 3"
```

---

### Currency Converter

Converts one currency to another using live exchange rates.

Example:

```bash
python main.py "Convert 100 USD to PKR"
```

---

## Getting Started

1. Clone the repository
2. Create a virtual environment (Recommended)
3. Install dependencies
4. Configure the `.env` file
5. Run the project

---

## Error Handling

The project includes:

* API key validation
* Retry logic with exponential backoff
* Rate limit handling
* HTTP request timeouts
* Exception handling for external API calls
* Input validation for calculator expressions

---

## Learning Outcomes

This project helped me understand:

* Native LLM tool calling
* Function schema design
* JSON argument parsing
* Asynchronous programming with Python
* API integration
* Retry strategies
* How an LLM decides when to call a tool
* The request/response loop used in tool-calling agents

---

## License

This project was developed for educational purposes as part of an AI/ML internship roadmap.
