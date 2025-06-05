# An automated web agent with a stealth browser

The package consists of a web agent that uses a stealth browser with a captcha solver.

## Stack

- Python: >=3.13
- Formatter: Ruff (please install the vscode extension [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff))

### Browser

- Browser: Chrome
- Browser simulator: [Playwright](https://playwright.dev/) with [playwright-stealth](https://github.com/AtuboDad/playwright_stealth)
- Captcha solver: [2captcha API](https://2captcha.com/)

### Web Agent

- [PydanticAI](https://ai.pydantic.dev/): a library for building AI agents
- [Pydantic](https://docs.pydantic.dev/latest/): a library for data validation and settings management

## Project Structure

For detailed information about the project structure, see the Notion docs.

## How to run

1. Install dependencies (make sure you have [uv](https://docs.astral.sh/uv/) installed)

```bash
uv sync
```

2. Download the browsers with the playwright cli

```bash
uv run playwright install
```

3. Create a .env file with the required API keys, see [.env.example](.env.example)

- GEMINI_API_KEY - set the [Gemini API](https://aistudio.google.com/apikey) key
- (CURRENTLY NOT USED) 2CAPTCHA_API_KEY - set the [2captcha](https://2captcha.com/) API key

4. Run the script

```bash
uv run web_agent/main.py
```

- you can also use the vscode task to run the script (just press `Ctrl+Shift+B` and select `UV run (python)`)
- you can also click on the `Run and Debug` button in the top right corner and select `Python: Current File`

5. Run the tests

```bash
uv run pytest
```

6. Run the formatter & linter

```bash
uv run ruff check --fix # check & fix linting
uv run ruff format # format the code
```

- The formatter & linter will automatically run if you save the file and the [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) extension is installed in vscode
- If you only want to check whether the code is formatted correctly, run `uv run ruff format --check`

## Contribution Guidelines

### Commit messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(optional-scope): short summary

[optional body]
```

#### Common Commit Types

| Type       | Purpose                               |
| ---------- | ------------------------------------- |
| `feat`     | Add new feature                       |
| `fix`      | Fix a bug                             |
| `chore`    | Maintenance tasks (e.g. deps, config) |
| `docs`     | Documentation changes                 |
| `refactor` | Code improvements, no behavior change |
| `style`    | Formatting, whitespace, linter fixes  |
| `test`     | Add or modify tests                   |
| `build`    | Build system or dependencies changes  |
| `ci`       | CI/CD pipeline configuration changes  |

#### Commit Examples

```
feat(browser): add persistent session handling
fix(agent): handle null return from LLM call
docs(readme): update installation instructions
refactor(utils): extract selector parsing logic
```

---

### Branch Naming Convention

Use a prefix + short description in `kebab-case`.

| Prefix      | Example Branch Name          |
| ----------- | ---------------------------- |
| `feat/`     | `feat/agent-decision-loop`   |
| `fix/`      | `fix/llm-response-timeout`   |
| `chore/`    | `chore/upgrade-dependencies` |
| `docs/`     | `docs/setup-instructions`    |
| `refactor/` | `refactor/browser-utils`     |
| `test/`     | `test/session-storage-tests` |
| `hotfix/`   | `hotfix/null-agent-crash`    |

### PR Title Format

Use the same format as commits:
<type>(optional-scope): short summary
