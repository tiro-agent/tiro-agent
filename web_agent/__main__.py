import argparse
import asyncio

import logfire
import nest_asyncio
from dotenv import load_dotenv

from web_agent.runner import AgentRunner, TaskLevel, check_vpn


async def main() -> None:
	nest_asyncio.apply()
	load_dotenv()

	parser = argparse.ArgumentParser(description='Web Agent')

	# Run ID determines output folder
	parser.add_argument('--run-id', type=str, help='Run id', required=False, default=None)

	# Configures which tasks to run
	parser.add_argument('--start-index', type=int, help='Start index', required=False, default=0)
	parser.add_argument('--task-id', type=str, help='Task to perform (all if not given)', required=False, default=None)
	parser.add_argument('--relevant-task-ids', nargs='+', type=str, help='Relevant task ids', required=False, default=None)
	parser.add_argument('--relevant-task-numbers', nargs='+', type=int, help='Relevant task numbers', required=False, default=None)
	parser.add_argument('--level', type=TaskLevel, help='Level', required=False, default=TaskLevel.ALL, choices=list(TaskLevel))

	# Step limit is determined by this factor times reference length (how many steps a human needs). Can be set to negative to use max steps instead.
	parser.add_argument('--step-factor', type=float, help='Step factor', required=False, default=2.5)

	# Max steps is the maximum number of steps to run. Default is -1, which means no limit. The smaller number between step factor and max steps will be used.
	parser.add_argument('--max-steps', type=int, help='Max steps', required=False, default=-1)

	# Other properties
	parser.add_argument('--logfire', action='store_true', help='Enable logfire logging', required=False, default=False)
	parser.add_argument('--disable-vpn-check', action='store_true', help='Disable VPN check', required=False, default=False)

	args = parser.parse_args()

	print('Hello from web-agent!')

	if args.relevant_task_ids is not None and args.relevant_task_numbers is not None:
		raise ValueError('Cannot use both --relevant-task-ids and --relevant-task-numbers')

	if args.step_factor <= 0 and args.max_steps <= 0:
		raise ValueError('Please set either step factor or max steps to a positive value')

	if not args.disable_vpn_check:
		check_vpn()

	if args.logfire:
		logfire.configure()
		logfire.instrument_pydantic_ai()

	# overwrite for testing
	# args.relevant_task_ids = ['824eb7bb0ef1ce40bfd49c12182d9428', 'e4e097222d13a2560db6f6892612dab6']

	# Initialize agent runner
	runner = AgentRunner(
		run_id=args.run_id,
		relevant_task_ids=args.relevant_task_ids,
		relevant_task_numbers=args.relevant_task_numbers,
		start_index=args.start_index,
		step_factor=args.step_factor,
		max_steps=args.max_steps,
	)

	if args.task_id is None:
		# If no task is given, run all tasks
		await runner.run_all_tasks(level=args.level)
	else:
		# Otherwise, run given task
		await runner.run_task_by_id(args.task_id)


if __name__ == '__main__':
	asyncio.run(main())
