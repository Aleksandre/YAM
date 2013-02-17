##Introduction
YAMC is a free and open source media player application availaible for multiple operating-systems.

##Description
Three YAMC device types are availaible : a client, a server and a mobile application.

<b>The client</b> is a desktop application that can:

- Play music locally
- Play music remotely on any client or server instance
- Run on Windows, Linux and Mac

<b>The server</b> is an headless python server that can:

- Play music locally
- Be controlled by any client or server instance
- Run on Windows, Linux and Mac
- Run on a Raspberry Pi

**The mobile application can:**
 Do nothing for now.

##Requirements
- Python2.7
- Qt4.7
- PySide1.1.2
- Phonon-VLC or Phonon-backend-gstreamer-4.6.3
- mutagen 1.12 (Used to index media files)

##Usage
###To start the client
<code>python yam/clientapp.py</code>
###To start a server instance
<code>python yam/serverapp.py</code>

###Example
To start a server instance that will
- Listen for TCP requests on port 2000
- Broadcast it's presence with UPD messages on port 3000

Run the following command:
<code>python yam/serverapp.py --request_port 2000 --broadcast_port 3000</code>

