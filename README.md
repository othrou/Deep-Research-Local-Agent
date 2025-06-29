# 🔍 AI Domain Deep Research Agent

An advanced AI research agent built using the Agno Agent framework, Ollama local models, and custom search tools. This agent helps users conduct comprehensive research on any topic by generating research questions, finding answers through multiple search engines, and compiling professional reports with local file saving.

## Features

- 🧠 **Intelligent Question Generation**:
  - Automatically generates 5 specific research questions about your topic
  - Tailors questions to your specified domain
  - Focuses on creating yes/no questions for clear research outcomes

- 🔎 **Multi-Source Research**:
  - Uses DuckDuckGo Search for comprehensive web results
  - Leverages SearXNG for enhanced search capabilities
  - Combines multiple sources for thorough research
  - Fetches full page content when needed

- 📊 **Professional Report Generation**:
  - Compiles research findings into a McKinsey-style report
  - Structures content with executive summary, analysis, and conclusion
  - Saves reports locally as HTML files for easy access

- 🖥️ **User-Friendly Interface**:
  - Clean Streamlit UI with intuitive workflow
  - Real-time progress tracking
  - Expandable sections to view detailed results
  - Model selection options (1.5b and 4b variants)

- 🏠 **Local and Private**:
  - Uses Ollama for local model inference
  - No cloud API dependencies for core functionality
  - Complete privacy with local processing

## Prerequisites

1. **Ollama Installation**
   ```bash
   # Install Ollama (visit https://ollama.ai for installation instructions)
   # Pull required models
   ollama pull llama3.2:1b
   ollama pull llama3.2:3b
   ```

2. **SearXNG Instance** (Optional but recommended)
   ```bash
   # Run SearXNG using Docker
   docker run -d -p 8888:8080 searxng/searxng
   ```

## How to Run

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone <your-repository-url>
   cd ai_domain_deep_research_agent

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   Create a `.env` file in the project root:
   ```env
   SEARXNG_URL=http://localhost:8888
   ```

3. **Setup Configuration**
   Ensure your `config/config.yaml` file is properly configured:
   ```yaml
   model:
     COLLECTION_NAME: "research_agent"
     model: "llama3.2:1b"
     available_models:
       - "llama3.2:1b"
       - "llama3.2:3b"
   
   search_tools:
     search_options:
       - "duckduckgo"
       - "searxng"
   ```

4. **Run the Application**
   ```bash
   python ai_domain_deep_research_agent.py
   ```

## Usage

1. Launch the application using the command above
2. Select your preferred model version in the sidebar (1.5b for lighter processing, 4b for better results)
3. Input your research topic and domain in the main interface
4. Click "Generate Research Questions" to create specific questions
5. Review the questions and click "Start Research" to begin the research process
6. Once research is complete, click "Compile Final Report" to generate a professional report
7. View the report in the app and find the saved HTML file in the `reports/` directory

## Project Structure

```
ai_domain_deep_research_agent/
├── ai_domain_deep_research_agent.py  # Main application file
├── config/
│   └── config.yaml                   # Hydra configuration
├── src/
│   ├── agents.py                     # Agent initialization functions
│   ├── processing.py                 # Text processing utilities
│   └── tools.py                      # Custom search and utility tools
├── assets/
│   └── logo.png                      # Application logo
├── reports/                          # Generated reports directory
├── requirements.txt                  # Python dependencies
├── .env                             # Environment variables
└── README.md                        # This file
```

## Technical Details

- **Agno Framework**: Used for creating and orchestrating AI agents
- **Ollama**: Provides local language models (Llama 3.2 variants)
- **Custom Search Tools**: Integrates DuckDuckGo and SearXNG for web search
- **Streamlit**: Powers the user interface with interactive elements
- **Hydra**: Manages configuration and model selection
- **Local Storage**: Saves reports as HTML files in the reports directory

## Search Tools

### DuckDuckGo Search
- Provides comprehensive web search results
- No API key required
- Built-in privacy protection

### SearXNG Search
- Self-hosted metasearch engine
- Aggregates results from multiple search engines
- Configurable and privacy-focused
- Requires local SearXNG instance

## Example Use Cases

- **Academic Research**: Quickly gather information on academic topics across various disciplines
- **Market Analysis**: Research market trends, competitors, and industry developments
- **Policy Research**: Analyze policy implications and historical context
- **Technology Evaluation**: Research emerging technologies and their potential impact
- **Personal Research**: Investigate any topic of interest with structured methodology

## Configuration Options

### Model Selection
- **1.5b Model**: Lighter processing, suitable for most laptops
- **4b Model**: More capable but requires better GPU/RAM

### Search Configuration
- Configure search result limits
- Enable/disable full page content fetching
- Customize search timeout settings

## Dependencies

```txt
streamlit
agno
ollama
python-dotenv
hydra-core
omegaconf
duckduckgo-search
langchain-community
httpx
markdownify
langsmith
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check if models are pulled: `ollama list`

2. **SearXNG Not Available**
   - The app will still work with DuckDuckGo only
   - Check SearXNG container: `docker ps`

3. **Model Loading Issues**
   - Verify model names in config match Ollama models
   - Check available models: `ollama list`

4. **Report Generation Fails**
   - Ensure `reports/` directory exists
   - Check file permissions

## Performance Tips

- Use the 1.5b model for faster processing on limited hardware
- Adjust search result limits in the tools configuration
- Consider running SearXNG locally for better search performance

## Privacy and Security

- All processing happens locally with Ollama
- No data sent to external AI services
- Search queries go through DuckDuckGo and SearXNG only
- Reports saved locally on your machine

## License

This project is available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue in the repository.
