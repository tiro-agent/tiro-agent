# Stealth browser with captcha solver

## Stack

- Browser: Chrome
- Browser simulator: Playwright with playwright-stealth
- Captcha solver: 2captcha API
- Python: >=3.13
- Formatter: Ruff (please install the vscode extension [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff))

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

- you can get the 2captcha API key from [2captcha](https://2captcha.com/)

4. Run the script

```bash
uv run browser.py
```

- you can also use the vscode task to run the script (just press `Ctrl+Shift+B` and select `UV run (python)`)
- you can also click on the `Run and Debug` button in the top right corner and select `Python: Current File` (while the browser.py file is open)

5. Run the tests

```bash
uv run pytest
```

6. Run the formatter & linter

```bash
uv run ruff check --fix # check if the code is linted correctly and fix it
uv run ruff format # format the code correctly (automatically run if you save the file and the ruff extension is installed)
```

(if you only want to check if the code is formatted correctly, run `uv run ruff format --check`)
