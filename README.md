# An autonomous web agent

The package consists of a web agent that can be used to automate tasks on the web.

## Stack

- Python: >=3.13
- Formatter: Ruff (please install the vscode extension [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff))

### Browser

- Browser: Chrome
- Browser simulator: [Playwright](https://playwright.dev/)

### Web Agent

- [PydanticAI](https://ai.pydantic.dev/): a library for building AI agents
- [Pydantic](https://docs.pydantic.dev/latest/): a library for data validation and settings management

## Project Structure

For detailed information about the project structure, see the Notion docs.

## How to run

### 1. Install dependencies (make sure you have [uv](https://docs.astral.sh/uv/) installed)

```bash
uv sync
```

### 2. Make sure you have the chrome browser installed on your machine

- if you don't have it installed, we recommend you to download it from the [chrome website](https://www.google.com/chrome/)

```bash
# Currently not needed, because we use the chrome browser installed on your machine
# uv run playwright install # installs the defaults (chromium, firefox, webkit)
```

- do not install the chrome browser with playwright, as it will override your existing chrome installation (if you have it installed), as seen in the [docs](https://playwright.dev/python/docs/browsers#:~:text=Google%20Chrome%20or%20Microsoft%20Edge%20installations%20will%20be%20installed%20at%20the%20default%20global%20location%20of%20your%20operating%20system%20overriding%20your%20current%20browser%20installation.)

### 3. Create a .env file with the required API keys, see [.env.example](.env.example)

- GEMINI_API_KEY - set the [Gemini API](https://aistudio.google.com/apikey) key
- LOGFIRE_TOKEN (optional) - if you want to use [Pydantic Logfire](https://pydantic.dev/logfire)

### 4. Run the script

```bash
uv run python -m web_agent
```

- you have to run it as a module, otherwise the imports will not work
- you can also click on the `Run and Debug` menu section and select `RUN: web-agent module` (you can also see the task in [.vscode/launch.json](.vscode/launch.json))
- you can also use the vscode task to run the script (select `RUN: uv run opened module`) (see [.vscode/tasks.json](.vscode/tasks.json))
- note: the `Run Python File` option in the top right corner is not working, due to the import structure of the project

### 5. Run the tests

```bash
uv run -m pytest
```

- you can also use the vscode task to run the tests (select `TEST: uv run all tests (pytest)`) (see [.vscode/tasks.json](.vscode/tasks.json))
- you can also click on the `Run and Debug` menu section and select `TEST: all files` (you can also see the task in [.vscode/launch.json](.vscode/launch.json))

### 6. Run the formatter & linter

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
