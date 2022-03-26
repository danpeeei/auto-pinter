import logging
from argparse import ArgumentParser

try:
    import chromedriver_binary  # noqa: F401
except Exception:
    pass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://www.pinterest.jp"
LOG = logging.getLogger(__name__)


class AutoPinter:
    def __init__(self, debug: bool = True) -> None:
        options = Options()
        if not debug:
            options.add_argument("--headless")
        self._driver = webdriver.Chrome(options=options)
        self._driver.get(BASE_URL)
        self._driver.implicitly_wait(10)

    def fill_input_by_test_id(self, text: str, test_id: str):
        input = self._driver.find_element(
            By.XPATH, f'//*[@data-test-id="{test_id}"]'
        ).find_element(By.TAG_NAME, "input")
        input.send_keys(text)

    def click_by_test_id(self, test_id: str):
        button = self._driver.find_element(By.XPATH, f"//*[@data-test-id='{test_id}']")
        button.click()

    def start(self, user: str, password: str):
        self.login(user, password)
        LOG.info("successfully logged in")
        boards = self.get_board_list()
        n = len(boards)
        LOG.info(f"found {n} boards")
        for board in boards:
            self.add_pin_to_board(board)
        LOG.info(f"successfully updated {n} boards")

    def close(self):
        self._driver.close()

    def login(self, username: str, password: str):
        """ログイン"""
        self.click_by_test_id("simple-login-button")

        self.fill_input_by_test_id(username, "emailInputField")
        self.fill_input_by_test_id(password, "passwordInputField")

        self.click_by_test_id("registerFormSubmitButton")

        # move to profile
        self.click_by_test_id("header-profile")

        # show saved contents
        self._driver.find_element(By.ID, "_saved-profile-tab").click()

    def get_board_list(self):
        boards = self._driver.find_elements(
            By.XPATH, "//*[@data-test-id='pwt-grid-item']"
        )
        result = []
        # 先頭は"すべてのピン"のため無視
        for board in boards[1:]:
            a: WebElement = board.find_element(By.TAG_NAME, "a")
            result.append(a.get_attribute("href"))
        return result

    def add_pin_to_board(self, board_url: str):
        # "おすすめのアイデア"を新規タブで開く
        try:
            url = board_url + "_tools/more-ideas/?ideas_referrer=2"
            self._driver.execute_script("window.open(arguments[0], 'newtab')", url)
            self._driver.switch_to.window(self._driver.window_handles[1])

            # 先頭のピンをボードに追加
            pin = self._driver.find_element(By.XPATH, "//*[@data-test-id='pin']")
            save = pin.find_element(By.XPATH, "//div[@aria-label='保存']")
            save.click()
        except Exception as e:
            LOG.error(e)
        finally:
            # タブを閉じる
            self._driver.close()
            self._driver.switch_to.window(self._driver.window_handles[0])

        LOG.info(f"{board_url}: ok")


def main():
    parser = ArgumentParser("auto-pinter")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-p", "--password", required=True)
    args = parser.parse_args()

    pinter = AutoPinter(args.debug)
    try:
        pinter.start(args.user, args.password)
    except Exception as e:
        LOG.error(e)
    finally:
        pinter.close()


if __name__ == "__main__":
    main()
