# Enhanced TheirStack Gmail MCP Server

A powerful Model Context Protocol (MCP) server that combines Gmail integration with TheirStack job search capabilities, written in Python. This server enables AI assistants like Claude to search for jobs and manage email communications for your job search through natural language interaction.

## 📚 Resources & Tutorials

**📖 [Read the Complete Tutorial](https://medium.com/@saidines12/automate-your-job-hunt-building-a-smart-mcp-server-with-theirstack-and-gmail-01078bffe2e4)** - Step-by-step guide on Medium

**🎥 [Watch the demo Video](https://www.youtube.com/watch?v=TiBvt1D4B7o&ab_channel=MachinePola)** - Demo video on YouTube

## 🌟 Key Features

### 💼 Job Search and Analysis
- Search for jobs across multiple platforms via TheirStack API
- Filter jobs by location, experience level, and skills
- Get detailed job descriptions and requirements
- Track application status and responses
- Receive automated daily job alerts
- Generate job search analytics and progress reports

### 📧 Smart Email Management for Job Search
- Send emails with customizable subject, content, and recipients
- Read and retrieve email content with full metadata
- Move emails to trash with confirmation
- Mark emails as read/unread
- Open emails directly in browser

### 📝 Draft Management
- Create draft emails for later review
- List all draft emails
- Edit existing drafts

### 🏷️ Advanced Label Management
- List all available labels
- Create custom labels
- Apply/remove labels from emails
- Rename existing labels
- Delete unused labels
- Search emails by label

### 📁 Folder Organization
- Create new folders (implemented as Gmail labels)
- Move emails between folders
- List all available folders

### 🔍 Powerful Search & Filtering
- Search emails using Gmail's advanced query syntax
- Create, manage, and delete email filters
- Filter by sender, recipient, subject, content, and more
- Customize search results with flexible parameters

### 🗄️ Archive Management
- Archive emails (remove from inbox without deleting)
- Batch archive multiple emails matching search criteria
- List all archived emails
- Restore archived emails to inbox

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Cloud project with Gmail API enabled
- OAuth 2.0 credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/saidineshpola/job-search-gmail-mcp.git
cd job-search-gmail-mcp

# Set up a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install -e .
```

> 💡 **Need help with setup?** Check out our [detailed tutorial](https://medium.com/@saidines12/automate-your-job-hunt-building-a-smart-mcp-server-with-theirstack-and-gmail-01078bffe2e4) or [video walkthrough](https://www.youtube.com/watch?v=TiBvt1D4B7o&ab_channel=MachinePola) for step-by-step instructions.

### Their Stack Setup
1. Get the API credentials from [theirstack](https://app.theirstack.com/settings/api-key) and save it inside `theirstack_api.json`:

```json
{
    "api_key": "your_theirstack_api_key_here",
}
```

### Google Cloud Setup

1. Create a [new Google Cloud project](https://console.cloud.google.com/projectcreate)
2. [Enable the Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
3. Configure the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent):
   - Select "External" user type
   - Add your email as a test user
   - Add the scope: `https://www.googleapis.com/auth/gmail/modify`
4. Create [OAuth 2.0 credentials](https://console.cloud.google.com/apis/credentials):
   - Choose "Desktop app" as the application type
   - Download the JSON credentials file

### Configuration

1. **Store OAuth Credentials**
   ```bash
   # Create directory for credentials
   mkdir -p ~/.gmail-mcp
   
   # Move downloaded credentials file to secure location
   mv ~/Downloads/client_secret_*.json ~/.gmail-mcp/credentials.json
   ```

2. **Configure User Profile**
   Update the default user profile in `src/theirstack/server.py` with your details so that you don't have to give it everytime in the prompt:
   ```python
   COMPACT_USER_PROFILE = UserProfile(
       name="AI/ML Engineer",              # Your job title
       skills=[                            # List your technical skills
           "AI/ML", "NLP", "LLM", "RAG",
           "LangChain", "PyTorch", 
           "Python", "FastAPI"
       ],
       preferred_locations=["India", "Remote"],  # Your preferred work locations
       years_of_experience=1,                    # Your years of experience
       experience="Update with your professional experience summary"
   )
   ```

   This profile will be used to:
   - Filter and prioritize job matches
   - Customize job search queries
   - Generate personalized application materials
 
 3. **Update default mail id** 
 Update the default MAil in src/gmail/server.py to your mail id for the backup if LLM doesn't know your mail id.

## 🔧 Usage

### Running with Claude Desktop

Add the following to your Claude Desktop configuration file (typically at `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\user\\Desktop\\projects\\gmail-mcp",
        "run",
        "gmail",
        "--creds-file-path",
        "C:\\Users\\user\\Desktop\\projects\\gmail-mcp\\client_secret_.apps.googleusercontent.com.json",
        "--token-path",
        "C:\\Users\\user\\Desktop\\projects\\gmail-mcp\\tokens.json"
      ]
    },
    "jobstack": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\user\\Desktop\\projects\\gmail-mcp",
        "run",
        "jobstack",
        "--api-config",
        "C:\\Users\\user\\Desktop\\projects\\gmail-mcp\\theirstack_api.json"
      ]
    }
  }
}
```

### Testing with MCP Inspector

For testing and debugging, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run /path/to/gmail-mcp/src/gmail/server.py --creds-file-path /path/to/credentials.json --token-path /path/to/tokens.json
```

## 🔐 Security Considerations

- **Never commit credentials or token files to version control**
- Store credentials in a secure location with appropriate permissions
- The server will request user confirmation before performing sensitive actions
- Review Google Cloud Console regularly for unusual activity
- Consider using environment variables for sensitive paths

## 🛠️ Architecture

This implementation features a comprehensive single-file architecture that handles all Gmail operations through the Google API client libraries. Key components include:

- OAuth2 authentication with automatic token refresh
- Comprehensive error handling and logging
- Structured tool definitions with clear input schemas
- Efficient email parsing and formatting

## 📚 Example Prompts

Try these job search-specific prompts with Claude:

- "Find ML engineering jobs posted in the last 2 days and send me the mail about it."
- "Send me a daily digest of new AI jobs in Bangalore"
- "Draft an application email for the Senior ML Scientist position at Wayfair"
- "Track my application status for recent jobs"
- "Create a follow-up email template for applications with no response"
- "Generate a weekly report of my job search progress"

## 🔄 Daily Job Search Workflow

1. The server automatically fetches new job postings every 24 hours
2. Matches are filtered based on your preferences in `theirstack_api.json`
3. A formatted email digest is sent to your specified email address
4. You can respond with actions like "apply", "save for later", or "ignore"
5. The server helps manage applications and follow-ups automatically

## 📊 Job Search Analytics

- Track your application success rates
- Monitor response times from employers
- View job market trends in your field
- Generate detailed progress reports
- Set and track application goals

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📖 Learn More

- **📝 [Complete Tutorial](https://medium.com/@saidines12/automate-your-job-hunt-building-a-smart-mcp-server-with-theirstack-and-gmail-01078bffe2e4)** - In-depth article explaining the architecture and implementation
- **🎥 [Video demo](https://www.youtube.com/watch?v=TiBvt1D4B7o&ab_channel=MachinePola)** - Visual walkthrough of mcp server
- **🔗 [Model Context Protocol](https://modelcontextprotocol.io/)** - Learn more about the MCP framework

## 📄 License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by various MCP server implementations in the community
- Thanks to [@theposch](https://github.com/theposch/gmail-mcp) for the gmail mcp server.
- Built with the [Model Context Protocol](https://modelcontextprotocol.io/) framework
- Uses Google's official API client libraries
