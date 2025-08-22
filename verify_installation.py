"""Verification script to check if the Kiro clone installation is working correctly."""
import sys
import os
from pathlib import Path


def check_file_exists(file_path: str) -> bool:
    """Check if a required file exists."""
    return Path(file_path).exists()


def check_python_imports():
    """Check if all required Python modules can be imported."""
    print("Checking Python imports...")
    
    required_modules = [
        'streamlit',
        'boto3',
        'botocore',
        'pathlib',
        'json',
        'typing',
        'dataclasses',
        'datetime'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} - MISSING")
            missing_modules.append(module)
    
    return missing_modules


def check_required_files():
    """Check if all required application files exist."""
    print("\nChecking required files...")
    
    required_files = [
        'app.py',
        'ai_client.py',
        'chat_interface.py',
        'intent_classifier.py',
        'vibe_coding.py',
        'file_browser.py',
        'workflow.py',
        'config.py',
        'models.py',
        'file_manager.py',
        'kiro_system_prompt.py',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if check_file_exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return missing_files


def check_ai_client_methods():
    """Check if AIClient has the required methods."""
    print("\nChecking AIClient methods...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        from ai_client import AIClient
        
        # Create a test instance
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        
        # Check required methods
        required_methods = ['generate_content', 'generate_response', 'test_connection']
        missing_methods = []
        
        for method in required_methods:
            if hasattr(ai_client, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - MISSING")
                missing_methods.append(method)
        
        return missing_methods
        
    except Exception as e:
        print(f"  ❌ Error checking AIClient: {e}")
        return ['AIClient_error']


def check_streamlit_installation():
    """Check if Streamlit is properly installed and can run."""
    print("\nChecking Streamlit installation...")
    
    try:
        import streamlit as st
        print(f"  ✅ Streamlit version: {st.__version__}")
        return True
    except ImportError:
        print("  ❌ Streamlit not installed")
        return False


def main():
    """Run all verification checks."""
    print("🔍 Kiro Clone Installation Verification")
    print("=" * 50)
    
    # Check Python imports
    missing_modules = check_python_imports()
    
    # Check required files
    missing_files = check_required_files()
    
    # Check AIClient methods
    missing_methods = check_ai_client_methods()
    
    # Check Streamlit
    streamlit_ok = check_streamlit_installation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_good = True
    
    if missing_modules:
        print(f"❌ Missing Python modules: {', '.join(missing_modules)}")
        print("   Fix: pip install -r requirements.txt")
        all_good = False
    else:
        print("✅ All Python modules available")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        print("   Fix: Ensure all project files are downloaded")
        all_good = False
    else:
        print("✅ All required files present")
    
    if missing_methods:
        print(f"❌ Missing AIClient methods: {', '.join(missing_methods)}")
        print("   Fix: Update ai_client.py to latest version")
        all_good = False
    else:
        print("✅ AIClient methods available")
    
    if not streamlit_ok:
        print("❌ Streamlit installation issue")
        print("   Fix: pip install streamlit")
        all_good = False
    else:
        print("✅ Streamlit ready")
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 INSTALLATION VERIFIED - Ready to run!")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Configure AWS settings in the sidebar")
        print("3. Test connection to AWS Bedrock")
        print("4. Start using the Kiro clone!")
    else:
        print("⚠️  ISSUES FOUND - Please fix the above problems")
        print("\nCommon fixes:")
        print("- pip install -r requirements.txt")
        print("- Ensure all project files are present")
        print("- Update to latest version of all files")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()