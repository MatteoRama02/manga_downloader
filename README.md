### English Version

A Manga Downloader, source of the pages [MangaWorld](https://www.mangaworld.ac/) and [Comick](https://comick.io/)

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

    python main.py


![alt text](https://raw.githubusercontent.com/MatteoRama02/manga_downloader/main/src/img/screenshot/main2.png)

- Write the name of the manga in the Text input
- If the name is in many mangas, select in the window the right one
- The manga will be exported in pdf and mobi in the folder _/Documents/MangaDownloader_

# Feature

![alt_text](https://raw.githubusercontent.com/MatteoRama02/manga_downloader/main/src/img/screenshot/manager.png)


- Check the status of the download in the Download Manager
- MultiDownload

# To implement

- Choose Chapters
- Release package

# Windows User

I haven't tested this script on Windows, but i have used the os independent paths. So i think its gonna work.

### Versione Italiana

Un Downloader di manga, fonte delle pagine [MangaWorld](https://www.mangaworld.ac/) e [Comick](https://comick.io/)

---

# Setup

## Installa Python e le librerie

- Basato su arch:

      sudo pacman -S python python-pip

-Debian/Ubuntu:

      sudo apt install python3 python3-pip

## Installa le librerie di Python

    pip install -r requirements.txt

# Utilizzo

    python main.py

- Scrivi il nome del manga nell'input di testo
- Se il nome è presente in molti manga, seleziona nella finestra che apparirà quello giusto
- Il manga verrà esportato in pdf e mobi nella cartella _/Documents/MangaDownloader_

# Funzionalità

- Controlla lo stato del download nel Download Manager
- Download multiplo

# Da implementare

- Sceglta capitoli
- Pacchetto di rilascio

# Utente Windows

Non ho testato questo script su Windows, ma ho utilizzato i percorsi indipendenti dal sistema operativo. Quindi penso che funzionerà.

## Crediti

- Le funzioni di recupero immagini di manga e ricerca dei nomi nel sito di MangaWorld è grazie alla repo [mangaworld_downloader](https://github.com/lmarzocchetti/mangaworld_downloader), rilasciato sotto la licenza MIT.
- Le funzioni di conversione PDF a MOBI è grazie alla repo [kcc - Kindle Comic Converter](https://github.com/lmarzocchetti/mangaworld_downloader)

