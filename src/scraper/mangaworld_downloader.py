import sys
import requests
import bs4
import os
import subprocess
import re
import shutil
import threading
from PIL import Image
from PyPDF2 import PdfMerger
import io
import img2pdf
from typing import Dict
import cloudscraper
import time


RESEARCH_STRING = "https://www.mangaworld.so/archive?keyword="

CHAPTERS_STRING = "?style=pages"

def natural_sort_key(s):
    """Sort strings in a natural order."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} [{bar}] {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def research_manga(manga: str) -> dict[str, str]:
    """
    Function that take a manga name and return 
    the dictionary of all results

    Args:
        manga (str): string of the researched manga

    Returns:
        dict[str, str]: dictionary of manga and their link
    """
    page = requests.get(RESEARCH_STRING + manga)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    job_all = results.find_all("a", class_="thumb position-relative")

    manga_dict = {job.__str__().split(r'"')[5]: job.__str__().split(r'"')[
        3] for job in job_all}

    return manga_dict

def research_thumbnails() -> Dict[str, str]:
    """
    Function that fetches the top manga from the Jikan API, sorts them by score,
    and returns a dictionary of the top 5 manga titles and their thumbnail links.

    Returns:
        dict[str, str]: Dictionary with manga titles as keys and their thumbnail image URLs as values.
    """
    
    # URL for fetching top manga
    url = "https://api.jikan.moe/v4/top/manga"

    # Parameters for the API request
    params = {
        "page": 1,  # Specify page number
        "type": "manga",  # Type of the top list
        "order_by": "published"  # This might need to be adjusted depending on available fields
    }
    
    # Make the API request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        top_manga = response.json()
    else:
        print("Failed to retrieve data:", response.status_code)
        return {}
    
    # Extract the manga list
    manga_list = top_manga.get('data', [])

    # Sort manga by score in descending order
    sorted_manga = sorted(manga_list, key=lambda x: x.get('score', 0), reverse=True)
    
    # Get the top 5 manga and their thumbnails
    manga_dict = {
        manga['title']: manga['images']['webp']['large_image_url']
        for manga in sorted_manga[:100]
    }
    
    return manga_dict


def manga_with_volumes_links(job_all: bs4.element.ResultSet) -> dict[str, list[str]]:
    """Return a dictionary with number of volumes and all the links for their chapters, for mangas that have volumes division

    Args:
        job_all (bs4.element.ResultSet): Each element of the volume to parse

    Returns:
        dict[str, list[str]]: dictionary with keys: volume_number and values:list to their chapter links
    """
    vol_chap_dict = {}

    for num_vol, vol in enumerate(job_all):
        for chap in vol.find_all("a", class_="chap"):
            key = f"Volume{num_vol}"
            if key not in vol_chap_dict.keys():
                vol_chap_dict[key] = []
            vol_chap_dict[key].append(chap.__str__().split(r'"')[3])

    for volume, chap_list in vol_chap_dict.items():
        tmp = chap_list[::-1]
        vol_chap_dict[volume] = tmp

    return vol_chap_dict


def manga_with_chapters_links(job_all: bs4.element.ResultSet) -> dict[str, list[str]]:
    """Return a dictionary with 1 volume and all the links for it chapters, for mangas that doesn't have volumes but only chapters

    Args:
        job_all (bs4.element.ResultSet): Each element of the volume to parse (aka all chapters in this case)

    Returns:
        dict[str, list[str]]: dictionary with keys: dictionary with 1 key (Volume0) and a links to it chapters
    """
    vol_chap_dict = {}
    vol_chap_dict["Volume0"] = []

    for _, vol in enumerate(job_all):
        for chap in vol.find_all("a", class_="chap"):
            vol_chap_dict["Volume0"].append(
                chap.__str__().split(r'"')[3].split("?")[0])

    return vol_chap_dict


def volumes_with_chapter_link(manga_url: str) -> dict[str, list[str]]:
    """
    Function that take a manga url and return a
    dictionary with all volumes and link of their chapters

    Args:
        manga_url (str): String of a manga url

    Returns:
        dict[str, list[str]]: dictionary with in key a string with volume name, and value a list with all the links of every chapters in volumes
    """
    page = requests.get(manga_url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    job_all = results.find_all("div", class_="volume-element pl-2")[::-1]

    # se un manga non e' diviso in volumi, ma contiene solo capitoli
    if (len(job_all) == 0):
        job_all = results.find_all("div", class_="chapter pl-2")[::-1]
        return manga_with_chapters_links(job_all)
    else:
        return manga_with_volumes_links(job_all)


def print_manga(manga_dict: dict[str, str]):
    """Clear the screen and print all mangas available

    Args:
        manga_dict (dict[str, str]): Mangas researched
    """
    _ = subprocess.call('clear' if os.name == 'posix' else 'cls')

    for index, manga in enumerate(manga_dict.keys()):
        print(f"{index}-{manga}")
    print("\n")


def choose_manga(manga_dict: dict[str, str]) -> str:
    """Simple TUI for select a manga to download

    Args:
        manga_dict (dict[str, str]): Mangas researched

    Returns:
        str: Manga selected
    """
    while True:
        print_manga(manga_dict)
        selected_manga: str = input(
            "Insert the number of the manga do you want to download: ")

        if selected_manga.isdigit() and int(selected_manga) >= 0 and int(selected_manga) < len(manga_dict.keys()):
            return list(manga_dict.keys())[int(selected_manga)]


def number_of_images_in_chapter(chapter_url: str) -> int:
    """Return the number of images in the chapter linked by the chapter url

    Args:
        chapter_url (str): A chapter url

    Returns:
        int: Number of images in chapters
    """
    page = page = requests.get(chapter_url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    job = results.find(
        "select", class_="page custom-select").find("option").__str__()

    number_of_images = job.split("/")[1].split("<")[0]

    return number_of_images

def download_image(image_url: str, vol_index: str, chap_index: str, image_index: str, selected_manga: str, retries=3) -> None:
    """Download an image and save it to a folder (Data/{selected_manga}/{vol_index}/{chap_index}_{image_index}.jpg)

    Args:
        image_url (str): URL to download the image
        vol_index (str): Volume associated with that image
        chap_index (str): Chapter index in this volume
        image_index (str): Positional number of this image in a specific chapter
        selected_manga (str): Manga selected
        retries (int): Number of retry attempts
    """
    
    scraper = cloudscraper.create_scraper()
    success = False
    
    for attempt in range(retries):
        try:
            response = scraper.get(image_url)

            if response.status_code == 520:
                time.sleep(5)  # wait before retrying
                continue  # retry if 520 error
            
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            results = soup.find("body")

            if response.status_code != 200:
                with open(f"{selected_manga}_error_{attempt+1}.html", "w") as f:
                    f.write(soup.prettify())
                continue  # retry if response is not OK

            image_link = results.find(
                "div", class_="col-12 text-center position-relative")
            image_link = image_link.find("img", class_="img-fluid").get("src")

            image = requests.get(image_link, stream=True)
            if image.status_code == 200:
                image.raw.decode_content = True
                os.makedirs(os.path.join(os.getcwd(),"Data", selected_manga, str(vol_index)), exist_ok=True)
                with open(os.path.join(os.getcwd(),"Data", selected_manga, str(vol_index), f"{chap_index}_{image_index}.jpg"), "wb") as f:
                    shutil.copyfileobj(image.raw, f)
            success = True
            break  # exit retry loop on success
        except Exception:
            time.sleep(5)  # wait before retrying
    
    if not success:
        print(f"Failed to download image after {retries} attempts: {image_url}")

def download_chapter_images(chapter_url: str, vol_index: str, chap_index: str, selected_manga: str, number_of_images: int) -> None:
    """Download all images contained in a chapter and save it (see download_image function)

    Args:
        chapter_url (str): url associated with a chapter
        vol_index (str): volume number associated with this chapter
        chap_index (str): chapter index in this volume
        selected_manga (str): manga selected
        number_of_images (int): number of images contained this chapter
    """
    threads = []

    for i in range(1, int(number_of_images) + 1):
        url: str = chapter_url + "/" + str(i) + CHAPTERS_STRING
        threads.append(threading.Thread(target=download_image, args=(
            url, vol_index, chap_index, str(i), selected_manga)))

    for thread in threads:
        thread.start()

    for i in range(len(threads)):
        threads[i].join()


def download_volumes_images(vol_chap_dict: dict[str, list[str]], selected_manga: str, incrementProgress) -> dict[int, dict[int, int]]:
    """Download all images in every volume of a specific manga

    Args:
        vol_chap_dict (dict[str, list[str]]): dictionary in which the keys are the volumes and values are the links to their chapters
        selected_manga (str): manga selected

    Returns:
        dict[int, dict[int, int]]: dictionary of dictionary, with key=volume and the value is dictionary with key=chapter and value=number of images in the chapter
    """
    vol_chap_num_images_dict: dict[int, dict[int, int]] = {}
    
    total_chapter: int = sum([len(chaps) for chaps in vol_chap_dict.values()])
    current_chapter: int = 0

    for index_vol, vol_name in enumerate(vol_chap_dict.keys()):
        chap_num_pages_dict: dict[int, int] = {}

        for index_chap, chap_link in enumerate(vol_chap_dict[vol_name]):
            url: str = chap_link + "/" + str(1) + CHAPTERS_STRING
            number_of_images = number_of_images_in_chapter(url)
            chap_num_pages_dict[index_chap] = number_of_images
            download_chapter_images(chap_link, str(index_vol), str(
                index_chap), selected_manga, number_of_images)
            current_chapter += 1
            
            # calculate the percentage of the download having the current chapter and the total number of chapters
            incrementProgress(current_chapter/total_chapter*100)            
            
            # printProgressBar(current_chapter, total_chapter,
            #                  prefix="Chapter download:", length=50)

        vol_chap_num_images_dict[index_vol] = chap_num_pages_dict

    return vol_chap_num_images_dict


def create_data_volumes_folders(selected_manga: str, vol_chap_dict: dict[str, list[str]]) -> None:
    """Create Data folder, manga folder and inside create the Volumes folders with "volumeNumber_numberofchapters"

    Args:
        selected_manga (str): manga which are selected
        vol_chap_dict (dict[str, list[str]]): dictionary with all volumes and list of links to their chapters
    """
    base_dir = os.path.abspath(os.curdir)
        
    if not os.path.exists(os.path.join(os.getcwd(),"Data")):
        os.mkdir((os.path.join(os.getcwd(),"Data")))

    os.chdir((os.path.join(os.getcwd(),"Data")))
    if os.path.exists(selected_manga):
        shutil.rmtree(selected_manga)
        
    os.mkdir(selected_manga)
    os.chdir(selected_manga)

    for index, _ in enumerate(vol_chap_dict.keys()):
        # name = f"{index}_{len(vol_chap_dict[volume])}"
        os.mkdir(str(index))

    os.chdir(base_dir)


def remove_data_folder(manga_name) -> None:
    """Remove recursively all data in the Data folder
    """
    shutil.rmtree(os.path.join(os.getcwd(),"Data", manga_name))
    
def create_pdf(vol_chap_num_pages: dict[str, list[str]], selected_manga: str) -> None:
    """Create PDFs of every volume contained in the selected manga."""
    if not isinstance(vol_chap_num_pages, dict):
        raise ValueError("vol_chap_num_pages should be a dictionary.")

    for vol_num, chap_num_pag_dict in vol_chap_num_pages.items():
        if not isinstance(chap_num_pag_dict, dict):
            raise ValueError(f"chap_num_pag_dict for volume {vol_num} should be a dictionary.")
        
        merger = PdfMerger()

        for chap_num, num_pages in chap_num_pag_dict.items():
            if not isinstance(num_pages, int):
                raise ValueError(f"num_pages for chapter {chap_num} in volume {vol_num} should be an integer.")

            for i in range(1, num_pages + 1):
                image_path = os.path.join(os.getcwd(),"Data", selected_manga, str(vol_num), f"{chap_num}_{i}.jpg")
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
        with open(f"Volume_{vol_num}.pdf", "wb") as output_file:
            merger.write(output_file)

        merger.close()
        
def create_pdf(manga_name:str) -> None:
    data_path = os.path.join(os.getcwd(),"Data", manga_name)
    
    for volume in os.listdir(data_path):
        volume_path = os.path.join(data_path, volume)
        if not os.path.isdir(volume_path):
            continue
        
        chapter_list = os.listdir(volume_path)
        chapter_list.sort(key=natural_sort_key)
        
        print(f"Processing volume {volume}...")
        print(f"Chapters: {chapter_list}")
        
        image_paths = []
        for chapter in chapter_list:
            chapter_path = os.path.join(volume_path, chapter)
            if not os.path.isfile(chapter_path) or not chapter.lower().endswith('.jpg'):
                continue
            
            try:
                with Image.open(chapter_path) as img:
                    img = img.convert('RGB')  # Ensure the image is in RGB mode
                    image_paths.append(chapter_path)  # Add the file path directly to the list
            except Exception as e:
                print(f"Error processing image {chapter_path}: {e}")
        
        if len(image_paths) == 0:
            print(f"No images found for volume {volume}. Skipping...")
            continue
        
        output_dir = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader", manga_name.replace(' ', '_'))
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
    output_pdf_path = os.path.join(output_dir, f"{manga_name}.pdf")

    output_pdf_path = output_pdf_path.replace(' ', '_')

    print(f"Saving volume {volume} as {output_pdf_path}...")
    
    try:
        with open(output_pdf_path, "wb") as output_file:
            output_file.write(img2pdf.convert(image_paths))
    except Exception as e:
        print(f"Error writing PDF file {output_pdf_path}: {e}")
    
    print(f"Saved as {output_pdf_path}.")

def create_pdf_mangaworld(manga_name:str) -> None:
    # get file list
    folder_list = os.listdir(os.path.join(os.getcwd(),f"Data",manga_name))
    
    merger = PdfMerger()
    
    for volume in folder_list:
        
        
        # get file list
        file_list = os.listdir(os.path.join(os.getcwd(),f"Data",manga_name,volume))
        
        file_list.sort(key=natural_sort_key)
        for file in file_list:
            
            image_path = os.path.join(os.getcwd(),f"Data",manga_name,volume, file)
            
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
    output_dir = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader", manga_name.replace(' ', '_'))
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(os.path.join(output_dir,f"{manga_name.replace(' ', '_')}.pdf"), "wb") as output_file:
        merger.write(output_file)

    merger.close()

def main():
    if len(sys.argv) != 2:
        print("Insert a manga to research!", file=sys.stderr)
        exit(-1)

    manga_to_research: str = sys.argv[1]

    manga_dict: dict[str, str] = research_manga(manga_to_research)

    if len(manga_dict.keys()) == 0:
        print("No manga found with that name! Closing the program...", file=sys.stderr)
        exit(-2)

    selected_manga: str = choose_manga(manga_dict)

    vol_chap_dict: dict[str, list[str]] = volumes_with_chapter_link(
        manga_dict[selected_manga])

    create_data_volumes_folders(selected_manga, vol_chap_dict)

    volume_chap_num_pages_dict: dict[int, dict[int, int]] = download_volumes_images(
        vol_chap_dict, selected_manga)

    create_pdf(volume_chap_num_pages_dict, selected_manga)

    remove_data_folder(selected_manga)


if __name__ == "__main__":
    main()
