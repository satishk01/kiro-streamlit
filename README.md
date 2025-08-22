# Kiro Streamlit Application

A web-based implementation of Kiro's specification workflow functionality using Streamlit and AWS Bedrock.

## Features

- **AI Model Selection**: Choose between Amazon Nova Pro and Anthropic Claude Sonnet 3.7
- **Three-Phase Workflow**: Requirements ? Design ? Tasks with user approval at each stage
- **AWS Bedrock Integration**: Role-based authentication for EC2 deployment
- **File Management**: Automatic saving to `.kiro/specs` directory structure
- **Session Management**: Persistent workflow state across interactions

## Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python run_app.py
   ```
   Or directly with Streamlit:
   ```bash
   streamlit run app.py
   ```

3. **Access the Application**
   - Open your browser to `http://localhost:8501`
   - Configure your working directory in the sidebar
   - Select an AI model (Note: AWS connection will fail locally without proper credentials)

### EC2 Deployment

1. **Launch EC2 Instance**
   - Use Amazon Linux 2 or Ubuntu
   - Attach IAM role with Bedrock permissions (see below)

2. **Install Dependencies**
   ```bash
   sudo yum update -y  # Amazon Linux
   sudo yum install -y python3 python3-pip git
   
   # Clone your application
   git clone <your-repo>
   cd kiro-streamlit-app
   
   # Install Python dependencies
   pip3 install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python3 run_app.py
   ```

## AWS Configuration

### Required IAM Role Permissions

Create an IAM role with the following policy and attach it to your EC2 instance:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

### Model Access

1. Go to AWS Bedrock Console
2. Navigate to "Model access" in the left sidebar
3. Request access to:
   - Amazon Nova Pro
   - Anthropic Claude 3.5 Sonnet

### Supported Regions

Bedrock is available in these regions:
- `us-east-1` (N. Virginia) - **Recommended**
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `eu-central-1` (Frankfurt)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)

## Usage

### Creating a New Specification

1. **Configure Settings**
   - Select AI model from sidebar
   - Set working directory path
   - Choose AWS region
   - Test AWS connection

2. **Start Workflow**
   - Enter feature name (use kebab-case: `my-feature`)
   - Describe your feature idea
   - Click "Start Specification Workflow"

3. **Follow Three-Phase Process**
   - **Requirements**: Review and approve generated requirements
   - **Design**: Review and approve technical design
   - **Tasks**: Review and approve implementation tasks

### Loading Existing Specifications

- Existing specs appear in the sidebar
- Click on any spec to load and continue working
- Status icons show completion: ?? (requirements), ??? (design), ? (tasks)

## File Structure

```
your-project/
+-- .kiro/
¦   +-- specs/
¦       +-- feature-name/
¦           +-- requirements.md
¦           +-- design.md
¦           +-- tasks.md
+-- ...
```

## Troubleshooting

### AWS Connection Issues

1. **"No AWS credentials found"**
   - Ensure EC2 instance has IAM role attached
   - For local development, configure AWS CLI or use environment variables

2. **"Access denied to Bedrock service"**
   - Check IAM role permissions
   - Ensure `bedrock:*` actions are allowed

3. **"Required models not available"**
   - Request model access in Bedrock console
   - Try a different AWS region

4. **"Cannot connect to Bedrock service"**
   - Verify Bedrock is available in your region
   - Check network connectivity

### Application Issues

1. **"Directory does not exist"**
   - Ensure the working directory path is correct and accessible
   - The application will create `.kiro/specs` automatically

2. **Workflow not progressing**
   - Ensure you approve each phase before proceeding
   - Check for error messages in the interface

## Development

### Project Structure

- `app.py` - Main Streamlit application
- `config.py` - Configuration management
- `ai_client.py` - AWS Bedrock integration
- `workflow.py` - Specification workflow engine
- `file_manager.py` - File operations
- `models.py` - Data models and state management
- `kiro_prompt.py` - Kiro system prompt

### Testing

Run the AWS connectivity test:
```bash
python test_aws.py
```

## License

This project implements Kiro's specification workflow methodology.