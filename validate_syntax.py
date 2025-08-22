#!/usr/bin/env python3
"""Simple syntax validation script."""

try:
    with open('chat_interface.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to compile the code
    compile(content, 'chat_interface.py', 'exec')
    print("✅ chat_interface.py syntax is valid!")
    
except SyntaxError as e:
    print(f"❌ Syntax Error in chat_interface.py:")
    print(f"   Line {e.lineno}: {e.text.strip() if e.text else 'N/A'}")
    print(f"   Error: {e.msg}")
    print(f"   Position: {' ' * (e.offset - 1) if e.offset else ''}^")
    
except Exception as e:
    print(f"❌ Other error: {e}")