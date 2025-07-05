from pydantic_ai import BinaryContent

from web_agent.agent.agent import Agent
from web_agent.browser.browser import Browser


def test_build_user_prompt() -> None:
	"""Tests if the user prompt is built correctly."""
	browser = Browser()
	agent = Agent(browser)
	metadata = {'title': 'Test', 'url': 'https://www.google.com'}
	past_actions_str = 'Past actions'
	available_actions_str = 'Available actions'

	# test with no previous screenshots
	previous_screenshots_paths = []
	current_screenshot_path = 'tests/data/task_data_002/trajectory/0_full_screenshot.png'

	previous_screenshots = [open(screenshot_path, 'rb').read() for screenshot_path in previous_screenshots_paths]
	current_screenshot = open(current_screenshot_path, 'rb').read()

	prompt_str = '\n'
	prompt_str += f'Metadata: \n{metadata!s}\n\n'
	prompt_str += f'Past actions:\n{past_actions_str}\n\n'
	prompt_str += f'Available actions:\n{available_actions_str}\n\n'
	prompt_str += 'Choose the next action to take.\n'

	expected_prompt = [
		prompt_str,
		'Current screenshot:',
		BinaryContent(data=current_screenshot, media_type='image/png'),
	]

	prompt = agent._build_user_prompt(metadata, past_actions_str, available_actions_str, previous_screenshots, current_screenshot)
	assert prompt == expected_prompt

	# test with previous screenshots
	previous_screenshots_paths = [
		'tests/data/task_data_002/trajectory/0_full_screenshot.png',
		'tests/data/task_data_002/trajectory/1_full_screenshot.png',
	]
	current_screenshot_path = 'tests/data/task_data_002/trajectory/2_full_screenshot.png'

	previous_screenshots = [open(screenshot_path, 'rb').read() for screenshot_path in previous_screenshots_paths]
	current_screenshot = open(current_screenshot_path, 'rb').read()

	expected_prompt = [
		prompt_str,
		'Previous screenshots:',
		*[BinaryContent(data=screenshot, media_type='image/png') for screenshot in previous_screenshots],
		'Current screenshot:',
		BinaryContent(data=current_screenshot, media_type='image/png'),
	]

	prompt = agent._build_user_prompt(metadata, past_actions_str, available_actions_str, previous_screenshots, current_screenshot)
	assert prompt == expected_prompt
