from flask import Flask, Response, request
from flask_cors import CORS
import threading
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import random, time, sys
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import OperationFailure
from cred import MUSER, MPASS, MCLUSTER

from datetime import datetime, date

app = Flask(__name__)
CORS(app)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
PROXY = "us-ca.proxymesh.com:31280"
CREDS = {
    "email": "yalohef558@evnft.com",
    "username": "RamLaxman517452",
    "password": "Welcome@2024"
}

class StatusLogger():
    def __init__(self):
        pass

    def emit(self, event, data):
        return f"event: {event}\ndata: {data}\n\n"
    
    def log(self, data):
        return self.emit("log", data)
    
    def topics(self, data):
        return self.emit("topics", data)
    
    def trendingTime(self, data):
        return self.emit("trendingTime", data)
    
    def ip(self, data):
        return self.emit("ip_address", data)

driver = None
wait = None
driver_lock = threading.Lock()

LOGIN_INPUT = 'input[autocomplete="username"]'
PASSWORD_INPUT = 'input[autocomplete="current-password"]'

def sleep_rand():
    time.sleep(random.randint(1, 3))

logger = StatusLogger()

def getMongoClient():
    uri = f"mongodb+srv://{MUSER}:{MPASS}@{MCLUSTER}/?retryWrites=true&w=majority&appName=TweetData"

    client = MongoClient(uri, server_api=ServerApi('1'))

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(e)
        return False
    
def saveData(data):
    client = getMongoClient()
    if not client:
        return False
    
    db = client.topics
    collection = db["trending"]
    try:
        result = collection.insert_one(data)
    except OperationFailure:
        print("An authentication error was received. Are you sure your database user is authorized to perform write operations?")
        sys.exit(1)
    else:
        inserted_count = len(result.inserted_ids)
        print("I inserted %x documents." %(inserted_count))
        yield logger.log("Data Saved")

class TrendingTopics():
    def __init__(self, username, email, password):
        self.ip = None
        self.username = username
        self.email = email
        self.password = password

        self.result = None

    def setIpAddress(self, ip):
        self.ip = ip
    
    def setTopics(self, topics):
        for i, topic in enumerate(topics):
            self.result[f"nameoftrend{i}"] = topic
    
    def getResult(self):
        return {
            "_id": {self.username: self.password},
            **self.result
        }

def twitterBot(use_proxy, headless):
    yield logger.log("-- Booting up --")
    global driver, wait

    try:
        with driver_lock:
            if driver:
                driver.quit()

            options = Options()
            options.add_argument(f'user-agent={USER_AGENT}')
            if use_proxy:
                yield logger.log(f"[Using Proxy]: {PROXY}")
                options.add_argument('--proxy-server=%s' % PROXY)

            if headless:
                yield logger.log(f"Running Chrome in headless mode")
                options.addArguments("--headless=new")
            
            data = TrendingTopics(**CREDS)

            yield logger.log("Opening Chrome Browser")
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 50)

        yield logger.log("Retrieving IP Address")
        driver.get("https://api.ipify.org/")
        ip_address = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text

        yield logger.ip(f"{ip_address}")

        data.setIpAddress(ip_address)

        today = date.today()
        c = datetime.now()

        yield logger.trendingTime(f"{today.strftime('%d-%m-%Y')} {c.strftime('%H:%M:%S')}")
        driver.get("https://x.com")

        yield logger.log("Navigating to login page of X")
        # Something went wrong, but don’t fret — it’s not your fault
        driver.get("https://x.com/login")


        yield logger.log("Attempting to login into X")
        login_input_fill = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_INPUT)))
        login_input_fill.send_keys(CREDS["email"])
        
        yield logger.log("[+] Username field filled")
        sleep_rand()

        next_btn = next((btn for btn in driver.find_elements(By.CSS_SELECTOR, "button[role='button']") 
                        if btn.find_element(By.CSS_SELECTOR, "span").text.lower() == "next"), None)
        if next_btn:
            next_btn.click()
        sleep_rand()

        while True:
            try:
                yield logger.log("[?] Checking for unusual login activity page by X\n")

                if wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "unusual login activity")):
                    yield logger.log("[+] Resolving unusual activity page")

                    email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')))
                    email_input.send_keys(CREDS["username"])
                    email_input.send_keys(Keys.RETURN)
                    
                    time.sleep(5)

                    break
            except TimeoutException:
                break
            
        password_input_fill = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PASSWORD_INPUT)))
        password_input_fill.send_keys(CREDS["password"])
        password_input_fill.send_keys(Keys.ENTER)
        
        yield logger.log("[+] Password field filled")
        sleep_rand()

        # try:
        #     if wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Help us keep your account safe")):
        #         pass
        # except TimeoutException:
        #         pass
         

        yield logger.log("Logged in successfully!")
        driver.implicitly_wait(0.5)

        yield logger.log("Waiting for homepage to load")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Timeline: Trending now"]')))

        # yield logger.log("Navigating to trending tweet page")
        # driver.get("https://x.com/explore/tabs/trending")
        
        trendings = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="trend"]')))
        yield logger.log("Fetching trending topics")
        tt = []
        for trending in trendings[0:5]:
            topic = trending.find_element(By.CSS_SELECTOR, "div:nth-child(2)").text
            tt.append(topic)
            yield logger.topics(topic)

        data.setTopics(tt)
    except:
        # yield logger.log("[x] Something went wrong")
        driver.quit()
    finally:
        yield logger.log("[=] Closing Browser")
        driver.quit()


@app.route('/tweet-trending')
def get_trending_tweets():
    use_proxy = request.args.get("use_proxy") == "true"
    headless = request.args.get("headless") == "true"
    print(use_proxy, headless)
    return Response(twitterBot(use_proxy = use_proxy, headless=headless), content_type='text/event-stream')


def start_flask():
    app.run(debug=True, threaded=True)

if __name__ == '__main__':
    start_flask()
