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
        self._driver.implicitly_wait(10)

    def _fill_input_by_test_id(self, text: str, test_id: str):
        input = self._driver.find_element(
            By.XPATH, f'//*[@data-test-id="{test_id}"]'
        ).find_element(By.TAG_NAME, "input")
        input.send_keys(text)

    def _click_by_test_id(self, test_id: str):
        button = self._driver.find_element(By.XPATH, f"//*[@data-test-id='{test_id}']")
        button.click()

    def start_process(self, user: str, password: str):
        """各ボードに対しておすすめのピンを追加する"""
        self._login(user, password)
        self._show_saved_contents()

        boards = self._get_board_list()
        n = len(boards)
        LOG.info(f"found {n} boards")
        for board in boards:
            self._add_pin_to_board(board)
        LOG.info(f"successfully updated {n} boards")

    def close(self):
        self._driver.close()

    def _open(self):
        self._driver.get(BASE_URL)
        LOG.info(f"successfully opened {BASE_URL}")

    def _login(self, username: str, password: str):
        self._click_by_test_id("simple-login-button")

        self._fill_input_by_test_id(username, "emailInputField")
        self._fill_input_by_test_id(password, "passwordInputField")

        self._click_by_test_id("registerFormSubmitButton")

        LOG.info(f"logged in. current url: {self._driver.current_url}")

    def _show_saved_contents(self):
        # move to profile
        self._click_by_test_id("header-profile")

        # show saved contents
        self._driver.find_element(By.ID, "_saved-profile-tab").click()

        LOG.info(f"showed saved contents. current url: {self._driver.current_url}")

    def _get_board_list(self):
        boards = self._driver.find_elements(
            By.XPATH, "//*[@data-test-id='pwt-grid-item']"
        )
        result = []
        # 先頭は"すべてのピン"のため無視
        for board in boards[1:]:
            a: WebElement = board.find_element(By.TAG_NAME, "a")
            result.append(a.get_attribute("href"))
        return result

    def _add_pin_to_board(self, board_url: str):
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
        pinter.start_process(args.user, args.password)
    except Exception as e:
        LOG.error(e)
    finally:
        pinter.close()


if __name__ == "__main__":
    main()
