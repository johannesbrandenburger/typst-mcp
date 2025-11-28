# Typst MCP Server

Typst MCP Server is an [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) implementation that helps AI models interact with [Typst](https://github.com/typst/typst), a markup-based typesetting system. The server provides tools for converting between LaTeX and Typst, validating Typst syntax, and generating images from Typst code.

## Available Tools

>⚠️ Currently all the functionality is implemented as `tools`, because Cursor and VS Code are not able to handle the other primitives yet.

The server provides the following tools:

1. **`list_docs_chapters()`**: Lists all chapters in the Typst documentation.
   - Lets the LLM get an overview of the documentation and select a chapter to read.
   - The LLM should select the relevant chapter to read based on the task at hand.

2. **`get_docs_chapter(route)`**: Retrieves a specific chapter from the Typst documentation.
   - Based on the chapter selected by the LLM, this tool retrieves the content of the chapter.
   - Also available as `get_docs_chapters(routes: list)` for retrieving multiple chapters at once.

3. **`latex_snippet_to_typst(latex_snippet)`**: Converts LaTeX code to Typst using Pandoc.
   - LLMs are better at writing LaTeX than Typst, so this tool helps convert LaTeX code to Typst.
   - Also available as `latex_snippets_to_typst(latex_snippets: list)` for converting multiple LaTeX snippets at once.

4. **`check_if_snippet_is_valid_typst_syntax(typst_snippet)`**: Validates Typst code.
   - Before sending Typst code to the user, the LLM should check if the code is valid.
   - Also available as `check_if_snippets_are_valid_typst_syntax(typst_snippets: list)` for validating multiple Typst snippets at once.

5. **`typst_to_image(typst_snippet)`**: Renders Typst code to a PNG image.
   - Before sending complex Typst illustrations to the user, the LLM should render the code to an image and check if it looks correct.
   - Only relevant for multi modal models.

## Getting Started

- Clone this repository
  - `git clone https://github.com/johannesbrandenburger/typst-mcp.git`
- Clone the [typst repository](https://github.com/typst/typst.git)
  - `git clone https://github.com/typst/typst.git`
- Run the docs generation in the typst repository
  - `cargo run --package typst-docs -- --assets-dir ../typst-mcp/typst-docs --out-file ../typst-mcp/typst-docs/main.json`
    - Make sure to adjust the path to your local clone of the typst-mcp repository
    - This will generate the `main.json` and the assets in the `typst-docs` folder
- Install required dependencies: `uv sync` (install [uv](https://github.com/astral-sh/uv) if not already installed)
  
- Install Typst

## Running the Server

### Local Installation

Execute the server script:

```bash
python server.py
```

Or install it in Claude Desktop with MCP:

```bash
mcp install server.py
```

Or use the new agent mode in VS Code:

[Agent mode: available to all users and supports MCP](https://code.visualstudio.com/blogs/2025/04/07/agentMode)

### Docker

For Docker installation and usage, see [DOCKER.md](DOCKER.md) for detailed build information and instructions.

## Platform Configuration

This MCP server can be integrated with various AI coding platforms. Below are configuration instructions for popular platforms:

### Claude Desktop

Add the following to your Claude Desktop configuration file (`claude_desktop_config.json`):

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "typst": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ]
    }
  }
}
```

Or for local installation:

```json
{
  "mcpServers": {
    "typst": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ]
    }
  }
}
```

### Cursor

Create `.cursor/mcp.json` in your project root for project-specific configuration:

```json
{
  "mcpServers": {
    "typst": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ]
    }
  }
}
```

Or create `~/.cursor/mcp.json` for global configuration. For local installation:

```json
{
  "mcpServers": {
    "typst": {
      "command": "python",
      "args": ["/path/to/typst-mcp/server.py"]
    }
  }
}
```

### Roo Code

Create `.roo/mcp.json` in your project root for project-specific configuration:

```json
{
  "mcpServers": {
    "typst": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ]
    }
  }
}
```

Or edit global settings via Roo Code MCP settings view. For local installation:

```json
{
  "mcpServers": {
    "typst": {
      "command": "python",
      "args": ["/path/to/typst-mcp/server.py"]
    }
  }
}
```

### OpenCode

Create or edit the `opencode.json` file in your project root:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "typst": {
      "type": "local",
      "command": ["docker", "run", "--rm", "-i", 
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ],
      "enabled": true
    }
  }
}
```

For local installation:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "typst": {
      "type": "local",
      "command": ["python", "/path/to/typst-mcp/server.py"],
      "enabled": true
    }
  }
}
```

### Claude Code

Configure MCP servers in your Claude Code settings file (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "typst": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ]
    }
  }
}
```

Or for local installation:

```json
{
  "mcpServers": {
    "typst": {
      "command": "python",
      "args": ["/path/to/typst-mcp/server.py"]
    }
  }
}
```

### VS Code with Agent Mode

VS Code's Agent Mode has native MCP support (no extension required):

1. Enable Agent Mode in VS Code settings (`chat.agent.enabled`)
2. Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "typst": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/johannesbrandenburger/typst-mcp:latest"
      ]
    }
  }
}
```

For global configuration, add to your user profile via **MCP: Open User Configuration** command.

## JSON Schema of the Typst Documentation

>⚠️ The schema of the typst documentation is not stable and may change at any time. The schema is generated from the typst source code and is not guaranteed to be complete or correct. If the schema changes, this repository will need to be updated accordingly, so that the docs functionality works again.