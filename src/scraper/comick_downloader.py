import urllib.parse
import bs4
import cloudscraper
import time
import urllib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.support import expected_conditions as EC
import random

URl_SITE = "https://comick.io"

def research_manga(manga_name: str) -> dict:
    
    url = f"{URl_SITE}/search?q={urllib.parse.quote(manga_name)}"
    
    # Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # make the smallest window possible
    chrome_options.add_argument("--window-size=0,1")
    #put it int the top left corner
    chrome_options.add_argument("--window-position=0,0")
    
    #make it invisible
    
    webdriver_service = Service('/opt/homebrew/bin/chromedriver')  # Update this path

    # Initialize Chrome WebDriver with the headless options
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    # Open the URL
    driver.get(url)

    # Use WebDriverWait to wait until the elements are available
    wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds
    results = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".w-16.h-28")))

    # Get the first result
    img = results[0].find_element(By.TAG_NAME, "img")
    print(img.get_attribute("src"))
    
    href = results[0].find_element(By.TAG_NAME, "a").get_attribute("href")
    print(href)
  
    #dict of manga name and url
    manga_dict = {result.find_element(By.TAG_NAME, "img").get_attribute("alt"): result.find_element(By.TAG_NAME, "a").get_attribute("href") for result in results}
    
    return manga_dict


def download_manga_volumes(manga_url:str, manga_name: str) -> None:
    
    retries = 5 
    

    
    scraper = cloudscraper.create_scraper()
    success = False
    i = 1
    
    while True:
        url = manga_url + f"/en/volume-{i}"
        # replace the url to the correct one
        url = url.replace("https://www.mangareader.to","https://www.mangareader.to/read")
        
        success = False
        for attempt in range(retries):
            try:
                response = scraper.get(url)

                if response.status_code == 520:
                    time.sleep(5)  # wait before retrying
                    # Debugging: save the HTML response to file if needed
                    with open(f"{manga_name}_error_download_{attempt+1}.html", "w") as f:
                        f.write(soup.prettify())
                    continue  # retry if 520 error
                if response.status_code == 404:
                    return
                
                soup = bs4.BeautifulSoup(response.text, "html.parser")

                
                with open(f"{manga_name}_debug_download_{attempt+1}.html", "w") as f:
                        f.write(soup.prettify())
                
                i = i + 1
                
                success = True
            except Exception as e:
                print(f"Error on attempt {attempt+1}: {e}")
                time.sleep(5)  # wait before retrying
        
        if not success:
            print(f"Failed to retrieve manga after {retries} attempts: {url}")
            return {}
        


def fetch_image_urls(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
 # Add a random User-Agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        # Add more user agents if needed
    ]
    user_agent = random.choice(user_agents)
    chrome_options.add_argument(f"user-agent={user_agent}")

    #
    # Specify the path to the ChromeDriver executable
    webdriver_service = Service('/opt/homebrew/bin/chromedriver')  # Update this path

    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(url)


    # Wait for the page to load completely
    time.sleep(5)

    # get all src of img tag where url is like meo. or meo3.
    image_urls = []
    img_tags = driver.find_elements(By.TAG_NAME, "img")
    for img_tag in img_tags:
        src = img_tag.get_attribute("src")
        if "meo." in src or "meo3." in src:
            image_urls.append(src)
     
    driver.quit()

    return image_urls

 



# Example usage
manga_data = research_manga("slam dunk")
print (manga_data)

#

# ---- METODO PER RICERCARE MANGA ------

#select the first manga_dict in the dict
manga_name = list(manga_data.keys())[0]
manga_url = manga_data[manga_name]

# ----- METODO PER RINTRACCIARE URL CAPITOLI --------

# ----- METODO PER SCARICARE CAPITOLO AVENDO URL CAPITOLO--------
# url = "https://comick.io/comic/real/jKQO4-chapter-1-en"
# image_urls = fetch_image_urls(url)
# for img_url in image_urls:
#     print(img_url)



