import argparse

from web_agent_analyzer.analyzer import ResultAnalyzer


def run_analysis(run_id: str) -> None:
	analyzer = ResultAnalyzer(run_id)
	analyzer.evaluate_all_tasks()
	analyzer.generate_summary()
	analyzer.save_results('results.csv')
	analyzer.generate_plots()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--run_id', type=str, required=True)
	args = parser.parse_args()
	run_id = args.run_id

	run_analysis(run_id)
