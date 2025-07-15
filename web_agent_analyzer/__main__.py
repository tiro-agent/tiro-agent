import argparse

import logfire
from dotenv import load_dotenv

from web_agent_analyzer.analyzer import ResultAnalyzer


def run_analysis(run_id: str) -> None:
	"""
	Runs the analysis for a specific run ID.
	"""
	analyzer = ResultAnalyzer(run_id)
	analyzer.evaluate_all_tasks()
	analyzer.generate_summary()
	analyzer.save_results('results.csv')
	analyzer.generate_plots()


if __name__ == '__main__':
	load_dotenv()

	parser = argparse.ArgumentParser()
	parser.add_argument('--run_id', type=str, required=True)
	parser.add_argument('--logfire', action='store_true', help='Enable logfire logging', required=False, default=False)
	args = parser.parse_args()
	run_id = args.run_id

	if args.logfire:
		logfire.configure()
		logfire.instrument_pydantic_ai()

	run_analysis(run_id)
