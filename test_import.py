#!/usr/bin/env python3
"""Test importing chat_interface to check for syntax errors."""

try:
    import chat_interface
    print("✅ Successfully imported chat_interface - no syntax errors!")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")
    print(f"   File: {e.filename}")
    print(f"   Line: {e.lineno}")
    print(f"   Text: {e.text}")
except ImportError as e:
    print(f"⚠️  Import Error (expected): {e}")
    print("This is normal if dependencies aren't installed")
except Exception as e:
    print(f"❌ Other Error: {e}")