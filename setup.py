from distutils.core import setup

resource_files = ['res/*','themes/*']

setup( 
    name = "CherryMusic",
    version = "0.2",
    description = "a mp3 server for your browser",
    long_description="""CherryMusic is a music streaming
    server based in cherrypy and jPlayer. You can search
    your collection, create and share playlists with
    other users.
    """,
    author = "Tom Wallroth & Tilman Boerner",
    author_email = "tomwallroth@gmail.com, til.boerner@gmx.net",
    url = "http://www.fomori.org/cherrymusic/",
    license = 'GPL',
    install_requires=["CherryPy >= 3.2.2"],
    packages = ['cherrymusic','cherrymusic.test'],
    #startup script
    scripts = ['cherrymusic.py'],
    #data required by the declared packages
    package_data = { 'cherrymusic' : resource_files }
)