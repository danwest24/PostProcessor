
# coding: utf-8

# In[46]:


import sys



#from tkinter import Tk, Label, Button

try:
    import tkinter as tk
    from tkinter import Tk, Label, Button
except(ImportError):
    import Tkinter as tk
    from Tkinter import Tk, Label, Button
import pandas as pd
import matplotlib
from scipy import signal
import scipy
import numpy as np
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure 
import os
#import Image, ImageDraw
#os.chdir('/home/danwest24/python scripts/Post Processor App/')


# In[47]:

class readwritefile(object):
    #must be called after controller has user input from config frame
    #NOTE: a column that is entirely NaN's (which would result from nonfunctional sensor) will break the plotting functions
    #need to write a function that handles automatically or through GUI user input
    #so far the easiest way to handle this is to fill the NaN's in that column with zero, although this throws off the 
    #averaging functions. perhaps setting a numerical flag if a column of NaN's is detected and then reading this flag to
    #determine program's actions at the time of averaging would be the ideal solution
    def __init__(self, controller):
        self.controller = controller
        self.filename = ('%s.csv' % controller.userin)
        
        self.readfile()
        self.nullchecker()
    def nullchecker(self):
        self.nullflag = []
        nullArr = self.datafile.isnull()
        
        sumnull = nullArr.sum(axis =0)
        # if number of nulls in a column exceeds half the number of rows, the row is replaced with 0's
        #which will allow the rest of them to be plotted without error
        for ind in range(len(self.datafile.columns)):
            if sumnull[ind] > ((len(self.datafile))/2):                    
                self.datafile.iloc[:,ind].fillna(value=0, axis=0, inplace=True)
                self.nullflag.append(ind)
        print(self.nullflag)
    def readfile(self):
        cwd = os.getcwd()
        
        filenames = os.listdir(cwd)
        
        result = [ filename for filename in filenames if filename.endswith( '.csv' ) ]
        print(result)
        self.matchflag= False
        for name in result:                        
            if self.filename == name:
                self.matchflag = True
        if self.matchflag is False:
            print('File not found! make sure its in the current directory')
            
        else:
            try:
                self.datafile = pd.read_csv(self.filename, names=['Timestamp','Flux1','GroundTemp1','Flux2','GroundTemp2','Flux3','GroundTemp3','Flux4','GroundTemp4','Temp1','Temp2','Temp3','Temp4','Temp5','Temp6','Humid1','Humid2','Humid3','Humid4', 'Humid5', 'Humid6'], header=None)
            except:
                self.datafile = pd.read_csv(self.filename, names=['Timestamp','Flux1','GroundTemp1','Flux2','GroundTemp2','Flux3','GroundTemp3','Flux4','GroundTemp4','Temp1','Temp2','Temp3','Temp4','Temp5','Temp6','Humid1','Humid2','Humid3','Humid4', 'Humid5', 'Humid6', 'ConcTemp1'], header=None)
            ##formatting the timestamp to work with matplotlib's date plotting
            
            self.datafile['Timestamp'] = pd.to_datetime(self.datafile['Timestamp'], format='%H:%M:%S')
            #self.datafile['Temp5'].fillna(value=0, axis=0, inplace=True)
            #self.datafile['Humid5'].fillna(value=0, axis=0, inplace=True)


    def writefile(self):
        self.filewrite = ('%s.csv' % self.controller.userin3)
        self.controller.datafile.to_csv(path_or_buf=self.filewrite)



# In[48]:

class Post_processor(object):
    """Post processor object works with data AFTER it has been trimmed and interpolated, and has correct sign.
        Flux sensors do not specify an up or a down, but all sensor outputs can be compared to 
        align the flux sensor data appropriately
        
        Post processor object currently has 5 functions:
        Plotter(): divides the pandas data into subcategories and plots them on subplots attached to figures.
        Figures are plotted on canvas tkinter object, and can be exported using figure.savefig()
        avg(): combines multiple sensor outputs into a single average parameter
        rollingavg(): gives rolling average with input parameter, bin size. bin size is the number of points adjacent
        to the target point that will be used to get an average value, which will then replace the target point, for 
        each element in the array.
        peaks(): finds the peaks of the data, can be used to eliminate outliers, etc
        
        """
    def __init__(self, controller):
        
        #self.t = controller.file.datafile['Timestamp']
        #uncomment above for full timestamp
        
        
        self.controller = controller
        self.datafile = self.controller.datafile
        self.t = self.datafile['Timestamp']
        self.binsize = self.controller.userin2
        self.matchflag = False             
        self.avg()
        self.rollingavg()
        self.stats()
        self.peaks()
        self.plotter()   
        
    def export(self, fignum):
        if fignum == 0:
            filename = ('%s.pdf' % self.controller.userin5)
        elif fignum == 1:
            filename = ('%s.pdf' % self.controller.userin6)
        elif fignum == 2:
            filename = ('%s.pdf' % self.controller.userin7)
        elif fignum == 3:
            filename = ('%s.pdf' % self.controller.userin9)
        elif fignum == 4:
            filename = ('%s.pdf' % self.controller.userin8)
        else:
            filename = 'default.pdf'
        spl = filename.split('.')
        if len(spl) >=2:
            filename = spl[0]
        elif len(spl) ==1:
            pass
        self.figures[fignum].savefig(filename)
        print('figure saved')
    def plotter(self):
        #create figures
        #CHANGES MADE FOR NaN COLUMN COMPATIBILITY:
        #commented out plots for affected column
        #commented out tight layout
        #changed subplot assignment and grid layout turning on
        Xmaxsize = self.controller.screen_w//100 -2   # 19.2 - > 19
        Ymaxsize = self.controller.screen_h//100 -2   # 10.8 - > 10
        f = Figure(figsize=(Xmaxsize,Ymaxsize), dpi=100)
        f2 =Figure(figsize=(Xmaxsize,Ymaxsize), dpi=100)
        f3 =Figure(figsize=(Xmaxsize, Ymaxsize), dpi=100)
        f4 =Figure(figsize=(Xmaxsize, Ymaxsize), dpi=100)
        f5 =Figure(figsize =(Xmaxsize, Ymaxsize), dpi=100)
        
        self.figures = [f, f2, f3, f4, f5]        
        #add subplots to figures
        #letter variables are arrays of subplots. each figure connects to the subplots it needs by letter-number pair
        #nanvariable = [0,3]
        self.a = [self.figures[ind].add_subplot(411) for ind in range(4)]
        self.b = [self.figures[ind].add_subplot(412) for ind in range(4)]
        self.c = [self.figures[ind].add_subplot(413) for ind in range(4)] 
        self.d = [self.figures[ind].add_subplot(414) for ind in range(4)]        
        for ind in range(3):
            self.a[ind].grid(True)
            self.b[ind].grid(True)
            self.c[ind].grid(True)
            self.d[ind].grid(True)
            
        self.e = self.figures[4].add_subplot(311)
        self.e.grid(True)
        self.f = self.figures[4].add_subplot(312)
        self.f.grid(True)
        
        self.g = self.figures[4].add_subplot(313)
        self.g.grid(True)
        #figures 1, 2, 3, and 4 created
        # 0 - individual raw readings 1 - averages of all sensors 2 - rolling averages (smoothed) 3-peaks
        
        
        self.g.plot(self.peakflux1times, self.peakflux1, label = 'Peaks, Flux 1')
        self.g.plot(self.peakflux2times, self.peakflux2, label = 'Peaks, Flux 2')
        self.g.plot(self.peakflux3times, self.peakflux3, label = 'Peaks, Flux 3')
        self.g.plot(self.peakflux4times, self.peakflux4, label = 'Peaks, Flux 4')
        
        self.g.legend(loc='upper left')
        self.e.plot(self.peaktimes,self.peakvalues, label = 'Peaks, including minima')
        self.e.plot(self.peaktimes2, self.peakvalues2, label = 'Peaks above average flux')
        self.e.plot(self.t, self.datafile['RollingFluxAverage'], label = 'Rolling Flux Average')
        self.e.set_title('Peak Flux measurements')
        self.e.set_ylabel('Flux (W/m^2)')
        self.e.legend(loc='upper left')
        
        self.f.plot(self.t, self.datafile['Flux1']) 
        self.f.plot(self.t, self.datafile['Flux2']) 
        self.f.plot(self.t, self.datafile['Flux3']) 
        self.f.plot(self.t, self.datafile['Flux4'])
        self.f.plot(self.peaktimes2,self.peakvalues2)
        self.f.set_ylabel('Flux (W/m^2)')
        self.f.legend(loc='upper left')
        
        self.figures[4].autofmt_xdate()
        self.figures[4].tight_layout()
        
        self.a[3].plot(self.t, self.datafile['RollingFlux1'], label = 'Flux 1 Rolling Average')
        self.a[3].set_ylabel("Flux, W/m^2")
        self.a[3].grid(True)
        self.b[3].plot(self.t, self.datafile['RollingFlux2'], label = 'Flux 2 Rolling Average')
        self.b[3].set_ylabel("Flux, W/m^2")
        self.b[3].grid(True)
        self.c[3].plot(self.t, self.datafile['RollingFlux3'], label = 'Flux 3 Rolling Average')
        self.c[3].set_ylabel("Flux, W/m^2")
        self.c[3].grid(True)
        self.d[3].plot(self.t, self.datafile['RollingFlux4'], label = 'Flux 4 Rolling Average')
        self.d[3].set_ylabel("Flux, W/m^2")
        self.d[3].grid(True)
        self.figures[3].autofmt_xdate()
        #self.figures[3].tight_layout()
        
        
        
        self.a[2].plot(self.t, self.datafile['RollingFluxAverage'])  
        self.a[2].set_title('Flux, Rolling Average')
        self.a[2].set_ylabel('Flux (W/m^2)')    
        self.a[2].labelpad = 20
        self.a[2].ypad = 20
        self.a[2].legend(loc='upper left')
        self.b[2].plot(self.t, self.datafile['RollingTempAverage'])
        self.b[2].set_title('Air Temperature, Rolling Average')    
        self.b[2].set_ylabel('Temperature (degC)')
        self.b[2].labelpad = 20
        self.b[2].ypad = 20
        self.b[2].legend(loc='upper left')
        self.c[2].plot(self.t, self.datafile['RollingHumidityAverage'])    
        self.c[2].set_title('Humidity, rolling average')
        self.c[2].set_ylabel('Relative Humidity (%)')
        self.c[2].labelpad = 20
        self.c[2].ypad = 20
        self.c[2].legend(loc='upper left')
        self.d[2].plot(self.t, self.datafile['RollingGroundTempAverage'])
        self.d[2].set_title('Ground temperature, rolling average')
        self.d[2].set_ylabel('Ground Temperature (degC)')
        self.d[2].set_xlabel('Time')
        self.d[2].labelpad = 20
        self.d[2].legend(loc='upper left')
        self.figures[2].autofmt_xdate() 
        self.figures[2].tight_layout()
        
        
        #avgd
        self.a[1].plot(self.t, self.datafile['FluxAvg'])
        self.a[1].set_title('Flux, Raw, 4 sensors averaged')
        self.a[1].set_ylabel('Flux (W/m^2)')  
        self.a[1].labelpad = 20  
        self.a[1].legend(loc='upper left')
        self.b[1].plot(self.t, self.datafile['TempAvg'])
        self.b[1].set_title('Air Temperature, Raw, 6 sensors averaged')    
        self.b[1].set_ylabel('Temperature (degC)')
        self.b[1].labelpad = 20
        self.b[1].legend(loc='upper left')
        self.c[1].plot(self.t, self.datafile['HumidAvg'])    
        self.c[1].set_title('Humidity, Raw, 6 sensors averaged')
        self.c[1].set_ylabel('Relative Humidity (%)')
        self.c[1].labelpad = 20
        self.c[1].legend(loc='upper left')
        self.d[1].plot(self.t, self.datafile['GroundTempAvg'])
        self.d[1].set_title('Ground temperature, Raw, 4 sensors averaged')
        self.d[1].set_ylabel('Ground Temperature (degC)')
        self.d[1].set_xlabel('Time')
        self.d[1].labelpad = 20
        self.d[1].legend(loc='upper left')
        self.figures[1].autofmt_xdate()
        self.figures[1].tight_layout()
        
        #indiv
        self.a[0].plot(self.t, self.datafile['Flux1']) 
        self.a[0].plot(self.t, self.datafile['Flux2']) 
        self.a[0].plot(self.t, self.datafile['Flux3']) 
        self.a[0].plot(self.t, self.datafile['Flux4']) 
        self.a[0].set_title('Flux, individual sensor readings')
        self.a[0].set_ylabel('Flux (W/m^2)')    
        self.a[0].labelpad = 20
        self.a[0].legend(loc='upper left')
        self.b[0].plot(self.t, self.datafile['Temp1'])
        self.b[0].plot(self.t, self.datafile['Temp2'])
        self.b[0].plot(self.t, self.datafile['Temp3'])
        self.b[0].plot(self.t, self.datafile['Temp4'])
        #self.b[0].plot(self.t, self.datafile['Temp5'])
        self.b[0].plot(self.t, self.datafile['Temp6'])
        self.b[0].set_title('Air Temperature, individual sensor readings')    
        self.b[0].set_ylabel('Temperature (degC)')
        self.b[0].labelpad = 20
        self.b[0].legend(loc='upper left')
        self.c[0].plot(self.t, self.datafile['Humid1'])
        self.c[0].plot(self.t, self.datafile['Humid2'])
        self.c[0].plot(self.t, self.datafile['Humid3'])
        self.c[0].plot(self.t, self.datafile['Humid4'])
        #self.c[0].plot(self.t, self.datafile['Humid5'])
        self.c[0].plot(self.t, self.datafile['Humid6'])    
        self.c[0].set_title('Humidity, individual sensor readings')
        self.c[0].set_ylabel('Relative Humidity (%)')
        self.c[0].labelpad = 20
        self.c[0].legend(loc='upper left')
        self.d[0].plot(self.t, self.datafile['GroundTemp1'])
        self.d[0].plot(self.t, self.datafile['GroundTemp2'])
        self.d[0].plot(self.t, self.datafile['GroundTemp3'])
        self.d[0].plot(self.t, self.datafile['GroundTemp4'])
        self.d[0].set_title('Ground temperature, individual sensor readings')
        self.d[0].set_ylabel('Ground Temperature (degC)')
        self.d[0].set_xlabel('Time')
        self.d[0].labelpad = 20
        self.d[0].legend(loc='upper left')
        self.figures[0].autofmt_xdate()
        self.figures[0].tight_layout()
        
        
        
    def avg(self):
        #averaging all 4 fluxes
        self.fluxavg = self.datafile['Flux1'] + self.datafile['Flux2']+self.datafile['Flux3']+self.datafile['Flux4']
        self.fluxavg = self.fluxavg/4
        #average of all 6 temp sensors
        self.tempavg = self.datafile['Temp1'] + self.datafile['Temp2']+self.datafile['Temp3']+self.datafile['Temp4']+self.datafile['Temp5']+self.datafile['Temp6']
        self.tempavg = self.tempavg/6
        #average of all 6 humidity sensors
        self.humidavg = self.datafile['Humid1']+self.datafile['Humid2']+self.datafile['Humid3']+self.datafile['Humid4']+self.datafile['Humid5']+self.datafile['Humid6']
        self.humidavg = self.humidavg/6
        #average of all 4 ground temps from flux plates
        self.GTavg = self.datafile['GroundTemp1']+self.datafile['GroundTemp2']+self.datafile['GroundTemp3']+self.datafile['GroundTemp4']
        self.GTavg = self.GTavg/4
        self.datafile = self.datafile.assign(FluxAvg=self.fluxavg, TempAvg=self.tempavg, HumidAvg=self.humidavg, GroundTempAvg=self.GTavg)
        
    def rollingavg(self):
        try:
            self.binsize =int(self.controller.userin4)
        except:
            print('Bin size not set. setting to default:10')
            self.binsize = 10
        try:
            self.rollfluxavg = self.fluxavg.rolling(window = self.binsize, center=False).mean()
            self.rolltempavg = self.tempavg.rolling(window = self.binsize, center=False).mean()
            self.rollhumidavg = self.humidavg.rolling(window = self.binsize, center=False).mean()
            self.rollGTavg = self.GTavg.rolling(window = self.binsize, center=False).mean()
            self.rollflux1 = self.datafile['Flux1'].rolling(window = self.binsize, center=False).mean()
            self.rollflux2 = self.datafile['Flux2'].rolling(window = self.binsize, center=False).mean()
            self.rollflux3 = self.datafile['Flux3'].rolling(window = self.binsize, center=False).mean()
            self.rollflux4 = self.datafile['Flux4'].rolling(window = self.binsize, center=False).mean()
        except:
        ##python 2.7
            self.rollfluxavg = pd.rolling_mean(self.fluxavg, self.binsize)
            self.rolltempavg = pd.rolling_mean(self.tempavg, self.binsize)
            self.rollhumidavg = pd.rolling_mean(self.humidavg,self.binsize)
            self.rollGTavg = pd.rolling_mean(self.GTavg, self.binsize)
            self.rollflux1 = pd.rolling_mean(self.datafile['Flux1'], self.binsize)
            self.rollflux2 = pd.rolling_mean(self.datafile['Flux2'], self.binsize)
            self.rollflux3 = pd.rolling_mean(self.datafile['Flux3'], self.binsize)
            self.rollflux4 = pd.rolling_mean(self.datafile['Flux4'], self.binsize)
        #concatenate newly created values back to original dataframe
        self.datafile = self.datafile.assign(RollingFluxAverage=self.rollfluxavg,RollingTempAverage=self.rolltempavg,RollingHumidityAverage=self.rollhumidavg,RollingGroundTempAverage=self.rollGTavg, RollingFlux1=self.rollflux1, RollingFlux2=self.rollflux2, RollingFlux3=self.rollflux3, RollingFlux4=self.rollflux4)
    
    def stats(self):
        self.avgflux1 = self.datafile['Flux1'].mean()
        self.avgflux2 = self.datafile['Flux2'].mean()
        self.avgflux3 = self.datafile['Flux3'].mean()
        self.avgflux4 = self.datafile['Flux4'].mean()
        self.avgtemp = self.datafile['TempAvg'].mean()
        self.avghumid = self.datafile['HumidAvg'].mean()
        self.avgGT = self.datafile['GroundTempAvg'].mean()
        self.avgOF = self.datafile['FluxAvg'].mean()
        self.start = self.datafile['Timestamp'].iloc[0]
        self.end = self.datafile['Timestamp'][(self.datafile['Timestamp'].size-1)]
        h1, m1, s1 = [self.start.hour, self.start.minute, self.start.second]
        startseconds = (h1*3600) + (m1*60) + s1
        h2, m2, s2 = [self.end.hour, self.end.minute, self.end.second]
        endseconds = (h2*3600) + (m2*60) + s2
        secduration = endseconds-startseconds
        hduration = secduration//3600
        mduration = (secduration - hduration*3600)//60
        sduration = secduration%60
        self.duration = ('%s:%s:%s' % (hduration, mduration, sduration))                       
        #averages contains all the previously calculated averages (no rolling avg arrays here)
        self.averages = {'F1':self.avgflux1,'F2':self.avgflux2,'F3':self.avgflux3,'F4':self.avgflux4,'OF':self.avgOF,'T':self.avgtemp,'GT':self.avgGT,'H':self.avghumid}
        
    def peaks(self):
        self.peakInd = signal.argrelmax(self.datafile['RollingFluxAverage'].as_matrix(), order=self.binsize)
        self.peakInd2 = signal.argrelmax(self.datafile['Flux1'].as_matrix(), order=self.binsize)
        self.peakInd3 = signal.argrelmax(self.datafile['Flux2'].as_matrix(), order=self.binsize)
        self.peakInd4 = signal.argrelmax(self.datafile['Flux3'].as_matrix(), order=self.binsize)
        self.peakInd5 = signal.argrelmax(self.datafile['Flux4'].as_matrix(), order=self.binsize)
        # take indexes and extract fluxes and timestamp
        self.peakvalues = self.datafile['RollingFluxAverage'][self.peakInd[0]]
        self.peakvalues2 = self.peakvalues[self.peakvalues>self.avgOF]
        self.peakflux1 = self.datafile['Flux1'][self.peakInd2[0]]
        self.peakflux2 = self.datafile['Flux2'][self.peakInd3[0]]
        self.peakflux3 = self.datafile['Flux3'][self.peakInd4[0]]
        self.peakflux4 = self.datafile['Flux4'][self.peakInd5[0]]
        self.peakflux1times = self.datafile['Timestamp'][self.peakflux1.index.values]
        self.peakflux2times = self.datafile['Timestamp'][self.peakflux2.index.values]
        self.peakflux3times = self.datafile['Timestamp'][self.peakflux3.index.values]
        self.peakflux4times = self.datafile['Timestamp'][self.peakflux4.index.values]
        self.peaktimes = self.datafile['Timestamp'][self.peakvalues.index.values]
        self.peaktimes2 = self.datafile['Timestamp'][self.peakvalues2.index.values]
        



# In[49]:

class GUI(tk.Tk): ##passing in tk object to class GUI

    def __init__(self, *args, **kwargs): 

        self.userin = None
        self.userin2 = None
        self.userin3 = None
        self.userin4 = 1
        self.userin5 = None
        self.userin6 = None
        self.userin7 = None
        self.userin8 = None
        self.userin9 = None
        self.datafile = None
        #GUI first creates container object, which is a frame
        #-GUI creates config frame object from config class and stores it in the container, displays Open file
        #-config frame returns user input to controller object, GUI
        #-Dataview is then called for pre-processing setup.
        #-GUI object then creates post processor object, with GUI object as the parameter
        #-parameter is then used in readfile

        tk.Tk.__init__(self, *args, **kwargs) ##run the initializer again after controller destroyed for the tk object
        
        self.frames = {}
        self.container_init()
        
        for F in (config,DataView,exportwindow,StartPage, Indiv, Averaged, RollAveraged, peakdisplay, statistics, RollAveragedsingle): ##F steps through the page objects
            page_name = F.__name__ ##stores names of page objects above in page_name
            frame = F(self.container, self) #controller is what controls the frame ie 
            self.frames[page_name] = frame # this is used in show_frame
            frame.grid(row=0, column=0, sticky="nsew")##frame occupies 0,0 space in grid and expands in N-S-E-W directions
            
            if page_name == 'config':
                self.screencenter(300,150)
                self.wait_frame('config')
                tk.Tk.__init__(self, *args, **kwargs)
                self.file = readwritefile(self)
                self.container_init()
                
            if page_name == 'DataView':
                self.screencenter(1200,1000)
                #self.attributes('-fullscreen', True)
                self.wait_frame('DataView')
                tk.Tk.__init__(self, *args, **kwargs)
                self.container_init()
                self.pp = Post_processor(self)
        self.show_frame('StartPage')
    def screencenter(self, w, h):
        self.update()
        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()        
        xCent = self.screen_w/2 - w/2
        yCent = self.screen_h/2 - h/2
        self.geometry('+%d+%d' % (xCent,yCent))
    def container_init(self):
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True) 
        self.container.grid_rowconfigure(0, weight=1) 
        self.container.grid_columnconfigure(0, weight=1)
    def wait_frame(self, page_name): #used for pop up windows
        frame = self.frames[page_name]
        frame.tkraise()
        if page_name == 'config':
            usename = 'Open File'
        if page_name == 'DataView':
            usename = 'Data Viewer'
        self.title("%s" % usename)

        frame.wait_window()
        
        
    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name] ##startPage is passed first, but the other windows can be passed 
        #in later by the startpage. the name of the page is used to create the controller object and configure frame
        frame.tkraise() ##raises current frame to top
        if page_name == 'StartPage':
            usename = 'Menu'
        elif page_name == 'Indiv':
            usename = 'Individual Sensor Output'
        elif page_name == 'Averaged':
            usename = 'Averaged Sensor Output'
        elif page_name == 'RollAveraged':
            usename = 'Rolling Averages'
        elif page_name == 'statistics':
            usename = 'Experiment Statistics'
        elif page_name == 'exportwindow':
            usename = 'Export to csv'
        elif page_name == 'peakdisplay':
            usename = 'Peaks'
        else:
            usename = page_name
        self.title("%s" % usename)
        
        #config frame sets parameters for file read/write and bin size parameter



# In[50]:

class config(tk.Frame):
    
    def __init__(self, parent, controller):
        #controller is GUI object!!
        tk.Frame.__init__(self, parent)
        #controller.screencenter()
        controller.title("Open File")

        self.parent = parent
        self.controller = controller
        title = tk.Label(self, text='Post Processor', font=("Courier", 20, "bold"))
        title.grid(row=0, column = 0, columnspan = 2)
        inputframe = tk.Frame(self)
        inputframe.grid(row=1, column=0, pady=10,padx=10)
        
        label=tk.Label(inputframe, text='Enter datafile name:')
        label.grid(row=1, column=0, padx=10)
       
        self.inp = tk.Entry(inputframe)
        self.inp.grid(row=1, column=1, sticky ='nsew',padx=10)
       
        
        button = tk.Button(self, text='Continue', command= self.inputhandler)
        button.grid(row=2, column=0, columnspan=2,padx=10)
        
    def inputhandler(self): #sets the userin attributes of the GUI object (controller)
        while self.controller.userin is None:
            
            self.controller.userin = self.inp.get()
            split = self.controller.userin.split('.')
            if len(split) == 2:
                self.controller.userin = split[0]
            elif len(split) == 1:
                pass
            else:
                print('Error: invalid filename ')
        self.controller.destroy()
        


# In[51]:

class DataView(tk.Frame):
    
    def __init__(self, parent, controller):
        #controller is GUI object!!
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.datafile = controller.file.datafile
        self.datafile['Timestamp'] = self.datafile['Timestamp'].dt.time
        listboxframe = tk.Frame(self)
        listboxframe.pack(side="top",fill="both", expand=True, padx = 10, pady= 10)
        #self.t = None
        self.listbox = [x for x in range(len(self.datafile.columns))]
        self.headerbar = [x for x in range(len(self.datafile.columns))]
        
        
        self.scrollbar = tk.Scrollbar(listboxframe)
        self.scrollbar.config(command=self.yview)
        self.scrollbar.grid(row=0, column= (len(self.controller.file.datafile.columns)+1), rowspan=2, sticky='ns')
        if controller.screen_w < 1281:
            colsize = 5
            rowsize = 60
        else:
            colsize=8
            rowsize=70
        for col in range(len(self.datafile.columns)):

            self.listbox[col] = tk.Listbox(listboxframe, yscrollcommand = self.scrollbar.set, borderwidth=0)
            self.listbox[col].bind("<Button-4>", self.OnMouseWheel)
            self.listbox[col].bind("<Button-5>", self.OnMouseWheel)
            self.listbox[col].bind("<MouseWheel>", self.OnMouseWheel)
            self.listbox[col].grid(row=1, column=col, sticky='nsew')
            #self.listbox[col].grid_rowconfigure(1, weight=2)
            self.listbox[col].config(width=colsize, height=rowsize)
            header = list(self.datafile)
            self.headerbar[col] = tk.Label(listboxframe, text = ("%s" % header[col]))
            self.headerbar[col].grid(row=0, column=col, sticky = 'nsew')
            
            for row in range(len(self.datafile)-1):
                row = row+1
                item = self.datafile.iloc[row,col]
                
                self.listbox[col].insert("end", ("%s"% item))

                #Buttons and controls
                
        buttonframe = tk.Frame(self)
        buttonframe.pack(side="bottom")
        
        flipframe = tk.Frame(buttonframe)
        flipframe.pack(side="left") 
        flip1 = tk.Button(flipframe, text='Flip sign for Flux 1', command= lambda: self.fluxflip(1))
        flip1.pack()
        flip2 = tk.Button(flipframe, text='Flip sign for Flux 2', command= lambda: self.fluxflip(2))
        flip2.pack()
        flip3 = tk.Button(flipframe, text='Flip sign for Flux 3', command= lambda: self.fluxflip(3))
        flip3.pack()        
        flip4 = tk.Button(flipframe, text='Flip sign for Flux 4', command= lambda: self.fluxflip(4))
        flip4.pack()
        
        binframe = tk.Frame(buttonframe)
        binframe.pack(pady=10, side="left")
        binsizelabel = tk.Label(binframe, text = 'Bin size for rolling average:')
        binsizelabel.grid(row=0, column = 0,padx=10)
        self.binsize = tk.Entry(binframe)
        self.binsize.grid(row=0, column=1, padx=10)
        
        interpol = tk.Button(buttonframe, text='Fill NaN- Linear Interpolate', command = self.interpole)
        interpol.pack(pady=10, side="left")
        
        trimframe = tk.Frame(buttonframe)
        trimframe.pack(pady=10, side="left")
        trimlabel = tk.Label(trimframe, text='Trim rows from top')
        trimlabel.grid(row = 0, column=0, columnspan=2, pady = 5)
        self.trimrows = tk.Entry(trimframe)
        self.trimrows.grid(row=1, column=0, padx=10)
        trimbut = tk.Button(trimframe, text='Trim', command = self.trim)
        trimbut.grid(row=1, column = 1, padx=10)
        
        contin = tk.Button(buttonframe, text='Continue', command= self.closewindow)
        contin.pack(side="left")
    def trim(self):
        rows = int(self.trimrows.get())
        if rows == '':
            pass
        else:
            self.datafile.drop(self.datafile.index[0:rows], inplace=True)
            #self.t = self.datafile['Timestamp']
            for col in range(0,21):
                self.listbox[col].delete(0, 'end')
            for col in range(0,21):
                for row in range(len(self.datafile)):
                    
                    item = self.datafile.iloc[row,col]
                    self.listbox[col].insert("end", ("%s"% item))
    def OnMouseWheel(self,event):
        
        if (event.num == 4):    # Linux encodes wheel as 'buttons' 4 and 5
            delta = -1
        elif (event.num == 5):
            delta = 1
        else:                   # Windows & OSX
            delta = event.delta
        for boxes in self.listbox:
            boxes.yview("scroll", delta, "units")
        return "break"
    def yview(self, *args):
        for boxes in self.listbox:
            boxes.yview(*args)
    def interpole(self):       
        self.datafile = self.datafile.interpolate()
        print('missing values filled')
        for col in range(9,21):
            self.listbox[col].delete(0, 'end')
        for col in range(9,21):
            for row in range(len(self.datafile)):
                item = self.datafile.iloc[row,col]
                self.listbox[col].insert("end", ("%s"% item))
    def fluxflip(self, fluxch):
        if fluxch == 1:
            self.datafile['Flux1'] = -self.datafile['Flux1']
            print("flipped 1")
            self.listbox[1].delete(0, 'end')
            for row in range(len(self.datafile)):
                item = self.datafile.iloc[row,1]
                self.listbox[1].insert("end", ("%s"% item))
        elif fluxch == 2:
            self.datafile['Flux2'] = -self.datafile['Flux2']
            print("flipped 2")
            self.listbox[3].delete(0, 'end')
            for row in range(len(self.datafile)):
                item = self.datafile.iloc[row,3]
                self.listbox[3].insert("end", ("%s"% item))
        elif fluxch == 3:
            self.datafile['Flux3'] = -self.datafile['Flux3']
            print("flipped 3")
            self.listbox[5].delete(0, 'end')
            for row in range(len(self.datafile)):
                item = self.datafile.iloc[row,5]
                self.listbox[5].insert("end", ("%s"% item))
        elif fluxch == 4:
            self.datafile['Flux4'] = -self.datafile['Flux4']
            print("flipped 4")
            self.listbox[7].delete(0, 'end')
            for row in range(len(self.datafile)):
                item = self.datafile.iloc[row,7]
                self.listbox[7].insert("end", ("%s"% item))
        else:
            pass
        self.update_idletasks()

    def closewindow(self): #sets the userin attributes of the GUI object (controller)
        self.controller.userin4 = self.binsize.get()
        self.controller.datafile = self.datafile
        self.controller.destroy()



# In[52]:

class StartPage(tk.Frame): ##class startpage uses tk.frame object

    def __init__(self, parent, controller): #constructor for startpage, controller is passed in so we can use GUI's 
        self.pp = controller.pp
        tk.Frame.__init__(self, parent) #constructor for frame - because thats what startpage is. parent object
        #for the frame is the container we created earlier
        self.controller = controller ##the controller passed in in for loop above. it is (self=GUI object)
        #GUI objects hold the frames, the containers, the title font, and the show frame methods
        #the individual classes specify the details of the inside of the frames. 
        label = tk.Label(self, text='Sensor Array Post Processing') ##just a label. use controller 
        ##var to replace controller with the page name based on what is passed it
        label.pack(side="top", fill="x", pady=10) #pack label on top, fill the x dimension, give it 10pix on the yside              
     
        button1 = tk.Button(self, text='Individual Raw Sensor Readings',
                            command=lambda: controller.show_frame('Indiv')) ##this switches to page1
        #lambda functions allow you to spontaneously run the function when the button is pressed. 
        button2 = tk.Button(self, text="Averaged Sensor Readings",
                            command=lambda: controller.show_frame("Averaged")) 
        button3 = tk.Button(self, text="Rolling Averages",
                            command=lambda: controller.show_frame("RollAveraged"))##this switches to page2
        button4 = tk.Button(self, text="Rolling Average Comparison", command=lambda: controller.show_frame("RollAveragedsingle"))
        button5 = tk.Button(self, text="Experiment statistics",
                            command=lambda: controller.show_frame("statistics"))
        button6 = tk.Button(self, text="Export data as csv", command=lambda: controller.show_frame("exportwindow"))
        button7 = tk.Button(self, text="Peaks", command=lambda: controller.show_frame("peakdisplay"))
        
        button8 = tk.Button(self, text='Exit', command=lambda: controller.destroy())
        
        button1.pack() #packin buttons
        button2.pack()
        button3.pack()
        button4.pack()
        button5.pack()
        button6.pack()
        button7.pack()
        button8.pack()
        #frame is handled with grid, so no need to pack



# In[53]:

class exportwindow(tk.Frame):

    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        
        exportframe = tk.Frame(self)
        exportframe.pack()
        exportlabel = tk.Label(exportframe, text='csv export')
        exportlabel.grid(row=0, column=0, columnspan=2, pady=2)

        #controller.datafile.to_csv(path_or_buf=self.filewrite)
        self.exportentry = tk.Entry(exportframe)
        self.exportentry.grid(row=1, column=0, padx=10)
        exportbut = tk.Button(exportframe, text='Export', command = self.exporter)
        exportbut.grid(row=1, column = 1, padx=10)     
        button2 = tk.Button(self, text="Back",
                           command=lambda: controller.show_frame("StartPage"))
        button2.pack()
    def exporter(self):
        self.controller.userin3 = self.exportentry.get()
        self.controller.file.writefile()
        
        



# In[54]:

class Indiv(tk.Frame):

    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.figurenum=0
        label = tk.Label(self, text='Individual Sensor Readings')
        label.pack(side="top", fill="x", pady=10)
        
        exportframe = tk.Frame(self)
        exportframe.pack()
        exportlabel = tk.Label(exportframe, text='PDF export')
        exportlabel.grid(row=0, column=0, columnspan=2, pady=2)
        
        self.exportentry = tk.Entry(exportframe)
        self.exportentry.grid(row=1, column=0, padx=10)
        exportbut = tk.Button(exportframe, text='Export', command = self.exporter)
        exportbut.grid(row=1, column = 1, padx=10)     
        
        button2 = tk.Button(self, text="Back",
                           command=lambda: controller.show_frame("StartPage"))
        button2.pack()

        canvas = FigureCanvasTkAgg(self.pp.figures[0], master = self)
        canvas.show()
        canvas.get_tk_widget().pack(side = 'bottom', padx=10, pady=10)
    def exporter(self):
        self.controller.userin5 = self.exportentry.get()
        self.controller.pp.export(self.figurenum)
        
    


# In[55]:

class Averaged(tk.Frame):

    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.figurenum=1
        
        label = tk.Label(self, text="Averaged Sensor Readings")
        label.pack(side="top", fill="x", pady=10)
        exportframe = tk.Frame(self)
        exportframe.pack()
        exportlabel = tk.Label(exportframe, text='PDF export')
        exportlabel.grid(row=0, column=0, columnspan=2, pady=2)
        
        self.exportentry = tk.Entry(exportframe)
        self.exportentry.grid(row=1, column=0, padx=10)
        exportbut = tk.Button(exportframe, text='Export', command = self.exporter)
        exportbut.grid(row=1, column = 1, padx=10)     
        button2 = tk.Button(self, text="Back",
                           command=lambda: controller.show_frame("StartPage"))
        button2.pack()
        canvas = FigureCanvasTkAgg(self.pp.figures[self.figurenum], master = self)
        canvas.show()
        canvas.get_tk_widget().pack(side = 'bottom')
    def exporter(self):
        self.controller.userin6 = self.exportentry.get()
        self.controller.pp.export(self.figurenum)


# In[56]:

class RollAveraged(tk.Frame):

    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.figurenum = 2
        
        label = tk.Label(self, text="Rolling Averages")
        label.pack(side="top", fill="x", pady=10)
        exportframe = tk.Frame(self)
        exportframe.pack()
        exportlabel = tk.Label(exportframe, text='PDF export')
        exportlabel.grid(row=0, column=0, columnspan=2, pady=2)
        
        self.exportentry = tk.Entry(exportframe)
        self.exportentry.grid(row=1, column=0, padx=10)
        exportbut = tk.Button(exportframe, text='Export', command = self.exporter)
        exportbut.grid(row=1, column = 1, padx=10)  
        button2 = tk.Button(self, text="Back",
                           command=lambda: controller.show_frame("StartPage"))
        button2.pack()
        canvas = FigureCanvasTkAgg(self.pp.figures[self.figurenum], master = self)
        canvas.show()
        canvas.get_tk_widget().pack(side = 'bottom')
    def exporter(self):
        self.controller.userin7 = self.exportentry.get()
        self.controller.pp.export(self.figurenum)
        


# In[57]:

class RollAveragedsingle(tk.Frame):

    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.figurenum=3
        
        label = tk.Label(self, text="Rolling Averages")
        label.pack(side="top", fill="x", pady=10)
        exportframe = tk.Frame(self)
        exportframe.pack()
        exportlabel = tk.Label(exportframe, text='PDF export')
        exportlabel.grid(row=0, column=0, columnspan=2, pady=2)
        
        self.exportentry = tk.Entry(exportframe)
        self.exportentry.grid(row=1, column=0, padx=10)
        exportbut = tk.Button(exportframe, text='Export', command = self.exporter)
        exportbut.grid(row=1, column = 1, padx=10)  
        button2 = tk.Button(self, text="Back",
                           command=lambda: controller.show_frame("StartPage"))
        button2.pack()
        #button3 = tk.Button(self, text = "add plot2 to plot1", command self.figurechange(3, 1))
        #button3.pack()
        canvas = FigureCanvasTkAgg(self.pp.figures[self.figurenum], master = self)
        canvas.show()
        canvas.get_tk_widget().pack(side = 'bottom')
    def exporter(self):
        self.controller.userin9 = self.exportentry.get()
        self.controller.pp.export(self.figurenum)
    #def figurechange(self, fig, subfig):
        
        


# In[58]:

class peakdisplay(tk.Frame):
    
    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller=controller
        self.figurenum = 4
        
        controlframe = tk.Frame(self)
        controlframe.pack(side="top")
        label = tk.Label(controlframe, text="Peak finder")
        label.pack(side="left", pady=10)
        
        canvas = FigureCanvasTkAgg(self.pp.figures[self.figurenum], master = self)
        canvas.show()
        canvas.get_tk_widget().pack(side = 'bottom')
        exportframe = tk.Frame(controlframe)
        exportframe.pack()
        exportlabel = tk.Label(exportframe, text='PDF export')
        exportlabel.grid(row=0, column=0, columnspan=2, pady=2)
        
        self.exportentry = tk.Entry(exportframe)
        self.exportentry.grid(row=1, column=0, padx=10)
        exportbut = tk.Button(exportframe, text='Export', command = self.exporter)
        exportbut.grid(row=1, column = 1, padx=10) 
        
        button2 = tk.Button(controlframe, text="Back", command=lambda: controller.show_frame("StartPage"))
        button2.pack()
    def exporter(self):
        self.controller.userin8 = self.exportentry.get()
        self.controller.pp.export(self.figurenum)
    


# In[59]:

class statistics(tk.Frame):

    def __init__(self, parent, controller):
        
        self.pp = controller.pp
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label1 = tk.Label(self, text="Statistics")
        label1.pack(side="top", fill="x", pady=10)
        label7 = tk.Label(self, text=('Experiment Start Time: %s' % self.pp.start))
        label7.pack(fill= "x", pady = 5)        
        label2 = tk.Label(self, text=("Experiment Duration: %s" % self.pp.duration))
        label2.pack(fill="x", pady=5)
        label3 = tk.Label(self, text=("Average Overall Flux: %s W/m^2" % self.pp.avgOF))
        label3.pack(fill="x", pady=5)
        label4 = tk.Label(self, text=("Average Temperature: %s degC" % self.pp.avgtemp))
        label4.pack(fill="x", pady=5)
        label5 = tk.Label(self, text=("Average Humidity: %s perRH" % self.pp.avghumid))
        label5.pack(fill="x", pady=5)
        label6 = tk.Label(self, text=("Average Ground Temperature: %s degC" % self.pp.avgGT))
        label6.pack(fill="x", pady=5) 
        
        button = tk.Button(self, text="Back",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()



# In[60]:

if __name__ == "__main__":
    
        app = GUI()
        app.mainloop()

