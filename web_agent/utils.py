import re


def matches_domain_pattern(domain: str, pattern: str) -> bool:
	"""Check if a domain matches a pattern with wildcards."""
	# Convert wildcard pattern to regex
	pattern = pattern.replace('.', r'\.').replace('*', '.*')
	return bool(re.match(f'^{pattern}$', domain))
