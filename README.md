##Introduction
YAMC is a distributed cross-platform media center built with Python. 

##Capabilities
The media center is made of clients and servers. The client has a user interface while the server is headless.

**The client can:**

- Play music locally
- Play music remotely on any client or server instance
- Run on Windows, Linux and Mac

**The server can:**

- Play music locally
- Be controlled by any client or server instance
- Run on Windows, Linux and Mac
- Run on a Raspberry Pi

##Requirements
- Python2.7
- Qt4.7
- PySide1.1.2
- Phonon-VLC or Phonon-backend-gstreamer-4.6.3
- mutagen 1.12 (Used to index media files)

##Usage
###To start the client
python yam/clientapp.py
###To start a server instance
python yam/serverapp.py
