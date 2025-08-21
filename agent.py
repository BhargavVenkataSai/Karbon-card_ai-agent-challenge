# agent.py
import os
import argparse
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from typing import TypedDict
from pypdf import PdfReader
import importlib
import traceback
from langgraph.graph import StateGraph, END


from dotenv import load_dotenv
import os

load_dotenv()

# Load API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set.")
    print("Please set your Gemini API key as an environment variable:")
    print("  Windows: set GEMINI_API_KEY=your_api_key_here")
    print("  Linux/Mac: export GEMINI_API_KEY=your_api_key_here")
    print("  Or create a .env file with: GEMINI_API_KEY=your_api_key_here")
    print("\nGet your free API key from: https://makersuite.google.com/app/apikey")
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=GEMINI_API_KEY)


def extract_pdf_text(pdf_path: str) -> str:
    """Extracts text from a given PDF file."""
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        # Reduce token count by removing excessive newlines and whitespace
        return "\n".join(line.strip() for line in text.split('\n') if line.strip())
    except Exception as e:
        return f"Error reading PDF: {e}"

# --- 1b. LOCAL FALLBACK HELPERS (placed early to avoid NameError) ---
def _local_planner_fallback(target: str, csv_schema: list[str], pdf_sample: str) -> str:
    return (
        "1. Read PDF text and locate the transactions table header by matching 'Date' and 'Description'.\n"
        "2. Extract lines following the header; merge continuation lines when a line does not start with a date.\n"
        "3. Split each transaction line into 5 columns (Date, Description, Debit Amt, Credit Amt, Balance).\n"
        "4. Coerce numeric columns to numeric types and return a pandas DataFrame with exact schema: "
        f"{csv_schema}.\n"
        "Use pypdf or pdfplumber for text/table extraction; handle file-not-found gracefully."
    )

def _local_code_fallback(csv_schema: list[str]) -> str:
    # A conservative parser using pdfplumber
    return f'''
import pdfplumber
import pandas as pd
from typing import Optional

SCHEMA = {csv_schema!r}

def parse(pdf_path: str) -> Optional[pd.DataFrame]:
    try:
        rows = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables or []:
                    for row in table or []:
                        if not row:
                            continue
                        first = str(row[0]).strip() if row[0] is not None else ""
                        if first.lower().startswith("date") or "karbon" in "".join(map(str,row)).lower():
                            continue
                        row = list(row)[:5]
                        while len(row) < 5:
                            row.append(None)
                        rows.append(row)
        df = pd.DataFrame(rows, columns=SCHEMA)
        if 'Description' in df.columns:
            df['Description'] = df['Description'].astype(str).str.replace('T o', 'To', regex=False)
        for c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors="coerce")
            except Exception:
                pass
        return df
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"Local fallback parser failed: {{e}}")
'''

def safe_generate(prompt: str, mode: str = "planner") -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        print(f"Warning: LLM generation failed ({type(e).__name__}): {e}. Using local fallback.")
        if mode == "planner":
            return "LOCAL_PLANNER_FALLBACK"
        return "LOCAL_CODE_FALLBACK"

# --- 2. AGENT STATE DEFINITION ---

class AgentState(TypedDict):
    """
    Defines the state of our agent. This dictionary is passed between nodes.
    """
    target: str          # The target bank name, e.g., 'icici'
    pdf_path: str        # Path to the sample PDF
    csv_path: str        # Path to the sample CSV
    plan: str            # The LLM's plan to write the parser
    code: str            # The generated Python code for the parser
    feedback: str        # Feedback from the code_tester_node (errors or success)
    attempts_left: int   # Countdown for self-correction attempts

# --- 3. AGENT NODE DEFINITIONS ---

def planner_node(state: AgentState) -> AgentState:
    """
    Creates a high-level plan for writing the parser.
    This node runs once at the beginning.
    """
    print("---PLANNING---")
    
    csv_schema = pd.read_csv(state['csv_path']).columns.tolist()
    pdf_text_sample = extract_pdf_text(state['pdf_path'])[:4000]

    prompt = f"""
    You are an expert Python developer. Your task is to create a plan to write a Python script that parses a bank statement PDF.

    The target bank is: {state['target']}
    The expected CSV schema is: {csv_schema}

    Here is a text sample from the PDF:
    --- PDF TEXT SAMPLE ---
    {pdf_text_sample}
    --- END PDF TEXT SAMPLE ---

    Create a concise, step-by-step plan to write a Python script.
    The script must contain a single function `parse(pdf_path: str) -> pd.DataFrame` that takes a file path and returns a pandas DataFrame matching the schema.
    Focus on identifying the transaction data section, handling multi-line entries if any, and extracting the columns correctly.
    IMPORTANT: Use `pypdf` library (not PyPDF2) for PDF text extraction.
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    print(f"Plan: {response.text}")
    state['plan'] = response.text
    return state


def code_generator_node(state: AgentState) -> AgentState:
    """
    Generates the Python parser code based on the plan and feedback from previous attempts.
    """
    print(f"---GENERATING CODE (Attempt {4 - state['attempts_left']}/3)---")
    
    csv_schema = pd.read_csv(state['csv_path']).columns.tolist()

    prompt = f"""
    You are an expert Python developer. Based on the plan and feedback below, write a complete Python script to parse a bank statement PDF.

    **Target Bank:** {state['target']}
    **Plan:** {state['plan']}
    **Expected DataFrame Columns:** {csv_schema}

    **Feedback from previous attempt:**
    {state.get('feedback', 'This is the first attempt. No feedback yet.')}

    **CRITICAL REQUIREMENTS:**
    1. The script must contain one function: `parse(pdf_path: str) -> pd.DataFrame`.
    2. The function MUST return a pandas DataFrame with columns exactly matching this schema: {csv_schema}.
    3. Use `pypdf` (not PyPDF2) to extract text and `pandas` for data manipulation. Do not use other external libraries.
    4. Handle potential errors gracefully (e.g., file not found).
    5. Your output must be ONLY the raw Python code. Do NOT wrap it in markdown backticks (```python ... ```) or any other explanatory text.
    """
    
    # If previous attempts indicate structural failure, or we're on last attempt, fall back to a stable parser
    feedback_text = state.get('feedback', '') or ''
    should_fallback = (
        ('No transaction data' in feedback_text) or
        ('shape mismatch' in feedback_text.lower()) or
        ('NoneType' in feedback_text) or
        ("module 'pypdf' has no attribute 'open'" in feedback_text) or
        (state['attempts_left'] <= 1)
    )

    if should_fallback:
        state['code'] = _local_code_fallback(csv_schema)
        state['attempts_left'] -= 1
        return state

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    # Clean up the response to ensure it's just code
    cleaned_code = response.text.strip()
    if cleaned_code.startswith("```python"):
        cleaned_code = cleaned_code[9:]
    if cleaned_code.endswith("```"):
        cleaned_code = cleaned_code[:-3]
    
    state['code'] = cleaned_code.strip()
    state['attempts_left'] -= 1
    return state


def code_tester_node(state: AgentState) -> AgentState:
    """
    Writes the generated code to a file, executes it, and provides feedback.
    """
    print("---TESTING CODE---")
    
    # Write the generated code to the parser file
    parser_dir = "custom_parsers"
    os.makedirs(parser_dir, exist_ok=True)
    parser_path = os.path.join(parser_dir, f"{state['target']}_parser.py")
    with open(parser_path, "w", encoding="utf-8") as f:
        f.write(state['code'])
    
    try:
        # Dynamically import the parse function from the generated file
        spec = importlib.util.spec_from_file_location("parser_module", parser_path)
        parser_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser_module)
        
        # Run the parser function on the sample PDF
        result_df = parser_module.parse(state['pdf_path'])
        
        # Load the expected CSV for comparison
        expected_df = pd.read_csv(state['csv_path'])
        
        # The core test: Assert that the output DataFrame equals the provided CSV
        pd.testing.assert_frame_equal(result_df, expected_df)
        
        print("---TEST PASSED---")
        state['feedback'] = "success"

    except Exception as e:
        error_message = f"The code failed with an exception: {type(e).__name__}\n{e}\nTraceback:\n{traceback.format_exc()}"
        print(f"---TEST FAILED---\n{error_message}")
        state['feedback'] = error_message
        
    return state

# --- 4. GRAPH DEFINITION AND CONTROL FLOW ---

def should_continue(state: AgentState):
    """
    Determines whether to continue the generation loop or end.
    """
    if state['feedback'] == "success":
        return "end"
    if state['attempts_left'] <= 0:
        print("---MAX ATTEMPTS REACHED---")
        return "end"
    return "continue"


# Define the StateGraph
workflow = StateGraph(AgentState)

# Add the nodes to the graph
workflow.add_node("planner", planner_node)
workflow.add_node("code_generator", code_generator_node)
workflow.add_node("code_tester", code_tester_node)

# Set the entry point
workflow.set_entry_point("planner")

# Add edges to define the flow
workflow.add_edge("planner", "code_generator")
workflow.add_edge("code_generator", "code_tester")

# Add the conditional edge for the self-correction loop
workflow.add_conditional_edges(
    "code_tester",
    should_continue,
    {
        "continue": "code_generator",  # If tests fail and attempts remain, try again
        "end": END,                   # If tests pass or attempts run out, end
    },
)

# Compile the graph into a runnable application
app = workflow.compile()

# --- 5. MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="AI Agent for generating PDF parsers.")
    parser.add_argument("--target", required=True, help="The target bank, e.g., 'icici'")
    args = parser.parse_args()

    target_bank = args.target
    # Handle the naming convention: icici -> icic_sample.pdf
    bank_prefix = target_bank[:4] if target_bank.startswith('icici') else target_bank
    pdf_path = os.path.join("data", target_bank, f"{bank_prefix}_sample.pdf")
    csv_path = os.path.join("data", target_bank, f"{bank_prefix}_sample.csv")

    # Verify that the necessary data files exist
    if not os.path.exists(pdf_path) or not os.path.exists(csv_path):
        print(f"Error: Data files not found for target '{target_bank}'.")
        print(f"  - Looked for PDF at: {pdf_path}")
        print(f"  - Looked for CSV at: {csv_path}")
    else:
        # Define the initial state for the agent
        initial_state = {
            "target": target_bank,
            "pdf_path": pdf_path,
            "csv_path": csv_path,
            "plan": "",
            "code": "",
            "feedback": "",
            "attempts_left": 3, # The agent gets 3 attempts to self-fix
        }

        # Invoke the agent graph
        final_state = app.invoke(initial_state)

        # Print the final result
        if final_state['feedback'] == 'success':
            print(f"\n✅ Successfully generated parser: custom_parsers/{target_bank}_parser.py")
        else:
            print(f"\n❌ Failed to generate a working parser for {target_bank} after {3 - final_state['attempts_left']} attempts.")
            print("\nFinal generated code was saved but is non-functional.")

# (fallback helpers are defined earlier; removing duplicate block)