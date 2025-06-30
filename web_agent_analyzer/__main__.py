from web_agent_analyzer.analyzer import ResultAnalyzer

if __name__ == '__main__':
	run_id = 'try_multi_screenshot_1'
	analyzer = ResultAnalyzer(run_id)
	analyzer.generate_summary()
	analyzer.save_results()
	analyzer.generate_plots()
	analyzer.evaluate_tasks_with_errors()
	analyzer.save_results('results_evaluated.csv')
