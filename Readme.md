# AI Agent for Bank Statement PDF Parsing

This project implements an autonomous AI agent that can generate custom parsers for bank statement PDFs. The agent uses Google's Gemini AI to analyze PDF samples and generate Python code that can parse similar statements.

## 🎯 Project Goal

Develop a coding agent that writes custom parsers for bank statement PDFs. When run via CLI, it writes a new parser in `custom_parsers/` and lets evaluators run it on their own statement files for new banks without manual tweaks.

## 🏗️ Architecture

The agent follows a **plan → generate → test → refine** loop using LangGraph:

```
┌─────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│ Planner │───▶│ Code Gen    │───▶│ Code Test  │───▶│ Success?   │
│         │    │             │    │             │    │             │
└─────────┘    └──────────────┘    └─────────────┘    └─────────────┘
                                                           │
                                                           ▼
                                                ┌─────────────────┐
                                                │ Self-Correct    │
                                                │ (≤3 attempts)   │
                                                └─────────────────┘
```

**Key Components:**

- **Planner Node**: Analyzes PDF sample and CSV schema to create parsing strategy
- **Code Generator Node**: Generates Python parser code using Gemini AI
- **Code Tester Node**: Tests generated code against sample data
- **Self-Correction Loop**: Automatically refines code up to 3 times on failures

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd Karbon-AI-agent

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key (get free credits from https://makersuite.google.com/app/apikey)
# Windows:
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac:
export GEMINI_API_KEY=your_api_key_here
```

**Note**: The system now uses LangGraph 0.6.6+ which provides better stability and performance.

### 2. Run the Agent

```bash
# Generate parser for ICICI bank
python agent.py --target icici

# The agent will:
# 1. Read data/icici/icic_sample.pdf & icic_sample.csv
# 2. Generate custom_parsers/icici_parser.py
# 3. Test the parser against the sample data
# 4. Self-correct if needed (up to 3 attempts)
```

### 3. Test the Generated Parser

```bash
# Run tests to verify parser works
python -m pytest tests/test_icici_parser.py -v
```

## 📁 Project Structure

```
Karbon-AI-agent/
├── agent.py                 # Main AI agent implementation
├── custom_parsers/          # Generated parser modules
│   ├── __init__.py
│   └── icici_parser.py     # Example parser for ICICI bank
├── data/                    # Sample data for different banks
│   └── icici/
│       ├── icic_sample.pdf # Sample PDF statement
│       └── icic_sample.csv # Expected CSV output
├── tests/                   # Test files
│   └── test_icici_parser.py
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 How It Works

### Agent Workflow

1. **Planning Phase**: Agent analyzes the PDF sample and CSV schema to understand the data structure
2. **Code Generation**: Uses Gemini AI to generate Python parser code
3. **Testing**: Runs the generated parser against sample data
4. **Self-Correction**: If tests fail, analyzes errors and regenerates code (up to 3 attempts)
5. **Success**: Outputs working parser that matches the expected CSV schema

### Parser Contract

All generated parsers must implement:

```python
def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parse a bank statement PDF and return a pandas DataFrame.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        DataFrame with columns matching the expected CSV schema
    """
```

## 🧪 Testing

The agent automatically tests generated parsers using:

- **Input**: Sample PDF statement
- **Expected**: Sample CSV with known schema
- **Assertion**: `pd.testing.assert_frame_equal()` to ensure exact match

## 🎨 Features

- **Autonomous**: No manual intervention needed after setup
- **Self-Correcting**: Automatically fixes code issues up to 3 times
- **Bank-Agnostic**: Works with any bank's statement format
- **Type-Safe**: Uses proper Python typing and error handling
- **Test-Driven**: Ensures generated parsers work correctly

## 🔑 API Requirements

- **Google Gemini API**: Free tier available at [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Alternative**: Can be easily modified to use other LLM providers

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Set**

   ```
   Error: GEMINI_API_KEY environment variable not set
   ```

   **Solution**: Set your Gemini API key as an environment variable

2. **PDF Parsing Errors**

   ```
   Error: PDF file not found
   ```

   **Solution**: Ensure sample PDF exists in `data/{bank}/` directory

3. **Test Failures**
   ```
   AssertionError: DataFrame not equal
   ```
   **Solution**: Agent will automatically retry up to 3 times

### Debug Mode

To see detailed agent output, run with verbose logging:

```bash
python -u agent.py --target icici
```

## 📈 Extending the Agent

### Adding New Banks

1. Create `data/{bank_name}/` directory
2. Add `{bank_name}_sample.pdf` and `{bank_name}_sample.csv`
3. Run: `python agent.py --target {bank_name}`

### Customizing Prompts

Modify the prompt templates in `planner_node()` and `code_generator_node()` functions to:

- Add specific parsing instructions
- Include bank-specific formatting rules
- Customize error handling requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the Karbon AI Challenge. See the challenge document for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Powered by [Google Gemini](https://ai.google.dev/) for code generation
- Inspired by [mini-swe-agent](https://github.com/princeton-nlp/mini-swe-agent) architecture
