from PyQt5.QtCore import QThread, pyqtSignal
from .mangaworld_downloader import volumes_with_chapter_link, create_data_volumes_folders, number_of_images_in_chapter, download_chapter_images, create_pdf, remove_data_folder
import pygame

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)  # Signal for status updates

    def __init__(self, manga_name, selectedManga, mangaDict, parent=None):
        super().__init__(parent)
        self.manga_name = manga_name
        self.selectedManga = selectedManga
        self.mangaDict = mangaDict
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
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

        self.status_update.emit(f"Generating PDFs...")
        create_pdf(selected_manga)
        remove_data_folder(selected_manga)
        self.status_update.emit(f"PDFs generated!")
        
        if self._stop_flag:
            return
        
        # Play sound when download is completed
        pygame.mixer.init()
        pygame.mixer.music.load('sounds/finish.mp3')
        pygame.mixer.music.play()

        # Check the stop flag during sound playback
        while pygame.mixer.music.get_busy():
            if self._stop_flag:
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)
