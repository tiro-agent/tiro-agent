def check_domain_pattern_match(domain: str, pattern: str) -> bool:
	"""
	Checks if a domain string matches a given pattern string with specific wildcard rules.

	Args:
	domain: The domain string to check.
	pattern: The pattern string.

	Returns:
	True if the domain matches the pattern, False otherwise.

	Raises:
	ValueError: If the pattern is invalid according to the security rules.
	"""
	# Rule 1: Wildcard '*' is only allowed at the beginning of the pattern.
	if '*' in pattern[1:]:
		raise ValueError("For security reasons, wildcard '*' is only allowed at the beginning of the pattern.")

	if pattern.startswith('*'):
		# Rule 2: If the pattern starts with '*', it must be followed by a dot.
		if not pattern.startswith('*.'):
			raise ValueError("For security reasons, if the pattern starts with '*', it must be followed by a dot.")

		suffix_pattern = pattern[2:]

		# Rule 3: If the pattern starts with '*.', there still must be a domain and an ending (e.g., 'domain.ending').
		if '.' not in suffix_pattern:
			raise ValueError("For security reasons, the pattern must contain a domain and an ending (e.g., 'domain.ending').")

		# If the domain ends with the suffix_pattern, it's a match.
		return domain.endswith(suffix_pattern)
	else:
		# Rule 4: Pattern must contain a domain and an ending (e.g., 'domain.ending').
		if '.' not in pattern:
			raise ValueError("For security reasons, the pattern must contain a domain and an ending (e.g., 'domain.ending').")

		# Rule 5: If the domain starts with 'www.' and the pattern doesn't, it's still a match.
		if domain.startswith('www.') and not pattern.startswith('www.'):
			domain = domain[4:]

		# Rule 6: If the pattern starts with 'www.' and the domain doesn't, it's still a match.
		if not domain.startswith('www.') and pattern.startswith('www.'):
			domain = 'www.' + domain

		# Rule 7: If no wildcard, then it must be an exact match.
		return domain == pattern
