import os
import urllib.parse
import random
import requests
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import re
import time
from selenium.common.exceptions import NoSuchElementException
from PIL import Image
from PyPDF2 import PdfMerger
import io

URl_SITE = "https://comick.io"

# Create and configure the Chrome driver for Selenium
def create_webdriver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add a random User-Agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]
    user_agent = random.choice(user_agents)
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    webdriver_service = Service('/opt/homebrew/bin/chromedriver')  # Update this path if necessary
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return driver

# Function to search for manga using Selenium
def research_manga_comick(manga_name: str) -> dict:
    driver = create_webdriver(headless=True)
    
    url = f"{URl_SITE}/search?q={urllib.parse.quote(manga_name)}"
    driver.get(url)
    
    # Wait for search results to load
    wait = WebDriverWait(driver, 10)
    results = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".w-16.h-28")))
    
    # Extract manga names and URLs
    manga_dict = {
        result.find_element(By.TAG_NAME, "img").get_attribute("alt"): result.find_element(By.TAG_NAME, "a").get_attribute("href")
        for result in results
    }
    
    driver.quit()
    return manga_dict

# Function to get the URL of the first chapter
def url_manga_first_chapter(manga_url: str) -> str:
    driver = create_webdriver(headless=True)
    driver.get(manga_url)
    
    # Wait for the first chapter button to appear
    wait = WebDriverWait(driver, 10)
    button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flex-1.h-12.btn.btn-primary.px-2.py-3.flex.items-center.rounded")))
    
    href = button.get_attribute("href")
    driver.quit()
    
    return href

# Function to fetch image URLs of a chapter
def fetch_image_urls(chapter_url: str, max_retries=3):
    driver = create_webdriver(headless=True)
    driver.get(chapter_url)

    retries = 0
    while retries < max_retries:
        try:
            wait = WebDriverWait(driver, 10)
            images = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))
            image_urls = [img.get_attribute("src") for img in images if "meo." in img.get_attribute("src") or "meo3." in img.get_attribute("src")]
            
            if image_urls:
                driver.quit()
                return image_urls
            
            retries += 1
        except Exception as e:
            print(f"Error fetching images: {e}. Retrying...")
            retries += 1
        finally:
            driver.quit()
    
    return []

# Function to download a single image
def download_image(url, folder_path, filename):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(os.path.join(folder_path, filename), 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image successfully downloaded: {filename}")
        else:
            print(f"Failed to download image: {filename}")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")

# Download images concurrently
def download_images_in_thread(image_urls, title, folder_path):
    with ThreadPoolExecutor() as executor:
        for page, img_url in enumerate(image_urls, 1):
            extension = img_url.split(".")[-1]
            # Use regular expression to find the chapter number
            match = re.search(r'(chapter-\d+(\.\d+)?)', title)
            if match:
                # Extract the chapter string from the match
                chapter_number = match.group(1)
                print(f"Chapter number: {chapter_number}")
            else:
                print("Chapter number not found")
            filename = f"{chapter_number} - {page}.{extension}"
            executor.submit(download_image, img_url, folder_path, filename)
def download_chapters(chapter_url: str, manga_name: str, max_depth=5, current_depth=1, retries=3, delay=5):
    if current_depth > max_depth:
        print(f"Reached maximum depth of {max_depth} chapters.")
        return

    print(f"Downloading Chapter {current_depth} from {chapter_url}")
    
    # Retry logic for downloading images
    for attempt in range(retries):
        try:
            image_urls = fetch_image_urls(chapter_url)
            title = chapter_url.split("/")[-1]  # Assuming title is the last part of the URL

            # Create folder to store images
            folder_path = os.path.join("Data", manga_name)
            os.makedirs(folder_path, exist_ok=True)

            # Start downloading images in a separate thread
            download_thread = threading.Thread(target=download_images_in_thread, args=(image_urls, title, folder_path))
            download_thread.start()
            download_thread.join()  # Ensure the thread finishes before proceeding
            break  # Exit the retry loop if successful
        except Exception as e:
            print(f"Error downloading images on attempt {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed to download images after {retries} attempts.")
                return  # Exit the function if we can't download images
    
    # Retry logic for fetching the next chapter URL
    for attempt in range(retries):
        try:
            driver = create_webdriver(headless=True)
            driver.get(chapter_url)

            # Save the current page's HTML
            try:
                href_next = driver.find_element(By.CSS_SELECTOR, 
                    ".relative.grow-0.w-full.flex.justify-center.h-28.md\\:h-32.xl\\:h-40.px-4.border-r.leading-5.border-gray-600.select-none.text-xl.bg-gray-100.hover\\:bg-gray-200.dark\\:bg-gray-700.dark\\:hover\\:bg-gray-600"
                ).get_attribute("href")
            except NoSuchElementException:
                try: 
                    href_next = driver.find_element(By.CSS_SELECTOR, 
                        ".relative.grow-0.w-8\\/12.flex.justify-center.h-28.md\\:h-32.xl\\:h-40.px-4.border-r.leading-5.border-gray-600.select-none.text-xl.bg-gray-100.hover\\:bg-gray-200.dark\\:bg-gray-700.dark\\:hover\\:bg-gray-600"
                    ).get_attribute("href")
                except NoSuchElementException:
                    href_next = None
            if href_next:
                # Recursively download the next chapter
                download_chapters(href_next, manga_name, max_depth, current_depth + 1, retries, delay)
            else:
                print("No more chapters found.")
            break  # Exit the retry loop if successful
        except Exception as e:
            print(f"Error finding next chapter on attempt {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed to find the next chapter after {retries} attempts.")
                return  # Exit the function if we can't find the next chapter
        finally:
            driver.quit()

def create_pdf_comick(manga_name: str):
    
    # get file list
    file_list = os.listdir(os.path.join(f"Data/{manga_name}"))
    
    file_list.sort(key=extract_chapter_and_page_numbers)
    
    merger = PdfMerger()
    
    for file in file_list:
        image_path = os.path.join("Data", manga_name, file)
        
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image file {image_path} does not exist.")

        image = Image.open(image_path)
        
        # Convert image to PDF
        pdf_bytes = io.BytesIO()
        image.save(pdf_bytes, format='PDF')
        pdf_bytes.seek(0)
        
        # Add PDF page to merger
        merger.append(pdf_bytes)

    # Save the merged PDF
    output_dir = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader", manga_name)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(os.path.join(output_dir,f"{manga_name}.pdf"), "wb") as output_file:
        merger.write(output_file)

    merger.close()
    
def extract_chapter_and_page_numbers(filename):
    """
    Extract chapter and page numbers from the filename.
    Expected filename format: 'chapter-<number> - <page>.<extension>'
    """
    chapter_match = re.search(r'chapter-(\d+(\.\d+)?)', filename, re.IGNORECASE)
    page_match = re.search(r'(\d+)\.\w+$', filename)  # Extracts the page number before the file extension
    
    if chapter_match and page_match:
        chapter_number = float(chapter_match.group(1)) if '.' in chapter_match.group(1) else int(chapter_match.group(1))
        page_number = int(page_match.group(1))
        return chapter_number, page_number
    
    # If no match, return very large numbers to ensure these files are sorted last
    return float('inf'), float('inf')


# Main function to execute the entire process
def example_main(manga_name: str, max_depth=5):
    manga_data = research_manga_comick(manga_name)
    print(manga_data)

    if manga_data:
        first_manga_name = list(manga_data.keys())[0]
        manga_url = manga_data[first_manga_name]

        # Get the first chapter URL and download chapters
        first_chapter_url = url_manga_first_chapter(manga_url)
        if first_chapter_url:
            download_chapters(first_chapter_url, first_manga_name, max_depth)


if __name__ == "__main__":
    example_main("uzumaki ito", max_depth=3)