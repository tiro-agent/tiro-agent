import argparse
import json
import time

import logfire
import nest_asyncio
from dotenv import load_dotenv

from web_agent.agent.agent import Agent
from web_agent.agent.schemas import Task
from web_agent.browser.browser import Browser

nest_asyncio.apply()
load_dotenv()


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
	parser.add_argument('--logfire', action='store_true', help='Enable logfire logging')
	args = parser.parse_args()

	start_i = 0
	# revelant_tasks = ['824eb7bb0ef1ce40bfd49c12182d9428', '92a3d4236f167af4afdc08876a902ba6', '8f2611047de227a2ca8bda13f6e2e5fb', 'aa4b5cb7114fcc138ade82b4b9716d24', '6ebde509dca8f15c0fa1bd74f071e8d6', '0b51b4fa0295ae80ccd176ebdad6fff6', 'b64f938af842f6a1b4489d0e49a785a7', '8fdec8eeffd3491e6526cc78c028120b', 'a7a73c8fa75441fc76df9746c327bdd6', '816851ff92ff0219acf4364dcc2c4692', '8244409b2c82043f966cad05f9afe132', 'b3f8bd9198d9d157e0848109563c4b23', 'db1ffb5e60578597d1c3aa3c389ac7b1', '7be8cd8dba885cddd9af5320f49bc41b', '239a29bde438fe44fe17fe1390ef1634', '9f1cba613830ca1c6a58f9498c06e679', '75146b7b67388b9244e0f21a1527c022', '871e7771cecb989972f138ecc373107b', 'b69eb4de621e9e265676daac44938f3f', '8ae510355d978424f490798f900bfa2c', '4c186c6ed888d0c8d4cf4adb39443080', 'eb323dc584156d0eb3a2b90bb8c4b791', '354b4ddf048815f8fd4163d0d7e1aaa3', 'e4e097222d13a2560db6f6892612dab6']

	# Find task
	if args.task_id is None:
		matching_tasks = tasks[start_i:]
		# matching_tasks = [t for t in matching_tasks if t['task_id'] in revelant_tasks]
	else:
		matching_tasks = [t for t in tasks if t['task_id'] == args.task_id]

	if len(matching_tasks) == 0:
		print('ERROR: Task(s) not found')
		return

	if args.logfire:
		logfire.configure()
		logfire.instrument_pydantic_ai()

	time_str = time.strftime('%Y-%m-%d_%H-%M-%S')
	# time_str = '2025-06-16_12-28-10'

	for i, task in enumerate(matching_tasks):
		nr = start_i + i
		print(f'============= Task {nr} =============')
		print('Id:', task['task_id'])
		print('Task:', task['confirmed_task'])
		print('Website:', task['website'])

		with Browser(headless=args.headless) as browser:
			agent = Agent(browser)
			output_dir = f'output/{time_str}/{nr:03d}_{task["task_id"]}'
			try:
				result = agent.run(
					Task(
						identifier=task['task_id'],
						description=task['confirmed_task'],
						url=task['website'],
						output_dir=output_dir,
						max_steps=40,
					)
				)
				print('Result:', result)
			except Exception as e:
				print(f'Task {nr} failed with following exception:', e)
		print('====================================\n\n')


if __name__ == '__main__':
	main()
