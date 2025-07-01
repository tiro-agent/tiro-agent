import argparse

from web_agent_analyzer.analyzer import ResultAnalyzer


def run_analysis(run_id: str) -> None:
	analyzer = ResultAnalyzer(run_id)
	analyzer.generate_summary()
	analyzer.save_results()
	analyzer.generate_plots()
	analyzer.evaluate_tasks_with_errors()
	analyzer.save_results('results_evaluated.csv')
	analyzer.generate_plots_post_evaluation()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--run_id', type=str, required=True)
	args = parser.parse_args()
	run_id = args.run_id

	run_analysis(run_id)
