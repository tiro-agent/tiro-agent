import argparse
import json
import time

import nest_asyncio

from web_agent.agent.agent import Agent
from web_agent.agent.schemas import Task
from web_agent.browser.browser import Browser

nest_asyncio.apply()


def main() -> None:
	print('Hello from web-agent!')

	user_input = input("To avoid getting your IP blocked, it is recommended to use a VPN. Type 'y' to continue: ")
	while user_input.lower() != 'y':
		user_input = input("You did not confirm. Please type 'y' once your VPN is connected to continue: ")

	with open('data/Online_Mind2Web.json') as f:
		tasks = json.load(f)

	# some easy random tasks
	# mta: 4091bdd3fa64a5b0d912bc08eaf9c824
	# qatarairways: 005be9dd91c95669d6ddde9ae667125c (easy) (currently not working)
	# gamestop: 62f1626ce249c31098854f8b38bdd6cf (medium) (has to use search - not that easy)

	parser = argparse.ArgumentParser(description='Web Agent')
	parser.add_argument('--task-id', type=str, help='Task to perform (all if not given)', required=False)
	# parser.add_argument('--browser', type=str, help='Browser to use', required=True)
	parser.add_argument('--headless', action='store_true', help='Run in headless mode')
	args = parser.parse_args()

	# Find task
	if args.task_id is None:
		matching_tasks = tasks[1:5]
	else:
		matching_tasks = [t for t in tasks if t['task_id'] == args.task_id]

	if len(matching_tasks) == 0:
		print('ERROR: Task(s) not found')
		return

	time_str = time.strftime('%Y-%m-%d_%H-%M-%S')

	for i, task in enumerate(matching_tasks):
		print(f'============= Task {i} =============')
		print('Id:', task['task_id'])
		print('Task:', task['confirmed_task'])
		print('Website:', task['website'])

		with Browser(headless=args.headless) as browser:
			agent = Agent(browser)
			output_dir = f'output/{time_str}/{task["task_id"]}'
			result = agent.run(
				Task(identifier=task['task_id'], description=task['confirmed_task'], url=task['website'], output_dir=output_dir)
			)
			print('Result:', result)
		print('====================================\n\n')


if __name__ == '__main__':
	main()
