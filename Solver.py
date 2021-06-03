import sys
import wx
import time
import random
import MySQLdb
#import myql.connector as MySQLdb (use this if you dont have mysqlclient)
import os.path
from city import *
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.figure import Figure

# global variables the use of citiesX and citiesY save on reprocessing the city coord for plotting
# cities stores the coords and the intial order of the coords its and array of city objects
# route stores the coords in the currently solved order
# the rest are mainly for intial settings
cities = []
citiesX = []
citiesY = []
route = []
end_time = 0
timeGiven = ""
problemName = ""
algorithm = "Greedy"
# test to see if the server cannot connect if so prints error then closes
try :
    conn = MySQLdb.connect(user='s5084150', password='L94p3vag', host='mysql.ict.griffith.edu.au', database='1810ICTdb')
    c = conn.cursor()
except:
    print("Error connecting to database")
    quit()
# default for the animation of the plotting
animate = False;

#MatplotPanel class deals with plotting the points in a panel for visulisation
class MatplotPanel(wx.Panel) :
    #justs add the panel plots it and adds the toolbar to the bottom
    def __init__ (self, parent) :
        wx.Panel.__init__(self, parent, style=wx.BORDER_DOUBLE)
        self.figure = Figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor('#E7E7E7')
        self.axes.invert_xaxis()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.ALL|wx.EXPAND)
        self.toolbar = NavigationToolbar(self.canvas)
        self.sizer.Add(self.toolbar, 0, wx.EXPAND)
        self.axes.plot()
        self.SetSizer(self.sizer)
        self.Fit()

    # adds the cities points in red dots to show the problem
    # used when loading new problem
    def plotCites(self) :
        global citiesX
        global citiesY
        citiesX = []
        citiesY = []
        for city in cities :
            citiesX.append(city.X)
            citiesY.append(city.Y)
        self.axes.clear()
        self.axes.plot(citiesY, citiesX, color='#000000', linestyle='None', marker='o', ms='2', aa=True)
        self.canvas.draw()

    # Plots the route in blue and the cities points in red
    def plot(self):
        x = []
        y = []
        for city in route :
            x.append(city.X)
            y.append(city.Y)
        if len(route) > 0 :
            x.append(route[0].X)
            y.append(route[0].Y)
        self.axes.clear()
        self.axes.plot(y, x, '#00D717')
        self.axes.plot(citiesY, citiesX, color='#000000', ls='None', marker='o', ms='2', aa=True)
        self.canvas.draw()

# Custom class for a pop up dialog that allows the user to connect and find a solution
class LoadSolutionDialog(wx.Dialog):
    #sets title
    def __init__(self, *args, **kw):
        super(LoadSolutionDialog, self).__init__(*args, **kw)
        self.InitUI()
        self.SetTitle("Please select solution from database")
    # sets the layout of the dialog and loads the problems in a combobox
    def InitUI(self):
        sizer = wx.GridBagSizer(0, 0)

        textProblem = wx.StaticText(self, label="Problem:")
        sizer.Add(textProblem, pos=(0, 0),
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        self.comboBoxProblem = wx.ComboBox(self)
        sizer.Add(self.comboBoxProblem, pos=(0, 1), span=(1, 2),
            flag=wx.ALL|wx.EXPAND, border=5)
        self.listBoxSolution = wx.ListBox(self, style = wx.LB_SINGLE, size=(300, 90))
        sizer.Add(self.listBoxSolution, pos=(1, 0), span=(4, 2),
            flag=wx.ALL|wx.EXPAND, border=5)
        textFilters = wx.StaticText(self, label="Filters:")
        sizer.Add(textFilters, pos=(0, 3), span=(1, 2),
            flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=5)
        textAlgorithmFilter = wx.StaticText(self, label="Algorithm:")
        sizer.Add(textAlgorithmFilter, pos=(1, 3),
            flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=5)
        self.textInputAlgorithmFilter = wx.TextCtrl(self)
        sizer.Add(self.textInputAlgorithmFilter, pos=(1, 4),
            flag=wx.ALL|wx.EXPAND, border=5)
        textTime = wx.StaticText(self, label="Time:")
        sizer.Add(textTime, pos=(2, 3),
            flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=5)
        self.textInputTime = wx.TextCtrl(self)
        sizer.Add(self.textInputTime, pos=(2, 4),
            flag=wx.ALL|wx.EXPAND, border=5)
        textAuthor = wx.StaticText(self, label="Author:")
        sizer.Add(textAuthor, pos=(3, 3),
            flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=5)
        self.textInputAuthor = wx.TextCtrl(self)
        sizer.Add(self.textInputAuthor, pos=(3, 4),
            flag=wx.ALL|wx.EXPAND, border=5)
        buttonLoad = wx.Button(self, wx.ID_OK, label="Load", size=(90, 28))
        sizer.Add(buttonLoad, pos=(4, 3), span=(1, 2),
            flag=wx.ALL|wx.EXPAND, border=5)

        c.execute("""
        SELECT Name
        FROM Problem
        """)
        query = c.fetchall()
        for problem in query :
            self.comboBoxProblem.Append(problem[0])

        self.selection = ""

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_LISTBOX, self.listBoxSolutionSelect, self.listBoxSolution)
        self.Bind(wx.EVT_COMBOBOX, self.fetch, self.comboBoxProblem)
        self.Bind(wx.EVT_TEXT, self.fetch, self.textInputAlgorithmFilter)
        self.Bind(wx.EVT_TEXT, self.fetch, self.textInputTime)
        self.Bind(wx.EVT_TEXT, self.fetch, self.textInputAuthor)

    # called every time the problem changes or the filters are updated
    # loads from the database the correct solution with given filters
    def fetch(self, event) :
        if (self.comboBoxProblem.GetValue() != "") :
            self.listBoxSolution.Clear()
            buildQuery = """
                SELECT SolutionID, TourLength, Author, Algorithm, RunningTime
                FROM Solution
                WHERE ProblemName = """ + "'" + self.comboBoxProblem.GetValue() + "'"
            if (self.textInputAlgorithmFilter.GetValue() != "") :
                buildQuery += " AND Algorithm LIKE '%" + self.textInputAlgorithmFilter.GetValue() + "%'"
            if (self.textInputAuthor.GetValue() != "") :
                buildQuery += " AND Author LIKE '%" + self.textInputAuthor.GetValue() + "%'"
            if (self.textInputTime.GetValue() != "") :
                buildQuery += " AND RunningTime = " + self.textInputTime.GetValue()
            c.execute(buildQuery)
            query = c.fetchall()
            for problem in query :
                self.listBoxSolution.Append(str(problem[0]) + " " + str(problem[1]) + " " + str(problem[2]) + " " + str(problem[3]) + " " + str(problem[4]))
        else :
            wx.MessageBox("Please select a problem!", style=wx.OK)


    # sets a variable of the selected soltion this is to stop in accesable data
    # ie if no solutions are there and you load you get index out of range
    def listBoxSolutionSelect(self, event) :
        self.selection = self.listBoxSolution.GetString(self.listBoxSolution.GetSelection())

#class for pop up to load a problem into the solver
class LoadProblemDialog(wx.Dialog):
    # sets title
    def __init__(self, *args, **kw):
        super(LoadProblemDialog, self).__init__(*args, **kw)
        self.InitUI()
        self.SetTitle("Please select problem from database")

    #sets layout of the dialog and loads all problems into the combobox
    def InitUI(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        textProblem = wx.StaticText(self, label="Problem:")
        sizer.Add(textProblem,
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        self.comboBoxProblem = wx.ComboBox(self, size=(270, 28))
        sizer.Add(self.comboBoxProblem,
            flag=wx.ALL|wx.EXPAND, border=5)
        buttonRefresh = wx.Button(self, label="Refresh", size=(90, 28))
        sizer.Add(buttonRefresh,
            flag=wx.ALL, border=5)
        buttonLoad = wx.Button(self, wx.ID_OK, label="Load", size=(90, 28))
        sizer.Add(buttonLoad,
            flag=wx.ALL, border=5)

        c.execute("""
        SELECT Name
        FROM Problem
        """)
        query = c.fetchall()
        for problem in query :
            self.comboBoxProblem.Append(problem[0])

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.buttonRefreshClick, buttonRefresh)

    #reloads all the problems in the database into the combobox
    def buttonRefreshClick(self, event) :
        self.comboBoxProblem.Clear()
        c.execute("""
        SELECT Name
        FROM Problem
        """)
        query = c.fetchall()
        for problem in query :
            self.comboBoxProblem.Append(problem[0])

#class to deal with selecting file with file explorer
class FileUploadDialog(wx.Dialog):
    # sets title
    def __init__(self, *args, **kw):
        super(FileUploadDialog, self).__init__(*args, **kw)
        self.InitUI()
        self.SetTitle("Select File to upload")

    #sets layout
    def InitUI(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        textFile = wx.StaticText(self, label="File Location:")
        sizer.Add(textFile,
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        self.textInputFile = wx.TextCtrl(self, size=(270, 28))
        sizer.Add(self.textInputFile,
            flag=wx.ALL|wx.EXPAND, border=5)
        buttonBrowse = wx.Button(self, label="Browse", size=(90, 28))
        sizer.Add(buttonBrowse,
            flag=wx.ALL, border=5)
        self.buttonUpload = wx.Button(self, wx.ID_OK, label="Upload", size=(90, 28))
        sizer.Add(self.buttonUpload,
            flag=wx.ALL, border=5)

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.buttonBrowseClick, buttonBrowse)

    #loads up built in file explorer to find path directory
    def buttonBrowseClick(self, event) :
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.textInputFile.SetValue(path)
        dlg.Destroy()

# Main interface class to display solutions and problems and to animate/solve current problem
class UserInterface(wx.Frame):
    #sets title and min size and default size as well as centring on screen
    def __init__(self, parent, title):
        super(UserInterface, self).__init__(parent, title=title,
        size=(700, 700))
        self.SetMinSize(self.GetSize())
        self.InitUI()
        self.Layout()
        self.Centre()
        self.Show()

    # sets layout
    # -menu bar
    # -matplotlib panel
    # -solver buttons
    def InitUI(self):
        menuBar = wx.MenuBar()

        fileMenu = wx.Menu()
        uploadItem = wx.MenuItem(fileMenu, wx.ID_OPEN, text = 'Upload New Problem \tCtrl+O', kind = wx.ITEM_NORMAL)
        fileMenu.Append(uploadItem)
        saveItem = wx.MenuItem(fileMenu, wx.ID_SAVE, text = 'Save Current Problem \tCtrl+S', kind = wx.ITEM_NORMAL)
        fileMenu.Append(saveItem)

        loadMenu = wx.Menu()
        loadProblemItem = wx.MenuItem(loadMenu, wx.ID_ANY, text = 'Load Problem from Database', kind = wx.ITEM_NORMAL)
        loadMenu.Append(loadProblemItem)
        loadSolutionItem = wx.MenuItem(loadMenu, wx.ID_ANY, text = 'Load Solution from Database', kind = wx.ITEM_NORMAL)
        loadMenu.Append(loadSolutionItem)

        menuBar.Append(fileMenu, "&File")
        menuBar.Append(loadMenu, "&Load")
        self.SetMenuBar(menuBar)


        panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        sizer = wx.GridBagSizer(0, 0)

        textDistance = wx.StaticText(panel, label="Distance:")
        sizer.Add(textDistance, pos=(0, 0),
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        self.textCurrentDistance = wx.StaticText(panel, label="")
        sizer.Add(self.textCurrentDistance, pos=(0, 1),
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)

        self.pnl = MatplotPanel(panel)
        self.pnl.plot()
        sizer.Add(self.pnl, pos=(1, 0), span=(8, 8),
            flag=wx.ALL|wx.EXPAND, border=10)

        textAlgorithm = wx.StaticText(panel, label="Algorithm:")
        sizer.Add(textAlgorithm, pos=(9, 0),
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        self.comboBoxAlgorithm = wx.ComboBox(panel, choices = ['Greedy', 'Two-Opt'])
        sizer.Add(self.comboBoxAlgorithm, pos=(9, 1), span=(1, 2),
            flag=wx.ALL|wx.EXPAND, border=5)
        buttonSolve = wx.Button(panel, label="Solve", size=(90, 28))
        sizer.Add(buttonSolve, pos=(9, 7),
            flag=wx.ALL|wx.EXPAND, border=5)
        textTimeGiven = wx.StaticText(panel, label="Time Allowed:")
        sizer.Add(textTimeGiven, pos=(9, 3),
            flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        self.textInputTimeGiven = wx.TextCtrl(panel)
        self.textInputTimeGiven.SetValue("1000")
        sizer.Add(self.textInputTimeGiven, pos=(9, 4), span=(1, 2),
            flag=wx.ALL|wx.EXPAND, border=5)
        self.checkBoxAnimate = wx.CheckBox(panel, label="Animate")
        sizer.Add(self.checkBoxAnimate, pos=(9, 6),
            flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=5)


        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(2)
        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.buttonSolveClick, buttonSolve)
        self.Bind(wx.EVT_MENU, self.menuUploadClick, uploadItem)
        self.Bind(wx.EVT_MENU, self.menuLoadProblemClick, loadProblemItem)
        self.Bind(wx.EVT_MENU, self.menuLoadSolutionClick, loadSolutionItem)
        self.Bind(wx.EVT_MENU, self.menuSaveClick, saveItem)
        self.Bind(wx.EVT_CHECKBOX, self.checkBoxAnimateClicked, self.checkBoxAnimate)

    #changes the animate setting to allow for animation of the plots
    def checkBoxAnimateClicked(self, event) :
        global animate
        animate = self.checkBoxAnimate.GetValue()

    #calls the save function if there is a solved problem otherwise message box
    def menuSaveClick(self, event) :
        if (len(route) > 0) :
            save(self)
        else :
            wx.MessageBox("Please solve before saving!", style=wx.OK)

    #launches the custom FileUploadDialog to find file then calls the upload function
    def menuUploadClick(self, event) :
        dlg = FileUploadDialog(self, title = 'Please pick a File')
        if dlg.ShowModal() == wx.ID_OK:
            upload(dlg.textInputFile.GetValue())
        dlg.Destroy()

    #lanuches the custom LoadProblemDialog then if "Load" is clicked loads in problem if
    #the problem is valid otherwise error message
    def menuLoadProblemClick(self, event) :
        global problemName
        global cities
        global route
        dlg = LoadProblemDialog(self, title = 'Load a Problem')
        if dlg.ShowModal() == wx.ID_OK :
            problem = dlg.comboBoxProblem.GetValue()
            if (problem != "") :
                route = []
                problemName = problem
                c.execute("""
                SELECT ID, x, y
                FROM Cities
                WHERE Name = %s
                """, (problemName,))
                query = c.fetchall()
                cities = []
                for city in query :
                    x = City(int(city[0]), float(city[1]), float(city[2]))
                    cities.append(x)
                self.pnl.plotCites()
                self.textCurrentDistance.SetLabel("")
            else :
                wx.MessageBox("Please select a problem!", style=wx.OK)
        dlg.Destroy()

    #launches the custom LoadSolutionDialog to get an id for a solution
    #if the id is correct then loads that solution into cities and then the ordered
    #into route if no solution is selected then error message if loaded then plots
    def menuLoadSolutionClick(self, event) :
        global problemName
        global cities
        global route
        dlg = LoadSolutionDialog(self, title = 'Load a Problem')
        if dlg.ShowModal() == wx.ID_OK :
            if (dlg.selection != "") :
                solutionSelection = dlg.selection.split()
                problemName = dlg.comboBoxProblem.GetValue()
                c.execute("""
                SELECT Tour
                FROM Solution
                WHERE SolutionID = %s
                """, (solutionSelection[0],))
                query = c.fetchall()
                tour = query[0][0].split(' ')

                c.execute("""
                SELECT ID, x, y
                FROM Cities
                WHERE Name = %s
                """, (problemName,))
                query = c.fetchall()
                cities = []
                for city in query :
                    x = City(int(city[0]), float(city[1]), float(city[2]))
                    cities.append(x)
                self.pnl.plotCites()

                route = []
                for node in tour :
                    if (node != "-1") :
                        for city in cities :
                            if (str(city.ID) == node) :
                                route.append(city)
                                break
                    else :
                        break
                self.pnl.plot()
                self.textCurrentDistance.SetLabel(str(calculateDistance(route)))
            else :
                wx.MessageBox("Please select a solution!", style=wx.OK)
        dlg.Destroy()

    #runs solver depending on which algorithm is selected. if time is given fall back to 1000
    #if no algorithm is selected(windows issue) then error message. if no problem is loaded then message
    def buttonSolveClick(self, event) :
        global timeGiven
        global algorithm
        method = self.comboBoxAlgorithm.GetValue()
        timeGiven = self.textInputTimeGiven.GetValue()
        if (not timeGiven.isdigit()) :
            timeGiven = 1000
        else :
            timeGiven = int(timeGiven)
        if (problemName != "") :
            if (method == 'Greedy') :
                algorithm = method
                greedySolve(self, timeGiven)
            elif (method == 'Two-Opt') :
                algorithm = method
                twoOptSolve(self, timeGiven)
            else :
                wx.MessageBox("Please select an algorithm to run!", style=wx.OK)
        else :
            wx.MessageBox("Please select a problem!", style=wx.OK)


#saves the current loaded route into the solutions with my name "Carl Humphries"
#and other details required
def save(self) :
    length = int(round(calculateDistance(route)))
    date = time.strftime('%Y-%m-%d')
    tour = ""
    for city in route :
        tour += str(city.ID) + " "
    tour += "-1"
    c.execute("""
    INSERT IGNORE INTO Solution (ProblemName, TourLength, Date, Author, Algorithm, RunningTime, Tour)
    VALUES(%s, %s, %s, %s, %s, %s, %s);
    """, (problemName, length, date, 'Carl Humphries', algorithm, timeGiven, tour))
    conn.commit()

#checks that the .tsp problem is valid if not error message.
#breaks up the problem then stores it from Part A/B
def upload(path) :
    if os.path.isfile(path):
        if path.endswith('.tsp') :
            fhand = open(path, 'r')
            problemName = os.path.splitext(os.path.basename(path))[0]
            comment = ""
            for line in fhand:
                line = line.rstrip()
                if line.startswith('COMMENT') :
                    line = line.strip('COMMENT')
                    line = line.strip(' ')
                    line = line.strip(':')
                    line = line.strip(' ')
                    comment += " " + line
                    break
            for line in fhand:
                line = line.rstrip()
                if line.startswith('DIMENSION') :
                    line = line.strip('DIMENSION')
                    line = line.strip(' ')
                    line = line.strip(':')
                    line = line.strip(' ')
                    size = int(line)
                    break
            c.execute("""SELECT Name
            FROM Problem
            WHERE Name = %s
            """, (problemName,))
            query = c.fetchall()
            if len(query) < 1 :
                c.execute("""
                INSERT IGNORE INTO Problem VALUES(%s, %s, %s);
                """, (problemName, size, comment))
                for line in fhand:
                    line = line.rstrip()
                    if line.startswith('NODE_COORD_SECTION') :
                        break
                for line in fhand:
                    line = line.rstrip()
                    if line == "EOF" or line == "":
                        break
                    else:
                        raw = line.split()
                        c.execute("""
                        INSERT IGNORE INTO Cities VALUES(%s, %s, %s, %s);
                        """, (problemName, int(raw[0]), float(raw[1]), float(raw[2])))
                        # print(int(raw[0])/size*100)
                        # use this to see percentage of upload
                conn.commit()
            else :
                wx.MessageBox("Problem already added, Please select another!", style=wx.OK)
        else :
            wx.MessageBox("Not a valid .TSP file!", style=wx.OK)
    else :
        wx.MessageBox("Not a valid path!", style=wx.OK)

#two opt swap method#
def twoOpt(oldRoute, posOne, posTwo) :
    newRoute = []
    newRoute = list(oldRoute[0:posOne] + oldRoute[posOne:posTwo][::-1] + oldRoute[posTwo:len(oldRoute)])
    return newRoute
#calculateDistance method for finding distance of list of cities#
def calculateDistance(cities) :
    routeDistance = 0
    first = cities[0]
    prev = first
    for city in cities:
        routeDistance += city.dist(prev)
        prev = city
    routeDistance += prev.dist(first)
    return routeDistance

def greedySolve(self, timeGiven) :
    #Greedy start#
    end_time = time.time() + timeGiven
    global route
    bestroute = []
    citiesTemp = list(cities)
    bestroute = cities
    route = []
    minimum = calculateDistance(cities)
    self.textCurrentDistance.SetLabel(str(minimum))
    for start in range(0, len(citiesTemp)) :
        citiesTemp = list(cities)
        route[:] = []
        route.append(citiesTemp[start])
        last = citiesTemp[start]
        del citiesTemp[start]
        while len(citiesTemp) > 0 and time.time() < end_time:
            distance = 0
            for index, city in enumerate(citiesTemp):
                if city.dist(last) < citiesTemp[distance].dist(last):
                    distance = index
            route.append(citiesTemp[distance])
            last = citiesTemp[distance]
            del citiesTemp[distance]
            if animate :
                self.pnl.plot()
        currentDistance = calculateDistance(route)
        if time.time() > end_time:
            break
        if currentDistance < minimum :
            minimum = currentDistance
            self.textCurrentDistance.SetLabel(str(minimum))
            bestroute = list(route)
    route = bestroute
    self.pnl.plot()
    self.textCurrentDistance.SetLabel(str(minimum))
    #prints the result as well as storing it. always stores newest run

def twoOptSolve(self, timeGiven) :
    #two opt swap#
    end_time = time.time() + timeGiven
    startTime = time.time()
    global route
    if (len(route) == 0) :
        route = list(cities)
    # route = list(cities)
    self.pnl.plot()
    oldDistance = calculateDistance(route)
    self.textCurrentDistance.SetLabel(str(oldDistance))
    improvements = True
    done = False
    while improvements == True:
        improvements = False
        for posOne in range(0, len(route)-1) :
            for posTwo in range(posOne+1, len(route)) :
                # testDistance = calculateDistance(new_route)
                # took out the calcualtion of the distance everytime significantly increasing speed
                distafter = route[(posOne+(len(route)-1))%len(route)].dist(route[posTwo-1]) + route[posOne].dist(route[posTwo%len(route)])
                distbefore = route[(posOne+(len(route)-1))%len(route)].dist(route[posOne]) + route[posTwo-1].dist(route[posTwo%len(route)])
                if time.time() > end_time :
                    done = True
                    break
                if distafter < distbefore :
                    new_route = twoOpt(route, posOne, posTwo)
                    route = list(new_route)
                    if animate == True :
                        self.pnl.plot()
                        self.textCurrentDistance.SetLabel(str(calculateDistance(route)))
                    improvements = True
                    break
            if improvements == True or done == True:
                break
    oldDistance = calculateDistance(route)
    self.pnl.plot()
    self.textCurrentDistance.SetLabel(str(oldDistance))

#Main#
if __name__ == '__main__':

    app = wx.App()
    UI = UserInterface(None, title='TSP Program')
    app.MainLoop()
