import argparse
from browser.browser import Browser
from agent.agent import Agent
import nest_asyncio
nest_asyncio.apply()

def main():
	print('Hello from web-agent!')

	tasks = { # TODO: Load actual dataset
		'QR': ('https://www.qatarairways.com/', 'Find the weight of baggage allowance for economy class on Qatar Airways.'),
		'MTA': ('https://new.mta.info/', 'Find the list of neighborhood maps for Brooklyn on new.mta.info.'),
		'Apple': ('https://www.apple.com/', 'Find technical specs for the latest Macbook Air on Apple.')
	}
 
	parser = argparse.ArgumentParser(description='Web Agent')
	parser.add_argument('--task-id', type=str, help='Task to perform', default='MTA')
	# parser.add_argument('--browser', type=str, help='Browser to use', required=True)
	parser.add_argument('--headless', action='store_true', help='Run in headless mode')
	args = parser.parse_args()
 
	with Browser(headless=args.headless) as browser:
		agent = Agent(browser)
		result = agent.run(tasks[args.task_id][1], tasks[args.task_id][0], 'output')
		print('Result:', result)

if __name__ == '__main__':
	main()
