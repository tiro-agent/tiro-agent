import argparse
import time
import json

import nest_asyncio
from agent.agent import Agent
from browser.browser import Browser

nest_asyncio.apply()


def main():
	print('Hello from web-agent!')

	with open('data/Online_Mind2Web.json') as f:
		tasks = json.load(f)

	parser = argparse.ArgumentParser(description='Web Agent')
	parser.add_argument('--task-id', type=str, help='Task to perform', default='4091bdd3fa64a5b0d912bc08eaf9c824')
	# parser.add_argument('--browser', type=str, help='Browser to use', required=True)
	parser.add_argument('--headless', action='store_true', help='Run in headless mode')
	args = parser.parse_args()

	# Find task
	matching_tasks = [t for t in tasks if t['task_id'] == args.task_id]
	if len(matching_tasks) == 0:
		print('ERROR: Task not found')
		return
	
	task = matching_tasks[0]
	print('Task:', task['confirmed_task'])
	print('Website:', task['website'])

	with Browser(headless=args.headless) as browser:
		agent = Agent(browser)
		output_dir = 'output/' + time.strftime('%Y-%m-%d_%H-%M-%S') + '_' + args.task_id
		result = agent.run(task['confirmed_task'], task['website'], output_dir)
		print('Result:', result)


if __name__ == '__main__':
	main()
