import os
import time

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from twocaptcha import TwoCaptcha

load_dotenv()
solver = TwoCaptcha(os.getenv('2CAPTCHA_API_KEY'))


def main():
	with sync_playwright() as p:
		browser = p.chromium.launch_persistent_context(headless=False, channel='chrome', user_data_dir='./.browser_user_data')
		page = browser.new_page()
		stealth_sync(page)
		page.goto('https://medium.com/')
		# wait until the page is loaded
		page.wait_for_load_state('networkidle')
		page.screenshot(path='example-chromium.png')
		# wait for 10 seconds
		time.sleep(10)
		browser.close()


if __name__ == '__main__':
	main()
