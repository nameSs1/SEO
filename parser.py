from selenium import webdriver
from selenium import common
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from req import Req
from datetime import datetime
from os import path, makedirs


def screen_page(driver, id_request, search_engine):  # В случае ошибки, делает скрин и сохраняет html в errors
    newpath = 'errors'
    if not path.exists(newpath):
        makedirs(newpath)
    file_name = '{0}{1}.'.format(id_request, search_engine)
    driver.save_screenshot(path.abspath('errors/' + str(file_name) + 'png'))
    elem_html = str(driver.page_source)
    with open(path.abspath('errors/' + str(file_name) + 'html'), "w", encoding='utf8') as write_file:
        write_file.write(elem_html)


def ran_pages_google(site_promoted, driver, namber = 0, namber_page = 0):
    """ принимает driver. возвращает позицию в поисковике. листает 10 страниц, если не находит, возврщает 101"""
    if namber_page == 10:
        return 101, False
    # page = driver.find_element_by_id("search")
    page = driver.find_element(By.XPATH, "//*[@id='search']")
    results = page.find_elements(By.XPATH, ".//div[@class='g']")
    for i, result in enumerate(results):
        try:  # xpath_str = "[contains(text(),'{}')]".format(cite_name)
            find_cite = result.find_element_by_xpath('.//cite')
        except:
            continue
        if site_promoted in find_cite.text:
            return namber + 1, find_cite.text
        else:
            namber += 1
    namber_page += 1
    driver.find_element_by_xpath(".//a[@aria-label='Page {0}'][text()='{0}']".format(namber_page + 1)).click()
    return ran_pages_google(site_promoted, driver, namber, namber_page)


def ran_pages_yandex(ins_request, driver, namber = 0, namber_page = 0):
    """ принимает driver. возвращает позицию в поисковике. листает 10 страниц, если не находит, возврщает 101"""
    if namber_page == 10:
        return 101, False
    results = driver.find_elements(By.XPATH, ".//ul/li[@class='serp-item']")  # получаем список результатов
    driver.implicitly_wait(0)
    for i, r in enumerate(results):
        try:
            r.find_element(By.XPATH, ".//div[contains(@class, 'label') and text()='реклама']")  # проверка рекламы
        except common.exceptions.NoSuchElementException:  # Значит не реклама, продолжаем
            find_cite = r.find_element(By.XPATH, ".//a")
            if ins_request.site_promoted in find_cite.get_attribute("href"):
                return namber + 1, find_cite.get_attribute("href")  # возвращаем номер и найденую ссылку
            else:
                namber += 1
        else:
            continue
    namber_page += 1
    try:
        aria_label = driver.find_element_by_xpath(".//div[@aria-label='Страницы']")  # aria-label="Страницы"
        aria_label.find_element_by_xpath(".//a[text()='{0}']".format(namber_page + 1)).click()
    except:
        screen_page(driver, ins_request.id, 'yandex')
    driver.implicitly_wait(0)
    return ran_pages_yandex(ins_request.site_promoted, driver, namber, namber_page)

def get_position(ins_request):
    site_promoted, request_value, id_request = ins_request.site_promoted, ins_request.value_req, ins_request.id
    """принимает название сайта, поисковик, запрос. возвращает позицию"""
    search_engines = {'google': 'https://www.google.by', 'yandex': 'https://yandex.by'}
    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", '127.0.0.1')
    profile.set_preference("network.proxy.socks_port", 9150)
    profile.set_preference("network.proxy.socks_remote_dns", False)
    profile.update_preferences()
    driver = webdriver.Firefox(firefox_profile=profile)
    driver.implicitly_wait(5)
    # Поиск в google
    try:
        driver.get(search_engines['google'])
        page = driver.find_element(By.XPATH, ".//input[@title='Шукаць']")  # Поиск
        page.send_keys(request_value)
        page.send_keys(Keys.RETURN)
        namber_google, url_result_google = ran_pages_google(site_promoted, driver)
    except:
        namber_google, url_result_google = False, False
    # Поиск в yandex
    try:
        driver.get(search_engines['yandex'])
        page = driver.find_element(By.XPATH, ".//*[@id='text']")  # Поиск
        page.send_keys(request_value)
        page.send_keys(Keys.RETURN)
        namber_yandex, url_result_yandex = ran_pages_yandex(ins_request, driver)
    except:
        namber_yandex, url_result_yandex = False, False
    driver.quit()
    return namber_google, url_result_google, namber_yandex, url_result_yandex


def start_parser():
    err = []  # Список id запросов, во время выполнения которых произошли ошибки
    # read_file_name = input('filename: ')
    read_file_name = 'list_requests'
    if 'json' in (read_file_name):
        dicts = Req.read_json(read_file_name)
    else:
        dicts = Req.read_txt(read_file_name)
    time_now = datetime.now(tz=None)
    print("time start {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))
    for d in dicts:
        position = get_position(d)
        if not position[0] or not position[2]:
            err.append(d.id)
        d.position_google = position[0] if position[0] else None
        d.url_result_google = position[1] if position[1] else None
        d.position_yandex = position[2] if position[2] else None
        d.url_result_yandex = position[3] if position[3] else None
    Req.create_json(dicts)
    time_now = datetime.now(tz=None)
    print("time finish {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))
    if err:
        print(err)


if __name__ == "__main__":
    start_parser()
