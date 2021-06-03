#TSP Solver#
#Required Files:#
-Solver.py        (Main program)
-city.py          (Class to structure cities)

#Required Installs:#
-matplotlib
python -m pip install matplotlib
//but I'm pretty sure I used pip3 and it was pip3 install matplotlib

-mysqlclient (MySQLdb)
pip3 install mysqlclient

-wx
pip3 install -U wxPython

//Note all packages used both pip and pip3 just incase

#Display#
I went with 700x700 size and set it to minimum but you can expand the program and scales accordingly

#Usage#
Anything that isnt the solver is in the menu bar
-upload from file to database (needs to be valid .tsp file) [Shortcut Ctrl+O or Command+O{Mac}]
-save to database (needs to have a currently solved problem) [Shortcut Ctrl+S or Command+S{Mac}]
-load problem (fetches all problems currently on the database and you pick one)
-load solution (fetches all problems to pick solutions for then uses filters to find specific solutions)

Solver is very straight forward
-load problem or solution
-pick algorithm
-pick time allowed (Default 1000sec) in seconds
-choose to animate (Slows down potential solving but looks nice)
-click solve
-then can save if need be with the save menu item or Ctrl+S or Command+S(Mac)
-can use navbar to look around at the problem and save image


#Bugs#
-the distance doesnt update on slower computers until its finished when animate is on (works on home windows good computer)
-when running large problems window becomes unresponsive but still finishes
-be careful loading solutions some students dont follow format so it doesnt load correctly
-dont know why but orignally loading the tsp as <node> <x> <y> made usa look backwards and rotated
 so had to swap the plotting so x and y plot as plot(y, x) and also had to flip the x axis weird but usa looked right so went with it

Any problems with packages not working email me at carl.w.humphries@gmail.com
