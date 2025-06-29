import argparse

import logfire
import nest_asyncio
from dotenv import load_dotenv

from web_agent.runner import AgentRunner, Level, check_vpn

if __name__ == '__main__':
	nest_asyncio.apply()
	load_dotenv()

	parser = argparse.ArgumentParser(description='Web Agent')
	parser.add_argument('--run-id', type=str, help='Run id', required=False, default=None)
	parser.add_argument('--start-index', type=int, help='Start index', required=False, default=0)
	parser.add_argument('--task-id', type=str, help='Task to perform (all if not given)', required=False, default=None)
	parser.add_argument('--relevant-task-ids', nargs='+', type=str, help='Relevant task ids', required=False, default=None)
	parser.add_argument('--logfire', action='store_true', help='Enable logfire logging', required=False, default=False)
	parser.add_argument('--disable-vpn-check', action='store_true', help='Disable VPN check', required=False, default=False)
	parser.add_argument('--level', type=Level, help='Level', required=False, default=Level.ALL, choices=list(Level))
	args = parser.parse_args()

	print('Hello from web-agent!')

	if not args.disable_vpn_check:
		check_vpn()

	if args.logfire:
		logfire.configure()
		logfire.instrument_pydantic_ai()

	# overwrite for testing
	# args.relevant_task_ids = ['824eb7bb0ef1ce40bfd49c12182d9428', 'e4e097222d13a2560db6f6892612dab6']

	runner = AgentRunner(
		run_id=args.run_id,
		relevant_task_ids=args.relevant_task_ids,
		start_index=args.start_index,
	)

	if args.task_id is None:
		runner.run_all_tasks(level=args.level)
	else:
		runner.run_task_by_id(args.task_id)
