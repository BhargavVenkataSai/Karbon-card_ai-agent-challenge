#!/usr/bin/env python3
"""
Demo script for the AI Agent Bank Statement Parser
This script demonstrates the agent's capabilities without requiring API keys.
"""

import os
import sys
import pandas as pd
from pathlib import Path

def demo_agent_architecture():
    """Demonstrate the agent's architecture and workflow."""
    print("🤖 AI Agent for Bank Statement PDF Parsing")
    print("=" * 50)
    
    print("\n🏗️  Agent Architecture:")
    print("┌─────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐")
    print("│ Planner │───▶│ Code Gen    │───▶│ Code Test  │───▶│ Success?   │")
    print("│         │    │             │    │             │    │             │")
    print("└─────────┘    └──────────────┘    └─────────────┘    └─────────────┘")
    print("                                                           │")
    print("                                                           ▼")
    print("                                                ┌─────────────────┐")
    print("                                                │ Self-Correct    │")
    print("                                                │ (≤3 attempts)   │")
    print("                                                └─────────────────┘")
    
    print("\n🔄 Self-Correction Loop:")
    print("   • Agent gets up to 3 attempts to fix code issues")
    print("   • Automatically analyzes test failures")
    print("   • Regenerates code with improved prompts")
    print("   • Continues until success or max attempts reached")

def demo_data_structure():
    """Show the project's data structure."""
    print("\n📁 Project Structure:")
    print("Karbon-AI-agent/")
    print("├── agent.py                 # Main AI agent implementation")
    print("├── custom_parsers/          # Generated parser modules")
    print("│   ├── __init__.py")
    print("│   └── icici_parser.py     # Example parser for ICICI bank")
    print("├── data/                    # Sample data for different banks")
    print("│   └── icici/")
    print("│       ├── icic_sample.pdf # Sample PDF statement")
    print("│       └── icic_sample.csv # Expected CSV output")
    print("├── tests/                   # Test files")
    print("│   └── test_icici_parser.py")
    print("├── requirements.txt         # Python dependencies")
    print("└── README.md               # Documentation")

def demo_existing_parser():
    """Demonstrate the existing ICICI parser."""
    print("\n🔍 Existing Parser Demo:")
    
    try:
        from custom_parsers.icici_parser import parse
        
        # Check if sample data exists
        pdf_path = "data/icici/icic_sample.pdf"
        csv_path = "data/icici/icic_sample.csv"
        
        if os.path.exists(pdf_path) and os.path.exists(csv_path):
            print(f"✅ Found sample data:")
            print(f"   PDF: {pdf_path}")
            print(f"   CSV: {csv_path}")
            
            # Load expected CSV
            expected_df = pd.read_csv(csv_path)
            print(f"📊 Expected CSV schema: {list(expected_df.columns)}")
            print(f"📈 Expected rows: {len(expected_df)}")
            
            # Show first few rows
            print("\n📋 Sample data (first 3 rows):")
            print(expected_df.head(3).to_string(index=False))
            
            # Test the parser
            print(f"\n🧪 Testing existing parser...")
            result_df = parse(pdf_path)
            print(f"✅ Parser executed successfully!")
            print(f"📊 Generated DataFrame shape: {result_df.shape}")
            print(f"📋 Generated data (first 3 rows):")
            print(result_df.head(3).to_string(index=False))
            
            # Verify they match
            if result_df.equals(expected_df):
                print("🎉 SUCCESS: Generated DataFrame exactly matches expected CSV!")
            else:
                print("⚠️  WARNING: Generated DataFrame doesn't match expected CSV")
                
        else:
            print("❌ Sample data not found. Please ensure data files exist.")
            
    except ImportError as e:
        print(f"❌ Could not import parser: {e}")
    except Exception as e:
        print(f"❌ Error testing parser: {e}")

def demo_agent_usage():
    """Show how to use the agent."""
    print("\n🚀 How to Use the Agent:")
    print("\n1. Setup Environment:")
    print("   pip install -r requirements.txt")
    print("   set GEMINI_API_KEY=your_api_key_here  # Windows")
    print("   export GEMINI_API_KEY=your_api_key_here  # Linux/Mac")
    
    print("\n2. Run the Agent:")
    print("   python agent.py --target icici")
    
    print("\n3. What Happens:")
    print("   • Agent reads data/icici/icic_sample.pdf & icic_sample.csv")
    print("   • Generates custom_parsers/icici_parser.py")
    print("   • Tests parser against sample data")
    print("   • Self-corrects if needed (≤3 attempts)")
    
    print("\n4. Test Results:")
    print("   • Success: ✅ Parser generated and working")
    print("   • Failure: ❌ Parser saved but non-functional")

def demo_extending():
    """Show how to extend for new banks."""
    print("\n📈 Extending for New Banks:")
    print("\n1. Add Sample Data:")
    print("   mkdir data/sbi")
    print("   cp your_sbi_statement.pdf data/sbi/sbi_sample.pdf")
    print("   cp your_sbi_expected.csv data/sbi/sbi_sample.csv")
    
    print("\n2. Generate Parser:")
    print("   python agent.py --target sbi")
    
    print("\n3. Test Generated Parser:")
    print("   python -m pytest tests/test_sbi_parser.py -v")

def main():
    """Run the complete demo."""
    demo_agent_architecture()
    demo_data_structure()
    demo_existing_parser()
    demo_agent_usage()
    demo_extending()
    
    print("\n" + "=" * 50)
    print("🎯 Ready to build your own AI agent!")
    print("📚 See README.md for detailed instructions")
    print("🔑 Get free Gemini API credits: https://makersuite.google.com/app/apikey")

if __name__ == "__main__":
    main()
