import json
import time
import traceback
from typing import Callable

from playwright.sync_api import sync_playwright, Page, Browser, Playwright





def get_browser(playwright: Playwright) -> Browser:

    # Launch a headless browser
    browser = playwright.firefox.launch(args=["--disable-http2"], headless=True)  # Set to True if you don't want to see the browser
    browser.new_context(user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"))

    return browser


def get_browser_page(browser: Browser) ->  Page:

    page = browser.new_page()

    return page


def navigate_to_fybra_device_details_page(page: Page, env_data)-> bool:
    
    try:

        # Go to the login page
        page.goto("https://fybra.app/auth/login")

        # Fill in the login form and submit
        page.fill("#input-email", env_data["email"])
        page.fill("#input-password", env_data["password"])
        page.click("form button")

        # Wait for the main page to load and click the Devices menu item
        page.wait_for_selector(".menu-items")
        
        page.click(".menu-items a[href='/home-devices']")

        # Wait for the devices page to load, then click the device detail button
        page.wait_for_selector("ngx-device-detail-button")
        page.click("ngx-device-detail-button")

        # Wait for the popup dialog to appear
        page.wait_for_selector("ngx-new-dev-dialog")
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def navigate_to_accuweather_aq_page(page: Page)-> bool:
    try:
        page.goto("https://www.accuweather.com/ro/ro/bucharest/1-287430_18_al/air-quality-index/1-287430_18_al")
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def read_fybra_device_values(loaded_page: Page) -> list[str] | None:
    values: list[str] = []
    
    try:
        rows_locator = loaded_page.locator("ngx-new-dev-dialog .row")
        if rows_locator.count() > 1:
            second_row_locator = rows_locator.nth(1)
            divs_locator = second_row_locator.locator("div > div")

            for i in range(divs_locator.count()):
                # Retrieve fresh text for each div in the second row
                values.append(divs_locator.nth(i).inner_text().strip())
    except:
        return None

    return values


def read_accuweather_aq_values(loaded_page: Page) -> list[list[str]] | None:
    values: list[list[str]] = []
    
    try:
        pollutants_containers = loaded_page.query_selector_all("#pollutants > .air-quality-pollutant")
        
        for pollutants_container in pollutants_containers:
            label = pollutants_container.query_selector_all("h3 > .display-type")[0].inner_text().strip()
            index = pollutants_container.query_selector_all(".pollutant-index")[0].inner_text().strip()
            concentration = pollutants_container.query_selector_all(".pollutant-concentration")[0].inner_text().strip()
            values.append([label, index, concentration])
    except:
        return None

    return values


def on_read(fybra_device_values: list[str], aq_values: list[list[str]]):
    print(fybra_device_values),
    print(aq_values)


def connect_and_read(tick_interval_seconds: int, nth_tick_to_refresh_fybra: int, nth_tick_to_refresh_aq: int, callback: Callable[[list[str], list[list[str]]], None]):
    try:
        with open('environment/environment.json', 'r') as env_file:
            env_data = json.load(env_file)
            with sync_playwright() as p:
                browser = get_browser(p)
                fybra_page = get_browser_page(browser)
                accuweather_page = get_browser_page(browser)
                successfully_navigated_to_accuweather = navigate_to_accuweather_aq_page(accuweather_page)
                successfully_navigated_to_fybra = navigate_to_fybra_device_details_page(fybra_page, env_data)
                
                nth_tick_fybra = 0
                nth_tick_aq = 0
                is_first_iteration = True
                fybra_values=[]
                accuweather_aq_values=[]
                while True:
                    
                    nth_tick_fybra = nth_tick_fybra + 1
                    nth_tick_aq = nth_tick_aq + 1
                    
                    if(successfully_navigated_to_fybra == False):
                        successfully_navigated_to_fybra = navigate_to_fybra_device_details_page(fybra_page, env_data)
                    
                    
                    if nth_tick_fybra >= nth_tick_to_refresh_fybra or is_first_iteration:
                        # do not reload page and just read again from the same page as the values are dynamic
                        fybra_values = read_fybra_device_values(fybra_page)
                        nth_tick_fybra = 0
                    
                    if nth_tick_aq >= nth_tick_to_refresh_aq or is_first_iteration or successfully_navigated_to_accuweather == False:
                        # refresh accuweather page as the values are not dynamic
                        successfully_navigated_to_accuweather = navigate_to_accuweather_aq_page(accuweather_page)
                        if(successfully_navigated_to_accuweather == False):
                            accuweather_aq_values = None
                        else:
                            accuweather_aq_values = read_accuweather_aq_values(accuweather_page)
                        nth_tick_aq = 0
                        
                    is_first_iteration = False

                    callback(fybra_values, accuweather_aq_values)

                    time.sleep(tick_interval_seconds)

    except Exception as e:
        print("\nGeneric Error.\n")
        #This line opens a log file
        with open("getaqdata_log.txt", "w") as log:
            traceback.print_exc(file=log)
            traceback.print_exc()
        return None


if __name__ == "__main__":
    connect_and_read(60,1,10, on_read)
