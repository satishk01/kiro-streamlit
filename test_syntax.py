#!/usr/bin/env python3
"""Test script to validate Python syntax."""

def test_syntax():
    """Test if all Python files have valid syntax."""
    import ast
    import os
    
    python_files = [
        'app.py',
        'chat_interface.py',
        'ai_client.py',
        'config.py',
        'models.py',
        'workflow.py',
        'file_manager.py',
        'intent_classifier.py',
        'kiro_spec_workflow.py'
    ]
    
    errors = []
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
                print(f"✅ {file_path} - Syntax OK")
            except SyntaxError as e:
                error_msg = f"❌ {file_path} - Syntax Error: {e}"
                print(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"⚠️  {file_path} - Other Error: {e}"
                print(error_msg)
                errors.append(error_msg)
        else:
            print(f"⚠️  {file_path} - File not found")
    
    if errors:
        print(f"\n❌ Found {len(errors)} syntax errors:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print(f"\n✅ All Python files have valid syntax!")
        return True

if __name__ == "__main__":
    test_syntax()