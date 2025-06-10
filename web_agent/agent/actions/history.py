from pydantic import BaseModel, Field

from web_agent.agent.actions.base import ActionResultStatus, BaseAction


class ActionsHistoryStep(BaseModel):
	"""The step of the action history."""

	action: BaseAction = Field(..., description='The action that was performed.')
	status: ActionResultStatus = Field(..., description='The status of the action.')
	message: str = Field(..., description='The message from the action.')
	screenshot: str = Field(..., description='The path to the screenshot of the action.')


class ActionsHistoryController:
	"""Controller for the action history."""

	def __init__(self) -> None:
		self.action_history: list[ActionsHistoryStep] = []

	def add_action(self, action: ActionsHistoryStep) -> None:
		self.action_history.append(action)

	def get_action_history(self) -> list[ActionsHistoryStep]:
		return self.action_history

	def get_action_history_str(self) -> str:
		return 'Prior actions: \n- ' + '\n- '.join(
			[
				f'ACTION: {step.action.get_action_str()}, [{step.status.value.capitalize()}]{
					", MESSAGE: " + step.message if step.status is not ActionResultStatus.SUCCESS else ""
				}'
				for step in self.action_history
			]
		)
