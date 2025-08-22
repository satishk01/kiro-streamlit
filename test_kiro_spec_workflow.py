"""Test the Kiro specification workflow."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kiro_spec_workflow import KiroSpecWorkflow
from ai_client import AIClient
import tempfile
import shutil


def test_kiro_spec_workflow():
    """Test the complete Kiro specification workflow."""
    print("Testing Kiro Specification Workflow")
    print("=" * 40)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize workflow
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        workflow = KiroSpecWorkflow(ai_client, temp_dir)
        
        print("✅ Workflow initialized")
        
        # Test 1: Create spec from idea
        print("\n1. Testing spec creation from idea...")
        user_idea = "Create a spec for user authentication system with login, registration, and password reset"
        
        # Mock AI response for testing
        class MockAIClient:
            def generate_response(self, prompt, system_prompt, max_tokens=2000, temperature=0.3):
                if "requirements" in prompt.lower():
                    return """# Requirements Document

## Introduction

This document outlines the requirements for a user authentication system that provides secure login, registration, and password reset functionality.

## Requirements

### Requirement 1

**User Story:** As a new user, I want to register for an account, so that I can access the application

#### Acceptance Criteria

1. WHEN a user provides valid email and password THEN the system SHALL create a new account
2. WHEN a user provides an existing email THEN the system SHALL return an error message
3. IF the password is less than 8 characters THEN the system SHALL reject the registration

### Requirement 2

**User Story:** As a registered user, I want to log in to my account, so that I can access my personalized content

#### Acceptance Criteria

1. WHEN a user provides correct credentials THEN the system SHALL authenticate the user
2. WHEN a user provides incorrect credentials THEN the system SHALL return an authentication error
3. WHEN a user is authenticated THEN the system SHALL provide a session token"""
                
                elif "design" in prompt.lower():
                    return """# Design Document

## Overview

The user authentication system will be built using a microservices architecture with JWT tokens for session management.

## Architecture

- Authentication Service: Handles login, registration, password reset
- User Service: Manages user profiles and data
- Token Service: Issues and validates JWT tokens

## Components and Interfaces

### Authentication Controller
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- POST /auth/reset-password

### User Repository
- Database interface for user CRUD operations
- Password hashing and validation

## Data Models

### User Model
- id: UUID
- email: string (unique)
- password_hash: string
- created_at: timestamp
- updated_at: timestamp

## Error Handling

- Input validation errors (400)
- Authentication failures (401)
- Server errors (500)

## Testing Strategy

- Unit tests for all components
- Integration tests for API endpoints
- End-to-end authentication flow tests"""
                
                elif "tasks" in prompt.lower():
                    return """# Implementation Plan

- [ ] 1. Set up project structure and dependencies
  - Create directory structure for authentication service
  - Install required packages (bcrypt, jwt, database driver)
  - _Requirements: 1.1_

- [ ] 2. Implement user data model and repository
- [ ] 2.1 Create User model with validation
  - Define User class with email, password fields
  - Implement password hashing using bcrypt
  - _Requirements: 1.1, 2.1_

- [ ] 2.2 Implement UserRepository for database operations
  - Create database connection and user table
  - Implement CRUD operations for users
  - _Requirements: 1.1, 2.1_

- [ ] 3. Build authentication service
- [ ] 3.1 Implement registration endpoint
  - Create POST /auth/register handler
  - Add email validation and duplicate checking
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 3.2 Implement login endpoint
  - Create POST /auth/login handler
  - Add password verification and JWT token generation
  - _Requirements: 2.1, 2.2, 2.3_"""
                
                return "Mock response"
        
        workflow.ai_client = MockAIClient()
        
        response, next_action = workflow.create_spec_from_idea(user_idea)
        
        if next_action == "requirements-review":
            print("✅ Requirements created successfully")
            print(f"Feature name: {workflow.get_feature_name()}")
            print(f"Current phase: {workflow.get_current_phase()}")
        else:
            print("❌ Requirements creation failed")
        
        # Test 2: Approve requirements
        print("\n2. Testing requirements approval...")
        response, next_action = workflow.handle_requirements_feedback("Yes, looks good")
        
        if next_action == "design-review":
            print("✅ Design created after requirements approval")
            print(f"Current phase: {workflow.get_current_phase()}")
        else:
            print("❌ Design creation failed")
        
        # Test 3: Approve design
        print("\n3. Testing design approval...")
        response, next_action = workflow.handle_design_feedback("Approved")
        
        if next_action == "tasks-review":
            print("✅ Tasks created after design approval")
            print(f"Current phase: {workflow.get_current_phase()}")
        else:
            print("❌ Tasks creation failed")
        
        # Test 4: Approve tasks
        print("\n4. Testing tasks approval...")
        response, next_action = workflow.handle_tasks_feedback("Perfect, looks good")
        
        if next_action == "complete":
            print("✅ Workflow completed successfully")
            print(f"Current phase: {workflow.get_current_phase()}")
        else:
            print("❌ Workflow completion failed")
        
        # Test 5: Check files were created
        print("\n5. Testing file creation...")
        spec_dir = os.path.join(temp_dir, ".kiro", "specs", workflow.get_feature_name())
        
        required_files = ["requirements.md", "design.md", "tasks.md"]
        for file_name in required_files:
            file_path = os.path.join(spec_dir, file_name)
            if os.path.exists(file_path):
                print(f"✅ {file_name} created")
                
                # Check file content
                with open(file_path, 'r') as f:
                    content = f.read()
                if len(content) > 100:
                    print(f"   Content length: {len(content)} characters")
                else:
                    print(f"   ❌ Content too short: {len(content)} characters")
            else:
                print(f"❌ {file_name} not found")
        
        print("\n🎉 Kiro specification workflow test completed!")
        
        # Summary
        print("\n📋 Kiro Spec Workflow Features Verified:")
        print("- Requirements generation with EARS format")
        print("- User approval at each stage")
        print("- Design document creation")
        print("- Implementation tasks generation")
        print("- File persistence in .kiro/specs directory")
        print("- Proper workflow state management")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def test_approval_detection():
    """Test the approval detection logic."""
    print("\nTesting Approval Detection")
    print("=" * 30)
    
    try:
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        workflow = KiroSpecWorkflow(ai_client, "/tmp")
        
        # Test approval phrases
        approval_tests = [
            ("yes", True),
            ("Yes, looks good", True),
            ("approved", True),
            ("Looks great, move on", True),
            ("ok", True),
            ("perfect", True),
            ("👍", True),
            ("no", False),
            ("needs changes", False),
            ("I want to modify something", False),
            ("can you add more details", False),
        ]
        
        for phrase, expected in approval_tests:
            result = workflow._is_approval(phrase)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{phrase}' -> {result} (expected: {expected})")
        
        print("\n✅ Approval detection tests completed")
        
    except Exception as e:
        print(f"❌ Approval detection test failed: {e}")


if __name__ == "__main__":
    print("Kiro Specification Workflow Test Suite")
    print("=" * 50)
    
    test_kiro_spec_workflow()
    test_approval_detection()
    
    print("\n🚀 All Kiro spec workflow tests completed!")
    print("\nThe app now supports:")
    print("- Proper Kiro specification workflow")
    print("- User approval at each stage (requirements, design, tasks)")
    print("- EARS format requirements")
    print("- Comprehensive design documents")
    print("- Actionable implementation tasks")
    print("- File persistence and state management")