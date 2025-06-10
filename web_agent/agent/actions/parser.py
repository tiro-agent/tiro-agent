import ast

from web_agent.agent.actions.actions import BaseAction


class ActionParser:
	"""Parser for action strings that converts them into BaseAction instances."""

	def parse(self, action_str: str, action_types: list[type[BaseAction]]) -> BaseAction:
		"""Parse an action string into a BaseAction instance using the provided action types."""
		action_str = self._clean_action_str(action_str)

		try:
			# Parse as Python expression using AST
			parsed = ast.parse(action_str, mode='eval')
			call_node = parsed.body

			# TODO: if ever needed, add additional security checks here (complex function names, DoS attacks, malicious arguments, etc.)

			if not isinstance(call_node, ast.Call):
				raise ValueError(f'Expected function call, got: {action_str}')

			# Extract function name
			if not isinstance(call_node.func, ast.Name):
				raise ValueError(f'Expected simple function name, got: {action_str}')

			action_name = call_node.func.id
			action_type = self._get_action_by_name(action_name, action_types)

			if action_type is None:
				raise ValueError(f'Action type not found: {action_name}')

			# Extract arguments and convert to kwargs
			kwargs = self._extract_kwargs_from_call(call_node, action_type)

			# Create and return the action
			return action_type(**kwargs)

		except SyntaxError as e:
			raise ValueError(f'Invalid syntax in action string "{action_str}": {e}') from e
		except Exception as e:
			raise ValueError(f'Failed to parse action string "{action_str}": {e}') from e

	def _clean_action_str(self, action_str: str) -> str:
		"""Clean and validate the action string."""
		action_str = action_str.strip()
		if not action_str:
			raise ValueError('Action string is empty')

		# Add parentheses if missing
		if '(' not in action_str:
			action_str = f'{action_str}()'

		return action_str

	def _extract_kwargs_from_call(self, call_node: ast.Call, action_type: type[BaseAction]) -> dict:
		"""Extract keyword arguments from AST call node."""
		kwargs = {}
		field_names = list(action_type.model_fields.keys())

		# Handle positional arguments
		for i, arg in enumerate(call_node.args):
			if i >= len(field_names):
				raise ValueError(f'Too many positional arguments: expected {len(field_names)}, got {len(call_node.args)}')

			field_name = field_names[i]
			kwargs[field_name] = self._extract_value_from_ast(arg)

		# Handle keyword arguments
		for keyword in call_node.keywords:
			if keyword.arg is None:
				raise ValueError('**kwargs not supported')

			if keyword.arg in kwargs:
				raise ValueError(f'Duplicate argument: {keyword.arg}')

			kwargs[keyword.arg] = self._extract_value_from_ast(keyword.value)

		return kwargs

	def _extract_value_from_ast(self, node: ast.AST) -> str | int | float:
		"""Extract Python value from AST node."""
		if isinstance(node, ast.Constant):
			return node.value
		else:
			raise ValueError(f'Unsupported argument type: {type(node).__name__}')

	def _get_action_by_name(self, name: str, action_types: list[type[BaseAction]]) -> type[BaseAction] | None:
		"""Find an action type by name from the provided action types list."""
		for action in action_types:
			if action.get_action_name() == name:
				return action
		return None
