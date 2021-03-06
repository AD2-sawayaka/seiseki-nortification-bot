import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import psycopg2
import os


def get_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)


# すでに登録されている名前であればTrue
def isResistered(name, cur):
    query = "SELECT subject_name FROM seiseki WHERE subject_name = '" + name +  "'"
    cur.execute(query)
    tmp = str()
    for row in cur:
        tmp = row
    if tmp:
        return True
    return False


def run():
    load_dotenv()
    MY_ID = os.environ["MY_ID"]
    MY_PASS = os.environ["MY_PASS"]
    # Seleniumをあらゆる環境で起動させるChromeオプション
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--proxy-server="direct://"')
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--start-maximized')
    # options.add_argument('--headless')  # ※ヘッドレスモードを使用する場合、コメントアウトを外す

    #
    # Chromeドライバーの起動
    #
    driver = webdriver.Chrome(chrome_options=options)

    driver.implicitly_wait(10)  # 秒

    #
    #
    # クローリング/スクレイピング
    #
    #

    # 学情にアクセスする
    url = os.environ['URL']
    driver.get(url)

    # トップページでログインボタンを押す
    selector = '#left_container > div.left-module-top.bg_color > div > div > a'
    element = driver.find_element_by_css_selector(selector)
    driver.execute_script('arguments[0].click();', element)

    # username
    selector = '#username'
    element = driver.find_element_by_css_selector(selector)
    element.send_keys(MY_ID)

    # password
    selector = '#password'
    element = driver.find_element_by_css_selector(selector)
    element.send_keys(MY_PASS)

    # Loginボタン
    selector = 'body > div > div > div > div > form > div:nth-child(3) > button'
    element = driver.find_element_by_css_selector(selector)
    driver.execute_script('arguments[0].click();', element)

    # 教務システム
    selector = '#home_systemCooperationLink > div.left-module.mt15 > div > ul > li:nth-child(1) > a'
    element = driver.find_element_by_css_selector(selector)
    driver.execute_script('arguments[0].click();', element)

    # ウィンドウハンドルを取得する
    handle_array = driver.window_handles
    # 一番最後のdriverに切り替える
    driver.switch_to.window(handle_array[-1])


    # 成績情報の参照
    selector = 'body > table:nth-child(4) > tbody > tr > td:nth-child(2) > table > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(1) > td:nth-child(2) > a'
    element = driver.find_element_by_css_selector(selector)
    driver.execute_script('arguments[0].click();', element)

    # ウィンドウハンドルを取得する
    handle_array = driver.window_handles
    # 一番最後のdriverに切り替える
    driver.switch_to.window(handle_array[-1])

    # tableを取得
    html = driver.page_source
    bsObj = BeautifulSoup(html, "html.parser")

    table = bsObj.findAll('table')[-3]
    rows = table.select("tr")

    # connectionとcursor
    conn = get_connection()
    cur = conn.cursor()

    # 科目名、担当教員名、科目区分、必修選択区分、単位、評価、得点、科目GP、取得年度、報告日、 試験種別
    flag = False
    update = False
    updateList = list()

    for row in rows:
        tmp = list()
        for cell in row.findAll(['td', 'th']):
            if cell.get_text(strip=True) != '':
                text = "'" + cell.get_text(strip=True) + "'"
                text = ''.join(text.split())
                tmp.append(text)
                # print(cell.get_text(strip=True))
        tmp_name = tmp[0].replace("'", "")
        tmp_str = tmp[0].replace("'", "") + " " + tmp[5].replace("'", "") + " " + tmp[6].replace("'", "")
        # print(tmp_name)
        tmp = ', '.join(tmp)
        if (flag):
            if isResistered(tmp_name, cur):
                print('あるよ')
            else:
                update = True
                print('ないから登録するよ')
                query = 'INSERT INTO seiseki VALUES (' + tmp + ')'
                updateList.append(tmp_str)
                cur.execute(query)
                conn.commit()
        else:
            flag = True
    # close
    cur.close()
    conn.close()

    time.sleep(5)
    driver.quit()
    return update, updateList


if __name__ == '__main__':
    run()
