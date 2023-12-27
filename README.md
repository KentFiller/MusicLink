<h1>MusicLink - Spotify Playlist Downloader</h1>

 ### [YouTube Demonstration](https://youtu.be/rxRgUHNu4aU)

<h2>Description</h2>
This Code Project allows users to upload MP3 files created from Spotify playlists to their devices.
Most of the interesting code will be in the dashboard, which houses the majority of the important functions for playlist downloading. Each function has a specific application in different areas of the web app. 
There are several that handle various tasks such as user authentication, to obtaining song data from the provided playlist link, obtaining YouTube URLs, downloading MP3s, and sending the zip file containing the chosen songs to the user's device.
<br />


<h2>Languages and Utilities Used</h2>

- The project is made using Python, Flask, SQLAlchemy, HTML, CSS, and JavaScript.
- It also uses both the Spotify and YouTube Data API.

<h2>Environments Used </h2>

- <b>VSCode Codespaces</b>

<h2>Program walk-through:</h2>

<p align="center">
Home Page: <br/>
<img src="https://i.imgur.com/Yg0s2be.png" height="80%" width="80%" alt="Usage Steps"/>
<br />
<br />
Go to "Register" and type in a username and password, same with "Login", you just type in your newly made username and password:  <br/>
<img src="https://i.imgur.com/VU1LVJY.png" height="80%" width="80%" alt="Usage Steps"/>
<br />
<br />
After that, you'll be redirected to the dashboard, where you can paste a playlist link on the field box: <br/>
<img src="https://i.imgur.com/J3jVLbQ.png" height="80%" width="80%" alt="Usage Steps"/>
<br />
<br />
After you pasted your desired spotify playlist link(Public playlist), press the "Get Playlist" button (may take some time to load):  <br/>
<img src="https://i.imgur.com/CrmkAh2.png" height="80%" width="80%" alt="Usage Steps"/>
<br />
<br />
Here you can see the all the songs in the playlist, select which ones you want to upload to your device by ticking the boxes:  <br/>
<img src="https://i.imgur.com/AviD9Y6.png" height="80%" width="80%" alt="Usage Steps"/>
<br />
<br />
After selecting your desired songs, press the "Download Selected Songs" button:  <br/>
<img src="https://i.imgur.com/k6jK3KT.png" height="80%" width="80%" alt="Usage Steps"/>
<br />
<br />
Youll be prompted to download a zip file, agreeing with it will download the zip file into your device, in the file is the songs you selected:  <br/>
<img src="https://i.imgur.com/KaHaCcK.png" height="80%" width="80%" alt="Usage Steps"/>
</p>

## Acknowledgments

MusicLink relies on several libraries and resources, including:

- [Flask](https://flask.palletsprojects.com/)
- [Flask Login](https://flask-login.readthedocs.io/en/latest/)
- [Flask WTForms](https://flask-wtf.readthedocs.io/en/1.2.x/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Spotipy](https://spotipy.readthedocs.io/)
- [Spotify API](https://developer.spotify.com/documentation/web-api)
- [YouTube Data API](https://developers.google.com/youtube/registering_an_application)
- [Pytube](https://github.com/pytube/pytube)

<!--
 ```diff
- text in red
+ text in green
! text in orange
# text in gray
@@ text in purple (and bold)@@
```
--!>
