# Cursor CLI Heavy Research System

A parallel research orchestration tool that leverages multiple AI assistants to conduct comprehensive research on any topic. The system spawns multiple `cursor-agent` workers in parallel, each with specialized focus areas, then synthesizes their findings into a unified analysis.

## 🚀 Features

- **Parallel Research**: Deploy 2-8 AI research assistants simultaneously
- **Intelligent Orchestration**: Automatic planning and role assignment based on query complexity
- **Specialized Focus Areas**: Each assistant tackles different aspects (facts, analysis, criticisms, case studies, etc.)
- **Comprehensive Synthesis**: Final unified report combining all perspectives
- **Flexible Output**: Support for both Markdown and plain text formats
- **Directory Analysis**: Optional analysis of specific codebases or project directories
- **Organized Output**: Timestamped, structured output directories for easy organization

## 📋 Prerequisites

- **Cursor CLI**: The system requires `cursor-agent` to be installed and available in your PATH
- **Python 3.13**: For running the orchestration system

### Installing Cursor CLI

```bash
curl https://cursor.com/install -fsS | bash
```

Verify installation:
```bash
cursor-agent --help
```

## 🛠️ Installation

1. **Clone or download the project**:
```bash
git clone https://github.com/karayaman/cursor-cli-heavy.git
cd cursor-cli-heavy
```

2. **Create and activate virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Interactive Mode

Run without arguments to enter interactive mode:

```bash
python main.py
```

The system will prompt you for:
- Research query
- Output format (markdown/text)
- Working directory (optional)

### Command Line Mode

```bash
python main.py "Your research query here" [options]
```

#### Options

- `-f, --format {markdown,text}`: Output format (default: markdown)
- `-w, --workdir PATH`: Working directory to analyze (absolute path)
- `--no-prompt`: Skip confirmation and run immediately

## 📁 Output Structure

The system creates organized output directories with timestamps:

```
outputs/
└── 2024-01-20-your-research-topic/
    ├── research-plan.md           # Initial research strategy
    ├── planning-session.log       # Orchestrator planning output
    ├── orchestration-prompt.md    # Orchestrator instructions
    ├── assistants/
    │   ├── ra-1-findings.md      # Research Assistant 1 findings
    │   ├── ra-2-findings.md      # Research Assistant 2 findings
    │   ├── ra-3-findings.md      # Research Assistant 3 findings
    │   └── ra-4-findings.md      # Research Assistant 4 findings
    └── final-analysis.md         # Synthesized comprehensive report
```

## 🧠 How It Works

### 1. Planning Phase
- An orchestrator AI analyzes your query
- Determines optimal number of research assistants (2-8)
- Assigns specialized focus areas to each assistant

### 2. Parallel Research Phase
- Multiple `cursor-agent` instances run simultaneously
- Each assistant researches from their specific angle:
  - **RA-1**: Factual research and direct information
  - **RA-2**: Analysis and metrics
  - **RA-3**: Alternative perspectives and criticisms
  - **RA-4**: Case studies and examples
  - **RA-5**: Implementation challenges and risks
  - **RA-6**: Future trends and research gaps
  - **RA-7**: Ethical, legal, and societal implications
  - **RA-8**: Contrarian views and edge cases

### 3. Synthesis Phase
- A synthesis AI combines all findings
- Creates executive summary, key findings, and recommendations
- Identifies areas of agreement and disagreement

## 🔧 Project Structure

```
cursor-cli-heavy/
├── main.py              # Entry point and argument parsing
├── ccheavy.py          # Core CCHeavy class and orchestration logic
├── requirements.txt    # Python dependencies
└── venv/              # Virtual environment (created after setup)
```

## ⚙️ Configuration

The system is designed to work out-of-the-box with sensible defaults:

- **Default assistants**: 4 (automatically adjusted based on query complexity)
- **Maximum assistants**: 8
- **Default format**: Markdown
- **Model**: GPT-5 (via cursor-agent)

## 🎨 Example Queries

### Technology Research
```bash
python main.py "Quantum computing applications in cryptography"
```

### Business Analysis
```bash
python main.py "Market opportunities for sustainable packaging"
```

### Codebase Analysis
```bash
python main.py "Performance bottlenecks in this web application" -w /path/to/webapp
```

### Academic Research
```bash
python main.py "Recent advances in neural network interpretability"
```

### Game Development
```bash
python main.py "Create a 2D Tetris game using HTML, CSS, and JavaScript. At the synthesis step, I want it to be implemented in the specified directory." -w /path/to/game/directory
```

## 🚨 Troubleshooting

### "cursor-agent command not found"
- Ensure Cursor CLI is installed: `curl https://cursor.com/install -fsS | bash`
- Restart your terminal after installation
- Verify with: `cursor-agent --help`

### Empty or Failed Assistant Outputs
- The system includes automatic retry logic
- Check `assistants/ra-X-stderr.log` files for error details
- Ensure you have a stable internet connection
- Verify your Cursor CLI authentication

### Permission Errors
- Ensure the working directory (if specified) is readable
- Check that the current directory is writable for output creation

## 🔒 Security Notes

- All outputs are saved to isolated timestamped directories
- Temporary directories are automatically cleaned up

## 📚 Dependencies

- **colorama**: Terminal color output (fallback included if not available)
- **cursor-agent**: AI research agent (external dependency)

## 🤝 Contributing

This is a research orchestration tool. Contributions welcome for:
- Additional output formats
- Enhanced error handling
- Performance optimizations
- New assistant specialization areas

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: This tool requires an active Cursor CLI installation and internet connectivity for AI model access. The quality of research depends on the capabilities of the underlying `cursor-agent` and GPT-5 model.
