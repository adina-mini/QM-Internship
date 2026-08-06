# Week 1 — Python CLI Agent

A command-line AI agent built with Groq API (LLaMA 3.3 70B), featuring retry logic, exponential backoff, and secure secret management.

## Features
- Groq LLaMA 3.3 70B model
- Exponential backoff retry (3 attempts)
- Rate limit handling (429)
- Secrets via .env — never hardcoded

## Usage
```bash
python agent.py "your question here"
```

## Stack
- Python 3.14
- Groq SDK
- python-dotenv
- argparse
