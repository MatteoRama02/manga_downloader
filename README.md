# mangaworld_downloader

A manga pdf downloader from mangaworld

Un programma per scaricare manga da MangaWorld (sito italiano)

---

# Setup

## Install Python and dependencies

- Arch-based:

      sudo pacman -S python python-pip

- Debian/Ubuntu:

      sudo apt install python3 python3-pip

## Install dependencies of Python

    pip install -r requirements.txt

# Usage

    python gui.py

- Write the name of the manga in the Text input
- If the name is in many mangas, select in the window the right one
- The manga will be exported in pdf foreach volume in the folder _/Documents/MangaDownloader_

# To implement

- Choose Chapters
- Remove downloading manga

# Windows User

I haven't tested this script on Windows, but i have used the os independent paths. So i think its gonna work.
