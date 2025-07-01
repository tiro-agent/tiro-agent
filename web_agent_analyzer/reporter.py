from pathlib import Path

import matplotlib.pyplot as plt
from pandera.typing import DataFrame

from web_agent.agent.schemas import SpecialAgentErrors
from web_agent_analyzer.schemas import ResultSchema


def generate_summary(
	results: DataFrame[ResultSchema], results_cleaned: DataFrame[ResultSchema], analysis_folder: Path, print_summary: bool = True
) -> None:
	summary = ''
	summary += 'SUMMARY\n'
	summary += f'Found {len(results)} tasks\n'
	summary += '-' * 100 + '\n'
	summary += 'After cleaning (removing LLM_ERROR, URL_BLOCKED, URL_LOAD_ERROR)\n\n'
	summary += f'Found {len(results_cleaned)} tasks after cleaning\n'
	summary += f'Successfully completed tasks: {len(results_cleaned[results_cleaned[ResultSchema.success]])}\n'
	summary += f'Success rate: {len(results_cleaned[results_cleaned[ResultSchema.success]]) / len(results_cleaned) * 100:.2f}%\n'
	summary += '\nSuccess rate by level:\n'
	for level in results_cleaned[ResultSchema.level].unique():
		level_tasks = results_cleaned[results_cleaned[ResultSchema.level] == level]
		successful_level_tasks = results_cleaned[(results_cleaned[ResultSchema.level] == level) & (results_cleaned[ResultSchema.success])]
		success_rate = len(successful_level_tasks) / len(level_tasks) * 100
		summary += f'{level}: {success_rate:.2f}% ({len(successful_level_tasks)}/{len(level_tasks)})\n'
	summary += '\nSpecial error types:\n'
	for error_type in results_cleaned[ResultSchema.run_error_type].unique():
		if error_type is None:
			continue
		summary += f'{error_type}: {len(results_cleaned[results_cleaned[ResultSchema.run_error_type] == error_type])}\n'
	summary += '-' * 100 + '\n'

	llm_error_tasks = results[results[ResultSchema.run_error_type] == SpecialAgentErrors.LLM_ERROR.value]
	summary += f'Found {len(llm_error_tasks)} tasks with LLM_ERROR\n'
	for task_number in llm_error_tasks[ResultSchema.task_number]:
		summary += f'{task_number} '
	summary += '\n' + '-' * 100 + '\n'

	url_blocked_tasks = results[results[ResultSchema.run_error_type] == SpecialAgentErrors.URL_BLOCKED.value]
	summary += f'Found {len(url_blocked_tasks)} tasks with URL_BLOCKED\n'
	for task_number in url_blocked_tasks[ResultSchema.task_number]:
		summary += f'{task_number} '
	summary += '\n' + '-' * 100 + '\n'

	url_load_error_tasks = results[results[ResultSchema.run_error_type] == SpecialAgentErrors.URL_LOAD_ERROR.value]
	summary += f'Found {len(url_load_error_tasks)} tasks with URL_LOAD_ERROR\n'
	for task_number in url_load_error_tasks[ResultSchema.task_number]:
		summary += f'{task_number} '
	summary += '\n' + '-' * 100 + '\n'

	if print_summary:
		print(summary)

	with open(analysis_folder / 'summary.txt', 'w') as f:
		f.write(summary)


def generate_plots(results: DataFrame[ResultSchema], analysis_folder: Path) -> None:
	_generate_plot_success_rate(results, analysis_folder)
	_generate_plot_success_rate_by_level(results, analysis_folder)
	_generate_plot_error_types_pre_evaluation(results, analysis_folder)


def _generate_plot_success_rate(results: DataFrame[ResultSchema], analysis_folder: Path) -> None:
	success_counts = results[ResultSchema.success].value_counts()
	if len(success_counts) == 0:
		return
	plt.figure(figsize=(10, 5))
	plt.pie(success_counts.values, labels=['Failed', 'Success'], autopct='%1.1f%%')
	plt.title('Success Rate')
	plt.savefig(analysis_folder / 'success_rate.png')
	plt.close()


def _generate_plot_success_rate_by_level(results: DataFrame[ResultSchema], analysis_folder: Path) -> None:
	unique_levels = results[ResultSchema.level].unique()
	if len(unique_levels) == 0 or unique_levels[0] is None:
		return
	for level in unique_levels:
		level_df = results[results[ResultSchema.level] == level]
		if len(level_df) == 0:
			continue
		success_counts = level_df[ResultSchema.success].value_counts()
		plt.figure(figsize=(10, 5))
		plt.pie(success_counts.values, labels=['Failed', 'Success'], autopct='%1.1f%%')
		plt.title(f'Success Rate for {level.capitalize()} Level Tasks')
		plt.savefig(analysis_folder / f'success_rate_by_level_{level}.png')
		plt.close()


def _generate_plot_error_types_pre_evaluation(results: DataFrame[ResultSchema], analysis_folder: Path) -> None:
	failed_tasks = results[results[ResultSchema.error_type].notna()]
	if len(failed_tasks) == 0:
		print('No errors found - all tasks were successful!')
		return
	error_counts = failed_tasks[ResultSchema.error_type].value_counts()
	if len(error_counts) > 0:
		plt.figure(figsize=(10, 5))
		plt.pie(error_counts.values, labels=error_counts.index, autopct='%1.1f%%')
		plt.title('Distribution of Error Types (Failed Tasks Only)')
		plt.savefig(analysis_folder / 'error_types_pre_evaluation.png')
		plt.close()


def generate_plot_error_types_post_evaluation(results: DataFrame[ResultSchema], analysis_folder: Path) -> None:
	# results are already post-evaluation
	failed_tasks = results[results[ResultSchema.error_type].notna()]
	if len(failed_tasks) == 0:
		print('No errors found - all tasks were successful!')
		return
	error_counts = failed_tasks[ResultSchema.error_type].value_counts()
	if len(error_counts) > 0:
		plt.figure(figsize=(10, 5))
		plt.pie(error_counts.values, labels=error_counts.index, autopct='%1.1f%%')
		plt.title('Distribution of Error Types (Failed Tasks Only) (Post-Evaluation)')
		plt.savefig(analysis_folder / 'error_types_post_evaluation.png')
		plt.close()
