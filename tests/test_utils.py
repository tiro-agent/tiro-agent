import pytest

from web_agent.utils import check_domain_pattern_match


def test_matches_domain_pattern() -> None:
	assert check_domain_pattern_match('google.com', 'google.com')
	assert check_domain_pattern_match('www.google.com', 'google.com')
	assert check_domain_pattern_match('google.com', 'www.google.com')
	assert check_domain_pattern_match('www.google.com', 'www.google.com')
	assert check_domain_pattern_match('google.com', '*.google.com')
	assert check_domain_pattern_match('www.google.com', '*.google.com')
	assert check_domain_pattern_match('test.maps.google.com', 'test.maps.google.com')
	assert check_domain_pattern_match('test.maps.google.com', '*.maps.google.com')
	assert check_domain_pattern_match('maps.google.com', '*.maps.google.com')

	# shouldraise security errors (value errors)
	with pytest.raises(ValueError):
		check_domain_pattern_match('google.com', '*.com')
	with pytest.raises(ValueError):
		check_domain_pattern_match('maps.google.com', 'maps.*.com')
	with pytest.raises(ValueError):
		check_domain_pattern_match('google.com', '*.*.com')
	with pytest.raises(ValueError):
		check_domain_pattern_match('google.com', '*.com')
	with pytest.raises(ValueError):
		check_domain_pattern_match('google.com', '*com')
	with pytest.raises(ValueError):
		check_domain_pattern_match('google.com', '*e.com')  # this is not a valid pattern
	with pytest.raises(ValueError):
		check_domain_pattern_match('google.com', '*')  # this is not a valid pattern (to allow for all set domains to None)

	# should not match
	assert not check_domain_pattern_match('google.com', 'test.com')
	assert not check_domain_pattern_match('google.com', '*.test.com')
	assert not check_domain_pattern_match('www.google.com', '*.test.com')
