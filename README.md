modular
=======


This is a walkthrough for acquiring, installing, and running modular for the first time.

Download the latest version of modular from this link:
https://github.com/ctogle/modular

You will need a build of python with the proper packages to run modular.
You can download python 2.7.8 (32-bit is recommended for now) from this link:
https://www.python.org/download/

The following packages are required to run modular:
Numpy 1.8.1
Scipy 0.14.0
PyOpenGL 3.1.0
PySide 1.2.2
matplotlib 1.3.1
dateutil 2.2
pyparsing 2.0.2
six 1.7.3

The versions you use most likely do not need to match these, but this combination has been tested.

On windows, every one of these can be installed very easily using this website:
http://www.lfd.uci.edu/~gohlke/pythonlibs/
Be sure to grab the proper version as it should indicate it's for python 2.7, 32 or 64 bit, whichever matches the python you installed.
For examples: "numpy‑MKL‑1.8.1.win32‑py2.7.exe" is for python 2.7, 32 bit version.

Once all of these are installed, and the contents of modular have been extracted to a new root folder (assumedly called "Modular"), open a command prompt or terminal.
Use the "cd" command to move to the Modular root directory which contains the file "modular.py" ("dir" command displays current directory contents.)
Use the command "python modular.py" to start modular.

If a window with buttons and such appears, then you can likely start simulating a demo mcfg file.
If instead you get an error along the lines of "python isn't a command", then you need to modify the environment variable "path" so that your prompt or terminal can find python.
Google how to change the "path environment variable" for your os and add a path to your python.exe ("C:\Python27;" is what I had to add on windows.)
You'll know you have this resolved when the command "python" does not return an error, but instead starts python.

Once all of this is working, you can run the "correl_demo.mcfg" demo file found in "Modular/chemicallite/".
Start modular with "python modular.py"
Make an ensemble, selecting the chemicallite module. (Ctrl+E, Tab, Enter)
Parse the "correl_demo.mcfg" demo file by using the "Parse mcfg File" button. (Ctrl+M)
Run the ensemble using the "Run Ensemble" button. (Alt+R)

Lots of things should be printed to your terminal as it runs the simulations (or crashes, in which case email me a screen shot of your terminal.)
This took about 548 seconds on the new dell.

Click the "Plot" button in the windows which appear when it finishes.
Using the interface in these windows, you can view the results of the run.


