# Stealth browser with captcha solver

## Stack
- Browser: Chrome
- Browser simulator: Playwright with playwright-stealth
- Captcha solver: 2captcha API
- Python: >=3.13

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
