# Aptivate Generic Intranet

This is a basic intranet application, written in Django.

It's intended to be easily extensible, and made from reusable
components.

Standard components are expected to include:

* Document library with content indexing and searching
* User profiles and permissions
* User directory (to find and contact users)

It may eventually include calendar, blog and wiki modules as well.

## Installation on Unix

`intranet` here means the directory where you checked out the Intranet code.
It should contain directories like `apache`, `deploy` and `django`.

Decide which environment name you're going to deploy. These are files
like `intranet/django/intranet/local_settings.py.*`. Examples are `dev`,
`staging` and `production`. If none of these configurations match your own,
you may wish to create a new one.

	cd atamis-intranet
	./deploy/tasks.py deploy:dev (or :whatever environment name)
	cd django/intranet
	./manage.py runserver

This should show you the server running correctly:

## Installation on Windows

### Installing the Django stack

Install [BitNami DjangoStack](http://bitnami.org/stack/djangostack) to get a
working Django installation on Windows. You can disable PostgreSQL and SQLite
databases if you like, you only need MySQL.

It's important to use DjangoStack 1.3 for now, until the support for Django
1.4 is completed.

During the installation you will need to choose a MySQL password. **DO NOT**
leave it blank and **DO** write it down somewhere safe and secure!

Say *Yes* to associating .py files with the Python interpreter, and *No* to
*Do you want to set up an initial project*.

Add the following directories to your PATH:

* `C:\Program Files\BitNami DjangoStack\mysql\bin`
* `C:\Program Files\BitNami DjangoStack\python`
* `C:\Program Files\BitNami DjangoStack\python\scripts`

### Configuring the Django stack

Open a command prompt and install `pip` and `virtualenv` in the BitNami
Python environment:

	easy_install pip virtualenv

You need to download an LXML binary package for Windows. This needs to
match the version of Python installed by BitNami, currently 2.6. You
can install that version using this command:

	easy_install lxml==2.3

If that doesn't work, check the [available downloads](http://pypi.python.org/pypi/lxml/2.3#downloads)
for one that works with your BitNami's version of Python.

You need to download and install `pywin32`. Read the 
[README file](http://heanet.dl.sourceforge.net/project/pywin32/pywin32/README.txt)
carefully, and then go to 
[the build list](http://sourceforge.net/projects/pywin32/files/pywin32/),
choose the latest build (or Build 217 if the latest doesn't work for some reason), 
download the appropriate version for your system, for example
[pywin32-217.win32-py2.6.exe for 32-bit Python 2.6](http://sourceforge.net/projects/pywin32/files/pywin32/Build%20217/pywin32-217.win32-py2.6.exe/download)
and run it to install it.

Similarly you need to download and install `PIL` 1.1.6 for your BitNami's
version of Python. Choose the right version from the
[download list](http://effbot.org/downloads/#pil), download and run it. It
should complain and refuse to install if it doesn't find the right version
of Python already installed on the system. Note that
[PIL 1.1.7 is broken](http://groups.google.com/group/pyinstaller/browse_thread/thread/c4d7b57ef3a5bf8b)
and you should not use it unless you want to manually hack the manifests
with `mt.exe`.

Similarly, if you want to use the Active Directory integration, you need
to download and install `python-ldap` from
[Christoph Gohlke](http://www.lfd.uci.edu/~gohlke/pythonlibs/#python-ldap).

Note that the current official version of `python-ldap` on
[PyPI](http://pypi.python.org/pypi/python-ldap/) (2.4.10) appears to be broken.
You cannot load the library after installation due to a DLL error. So
please don't install that version:

    Python 2.6.2 (r262:71605, Apr 14 2009, 22:40:02) [MSC v.1500 32 bit (Intel)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import ldap
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\Program Files\BitNami DjangoStack\python\lib\site-packages\ldap\__init__.py", line 22, in <module>
        from ldap._ldap import *
    ImportError: DLL load failed: This application has failed to start because the application configuration is incorrect. Reinstalling the application may fix this problem.

### Installing the Intranet

You need to know where to get the files from. This is most likely a Git
repository, unless someone gave you a [ZIP file](https://github.com/aptivate/intranet/zipball/master)
or something like that. The ZIP installation doesn't require Git, but
can't easily be upgraded later.

We will assume that you need to check out the code from a Git repository.

### Downloading the application using Git

Install the latest version of [MSYS Git](http://code.google.com/p/msysgit/downloads/list).
During the installation, be sure to select *Run Git from the Windows command prompt*.

If you need access to a private repository, follow
[these instructions](https://help.github.com/articles/generating-ssh-keys)
to generate a new `id_rsa.pub` file. Skip *Step 4: Add your SSH key to GitHub*, and
send the `id_rsa.pub` file to the administrator who controls the repository
you want to access.

Run the *Git GUI* (from Start/Programs/Git) and choose *Clone Existing Repository*.
For the *Source Location*, enter the Git repository URL that you were given,
for example: `git://github.com/aptivate/intranet.git`. For the *Target Directory*,
click on the *Browse* button, navigate to *C:/Program Files/BitNami DjangoStack/apps*,
and then add '/intranet' on the end of the directory name. Click on the *Clone*
button. When it's finished downloading the code, you will see a window with red,
orange and green bars. Please close this window.

### Configuring the application

Open a Windows command prompt and change directory to the `intranet` directory:

	cd "C:\Program Files\BitNami DjangoStack\apps\intranet"

Start a Windows deployment:

	python deploy\tasks.py deploy:windows

It should end like this, anything else is an error:

	** Finished deploying intranet for windows.

If it fails with the following error:

	WindowsError: [Error 14001] This application has failed to start because the application configuration is incorrect. Reinstalling the application may fix this problem

That's due to a [bug in virtualenv](https://github.com/pypa/virtualenv/issues/294). It seems that you can fix it with the following commands:

	pip uninstall virtualenv
	pip install git+git://github.com/aptivate/virtualenv.git
	del /s/q django\intranet\.ve

Create a user that you can use to log into the Intranet:

	python django\intranet\manage.py createsuperuser

Load any fixtures that you've been told to load, for example:

	cd django\intranet
	python manage.py loaddata atamis\fixtures\ata_groups.json
	python manage.py loaddata atamis\fixtures\ata_programs.json

Run the Intranet using the test server:

	python manage.py runserver

Open a web browser and check that you can connect to the Intranet using
the test server at [http://localhost:8000/](http://localhost:8000/), and
that you can log in using the superuser account that you just created.

Press Ctrl+C in the command prompt window to kill the test server, and
try to access the Intranet through Apache at [http://localhost/](http://localhost/),
and log in using the superuser account.

### Installing Apache Tika Server

The Intranet uses Apache Tika to extract plain text from binary documents,
such as Microsoft Word and Excel files, to index them for searching.
Apache Tika requires a servlet container such as Apache Tomcat to host it
reliably and start automatically when the system is started.

[Download the latest stable version of Tomcat 7](http://tomcat.apache.org/download-70.cgi).
We recommend downloading the 32-bit/64-bit Windows Service Installer. Run
the installer to install the application.

If the installer asks for the *path to java 6.0 or later JRE*, that probably
means that you don't have a Java runtime environment installed. In that case,
cancel the installation of Tomcat, download and install a
[Java 7 JRE](http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1637588.html),
probably the "Windows x86 Offline" or "Windows x64" version, and then start
the Tomcat installation again.

During the installation, enter a Tomcat Administrator User name and Password,
and record them somewhere safe and secure.

When the installation finishes, open
[http://localhost:8080/](http://localhost:8080/) in your browser and
check that it shows a page saying *If you're seeing this, you've
successfully installed Tomcat. Congratulations!*.

Now use Windows Explorer to find:

	C:\Program Files\BitNami DjangoStack\apps\intranet\java\tika-server-1.1-SNAPSHOT.war

Copy it to whichever of the following directories exists:

	C:\Program Files\Apache Software Foundation\Tomcat 7.0\webapps
	C:\Program Files (x86)\Apache Software Foundation\Tomcat 7.0\webapps

And rename it to `tika.war`. Watch that directory, in a few seconds you
should see a directory called `tika` magically appear, as Tomcat unpacks
the WAR file. You should then be able to open
[http://localhost:8080/tika/tika](http://localhost:8080/tika/tika) in your
browser, and it should show this message:

	This is Tika Server. Please PUT

When you see that, your installation should be finished! Try uploading some
documents to the intranet to check that it works, and the contents are
properly extracted and indexable.

Open *Control Panel/Administrative Tools/Services*, find the
*Apache Tomcat* service and double-click on it. If it's not started,
click on the Start button. Check that the *Startup type* is set to
*Automatic*.

### Error R6034

You may get the following pop-up error message while using the Intranet:

	Program: C:\PROGRA~1\BITNAM~1\apache2\bin\httpd.exe
	R6034
	An application has made an attempt to load the C runtime library incorrectly.

This seems to be caused by BitNami DjangoStack distributing its own copy
of the Microsoft C runtime, which can conflict with the version installed
on the system. It seems to happen the first time that the application uses a
native library, for example when uploading a new image or document.

You can try the following steps to disable BitNami's copy of the C runtime:

* Go into `C:\Program Files\BitNami DjangoStack\apache2\bin`
* Create a directory called `disabled`
* Move all the `msvc*.dll` and `Microsoft.VC90` files into the `disabled` directory
* Go into `C:\Program Files\BitNami DjangoStack\python`
* Repeat the same steps as above.

Then restart the djangoStack Apache service and check that the error does
not occur when you upload a file.
