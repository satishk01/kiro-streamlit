#!/usr/bin/env python3
"""Startup script for Kiro Streamlit application."""
import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import boto3
        print("✅ Dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_aws_config():
    """Check basic AWS configuration."""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS configured - Identity: {identity.get('Arn', 'Unknown')}")
        return True
    except Exception as e:
        print(f"⚠️  AWS not configured: {e}")
        print("This is expected if running locally. Ensure proper IAM role when deploying to EC2.")
        return False

def main():
    """Main startup function."""
    print("🤖 Starting Kiro Streamlit Application...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check AWS (optional for local development)
    check_aws_config()
    
    # Start Streamlit app
    print("\n🚀 Starting Streamlit server...")
    print("📱 The app will open in your browser at http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down Kiro application...")

if __name__ == "__main__":
    main()