import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip(reason='only for example')
def test_has_title(page: Page) -> None:
	page.goto('https://playwright.dev/')

	# Expect a title "to contain" a substring.
	expect(page).to_have_title(re.compile('Playwright'))


@pytest.mark.skip(reason='only for example')
def test_get_started_link(page: Page) -> None:
	page.goto('https://playwright.dev/')

	# Click the get started link.
	page.get_by_role('link', name='Get started').click()

	# Expects page to have a heading with the name of Installation.
	expect(page.get_by_role('heading', name='Installation')).to_be_visible()
