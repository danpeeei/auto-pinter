import logging
from argparse import ArgumentParser

import chromedriver_binary  # noqa: F401
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://www.pinterest.jp"
driver = webdriver.Chrome()
driver.get(BASE_URL)
driver.implicitly_wait(10)

board_tab = None


LOG = logging.getLogger(__name__)


def fill_input_by_test_id(text: str, test_id: str):
    input = driver.find_element(
        By.XPATH, f'//*[@data-test-id="{test_id}"]'
    ).find_element(By.TAG_NAME, "input")
    input.send_keys(text)


def click_by_test_id(test_id: str):
    button = driver.find_element(By.XPATH, f"//*[@data-test-id='{test_id}']")
    button.click()


def login(username: str, password: str):
    """ログイン"""
    click_by_test_id("simple-login-button")

    fill_input_by_test_id(username, "emailInputField")
    fill_input_by_test_id(password, "passwordInputField")

    click_by_test_id("registerFormSubmitButton")

    # move to profile
    click_by_test_id("header-profile")

    # show saved contents
    driver.find_element(By.ID, "_saved-profile-tab").click()


def get_board_list():
    boards = driver.find_elements(By.XPATH, "//*[@data-test-id='pwt-grid-item']")
    result = []
    # 先頭は"すべてのピン"のため無視
    for board in boards[1:]:
        a: WebElement = board.find_element(By.TAG_NAME, "a")
        href = a.get_attribute("href")
        result.append(href)
    return result


def add_pin_to_board(board_url: str):
    # "おすすめのアイデア"を新規タブで開く
    try:
        url = board_url + "_tools/more-ideas/?ideas_referrer=2"
        driver.execute_script("window.open(arguments[0], 'newtab')", url)
        driver.switch_to.window(driver.window_handles[1])

        # 先頭のピンをボードに追加
        pin = driver.find_element(By.XPATH, "//*[@data-test-id='pin']")
        save = pin.find_element(By.XPATH, "//div[@aria-label='保存']")
        save.click()
    except Exception as e:
        LOG.error(e)
    finally:
        # タブを閉じる
        driver.close()
        driver.switch_to.window(driver.window_handles[0])


def main():
    parser = ArgumentParser("auto-pinter")
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-p", "--password", required=True)
    args = parser.parse_args()

    login(args.user, args.password)
    boards = get_board_list()
    for board in boards:
        add_pin_to_board(board)
    LOG.info(f"updated {len(boards)} boards ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    driver.close()
