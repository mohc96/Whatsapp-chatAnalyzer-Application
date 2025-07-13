# backend/app/analyzer.py
import pandas as pd
from io import StringIO

def analyze_chat(raw_text: str) -> dict:
    # Temporary: just return message count
    messages = raw_text.strip().split('\n')
    return {
        "total_lines": len(messages),
        "sample": messages[:5]  # Show sample
    }
