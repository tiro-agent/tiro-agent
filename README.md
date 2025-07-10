# <img src="https://upload.wikimedia.org/wikipedia/commons/c/c8/Logo_of_the_Technical_University_of_Munich.svg" width="44">&ensp;Tiro - an autonomous web agent
This repository consists of a web agent that can be used to automate tasks on the live web. For more details, please refer to the system report.

> [!IMPORTANT]
> Please note that operating in a live web environment, as this agent does, may result in occasional inconsistencies or unexpected errors. Although multiple error-handling mechanisms are in place, some issues may still arise. Additionally, the use of a large language model introduces inherent unpredictability. For this reason, __YOU SHOULD NEVER USE THIS AGENT FOR SENSITIVE TASKS OR DATA.__ Please keep this in mind while using the agent.

## 🗂️ Project structure
This shows an excerpt of the project structure to highlight relevant directories.
```
├── data - benchmark data with task definitions
├── scripts - scripts for running and evaluating the web agent (you should use these)
├── tests - internal tests (only used during development)
├── web_agent - agent source code
└── web_agent_analyzer - analysis source code
```

## 🚀 Getting started
### Environment and dependencies
To get started, you need to install the required dependencies. This project uses [uv](https://docs.astral.sh/uv/), so make sure to you have it installed.

Then, create an environment and sync all dependencies:
```bash
uv sync
```

### Browser setup
Additionally, make sure that [Google Chrome](https://www.google.com/chrome/) is installed on your machine. The agent will use your existing copy as its browser environment.

### API keys
This project uses the [Gemini API](https://aistudio.google.com/apikey) for LLM inference. Please sign up there and create an API key under the free plan. You may want to consider using two API keys to enable parallel execution.

Additionally, the agent is able to log its API calls to [Pydantic Logfire](https://pydantic.dev/logfire). If this is desired, a Logfire project token is required. Please consult their [docs](https://logfire.pydantic.dev/docs/how-to-guides/create-write-tokens/) on how to set one up.

Finally, create a `.env` file in the root directory to store all keys:
```env
GEMINI_API_KEY=enter-API-key-here
GEMINI_API_KEY_2=enter-second-API-key-here-(optional)
LOGFIRE_TOKEN=enter-API-key-here-(optional)
```

## ⚙️ Usage
Usage of this agent is split into two steps to allow for greater flexibility.
### Running the agent
If you want to simply run all tasks in the Online-Mind2Web benchmark, there is a premade script provided for you:
```bash
./scripts/run_tasks.sh
```
Please change the `run_id` inside the script to your desired output name.

> [!NOTE]  
> This script is designed to be run from the root directory. Also, it is a Unix script, so it won't run on Windows. Please use the method described below in this case.


If you require more fine control over what tasks to run, you may alternatively use the agent's main method directly through uv:
```bash
uv run python -m web_agent
```
Please consult [this file](web_agent/__main__.py) for available command line arguments.

### Evaluating runs
You may use the following script to evaluate a prior run using statistics matching those in the system report:
```bash
./scripts/run_evaluation.sh
```
Please change the `run_id` inside the script to match the run to be evaluated.

## 📊 Performance
An evaluation of the agent’s performance on the Online-Mind2Web benchmark is provided in the system report, along with a discussion of common error cases.

## 🖥️ Tested on
MacOS 15.5, M2 Pro, Python 3.13.4<br>
MacOS 15.5, M1 Pro, Python 3.13.4

## 🚧 Known issues
__Gemini API instability:__ Occasionally, the Gemini API will either time out or produce invalid responses. This is a [known issue](https://discuss.ai.google.dev/t/persistent-500-error-for-gemini-2-5-flash-for-certain-prompts-even-after-an-hour-of-retries/89319) on Google's side as well. For now, the agent skips to the next tasks if this issue occurs. Should it happen too often, this can impact the accuracy of evaluation results. Thus, it is recommended to rerun those tasks before final evaluation.

## ✉️ Contact
This project: [Niklas Simakov (TUM CIT)](mailto:niklas.simakov@tum.de), [Karl Benedikt Kaesen (TUM CIT)](mailto:benedikt.kaesen@tum.de)<br>
Tutor: [Ludwig Felder (TUM CIT)](mailto:ludwig.felder@tum.de)<br>
Supervising chair: [Prof. Chunyang Chen (TUM CIT)](mailto:chun-yang.chen@tum.de)
