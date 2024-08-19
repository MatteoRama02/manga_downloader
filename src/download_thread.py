from PyQt5.QtCore import QThread, pyqtSignal
from .scraper.mangaworld_downloader import volumes_with_chapter_link, create_data_volumes_folders, number_of_images_in_chapter, download_chapter_images, create_pdf, remove_data_folder
from .scraper.comick_downloader import url_manga_first_chapter, download_chapters, create_pdf_comick,fetch_image_urls, download_images_in_thread, create_webdriver
import pygame
import os
import threading
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)  # Signal for status updates

    def __init__(self, manga_name, selectedManga, mangaDict, chooseSite="MangaWorld - IT", parent=None):
        super().__init__(parent)
        self.manga_name = manga_name
        self.selectedManga = selectedManga
        self.mangaDict = mangaDict
        self.chooseSite = chooseSite
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def mangaworld_run(self):
        selected_manga = self.selectedManga
        manga_dict = self.mangaDict
        
        if not selected_manga:
            self.status_update.emit("User canceled the selection")
            return

        vol_chap_dict = volumes_with_chapter_link(manga_dict[selected_manga])
        create_data_volumes_folders(selected_manga, vol_chap_dict)

        total_chapters = sum(len(chaps) for chaps in vol_chap_dict.values())
        current_chapter = 0

        for i, (vol_name, chapters) in enumerate(vol_chap_dict.items()):
            if self._stop_flag:
                self.status_update.emit("Download canceled")
                return

            for j, chap_link in enumerate(chapters):
                if self._stop_flag:
                    self.status_update.emit("Download canceled")
                    return
                
                number_of_images = number_of_images_in_chapter(chap_link)
                download_chapter_images(chap_link, i, str(j), selected_manga, number_of_images)

                current_chapter += 1
                self.progress.emit(int((current_chapter / total_chapters) * 100))

        if self._stop_flag:
            self.status_update.emit("Download canceled")
            return

    def comick_run(self):
        selected_manga = self.selectedManga
        manga_dict = self.mangaDict
        
        manga_url = manga_dict[selected_manga]
        # Get the first chapter URL and download chapters
        first_chapter_data = url_manga_first_chapter(manga_url)

        # Get the first chapter URL and total chapters from the returned dictionary
        first_chapter_url = list(first_chapter_data.keys())[0]
        total_chapters = int(first_chapter_data[first_chapter_url])

        self.download_comick_chapters(first_chapter_url, selected_manga, total_chapters)

    def download_comick_chapters(self, first_chapter_url: str, manga_name: str, total_chapters: int):
        current_depth = 1
        retries = 3
        delay = 5
        
        while current_depth <= total_chapters:
            if self._stop_flag:
                self.status_update.emit("Download canceled")
                return

            # Retry logic for downloading images
            for attempt in range(retries):
                try:
                    image_urls = fetch_image_urls(first_chapter_url)
                    title = first_chapter_url.split("/")[-1]  # Assuming title is the last part of the URL

                    # Create folder to store images
                    folder_path = os.path.join(os.getcwd(),"src","scraper","Data", manga_name)
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
                        self.status_update.emit(f"Failed to download images after {retries} attempts.")
                        return  # Exit the function if we can't download images

            # Update progress after each chapter download
            self.progress.emit(int((current_depth / total_chapters) * 100))

            # Retry logic for fetching the next chapter URL
            for attempt in range(retries):
                try:
                    driver = create_webdriver(headless=True)
                    driver.get(first_chapter_url)

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
                    driver.quit()

                    if href_next:
                        first_chapter_url = href_next  # Set the new chapter URL for the next iteration
                        current_depth += 1
                    else:
                        return
                except Exception as e:
                    self.status_update.emit(f"Error finding next chapter on attempt {attempt + 1}/{retries}: {e}")
                    if attempt < retries - 1:
                        self.status_update.emit(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        self.status_update.emit(f"Failed to find the next chapter after {retries} attempts.")
                        return  # Exit the function if we can't find the next chapter

    def run(self):
        selected_manga = self.selectedManga

        if self.chooseSite == "MangaWorld - IT":
            self.mangaworld_run()
            create_pdf(selected_manga)
        else:
            self.comick_run()
            create_pdf_comick(selected_manga)

        self.status_update.emit(f"Generating PDFs...")
        
        remove_data_folder(selected_manga)
        self.status_update.emit(f"PDFs generated!")

        if self._stop_flag:
            return
        
        # Play sound when download is completed
        pygame.mixer.init()
        current_dir = os.path.dirname(os.path.abspath(__file__))

        sound_file_path = os.path.join(current_dir, 'sounds', 'finish.mp3')
        pygame.mixer.music.load(sound_file_path)
        pygame.mixer.music.play()

        # Check the stop flag during sound playback
        while pygame.mixer.music.get_busy():
            if self._stop_flag:
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)
