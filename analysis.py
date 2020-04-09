import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import socket
import os
from datetime import datetime
from matplotlib import colors
import matplotlib as mpl
from matplotlib.transforms import Bbox

class corvidData:

    def __init__(self,online=True):
        self.online = online
        if(corvidData.isConnected() and self.online):
            print("downloading data from: https://covid.ourworldindata.org/data/ecdc/")
            corvidData.getData(self)
        else:
            print("Searching for local data files...")
            corvidData.findFile(['cases.csv','deaths.csv'])
            path_cases = "cases.csv"
            path_deaths = "deaths.csv"
            self.cases = pd.read_csv(path_cases,sep=',')
            self.deaths = pd.read_csv(path_deaths,sep=',')
        self.cases.fillna(0, inplace=True)
        self.deaths.fillna(0, inplace=True)

    def isConnected():
        try:
            # connect to the host -- tells us if the host is actually
            # reachable
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            print("Warning: connection error, unable to download data")
        return False

    def findFile(name):
        cur_dir = os.getcwd()
        counter = 0
        for root, dirs, files in os.walk(cur_dir):
            for n in name:
                if n in files:
                    counter += 1
        if(counter < 2):
            print("Warning: no data files found in local Directory")
            exit()
        else:
            print("Found data files: using local data")

    def location(self,where):
        self.where = where

    def getData(self):
        url_deaths = "https://covid.ourworldindata.org/data/ecdc/new_deaths.csv"
        url_cases = "https://covid.ourworldindata.org/data/ecdc/new_cases.csv"
        d = requests.get(url_deaths, allow_redirects=True)
        c = requests.get(url_cases, allow_redirects=True)

        open('cases.csv', 'wb').write(c.content)
        open('deaths.csv', 'wb').write(d.content)

        path_cases = "cases.csv"
        path_deaths = "deaths.csv"
        self.cases = pd.read_csv(path_cases,sep=',')
        self.deaths = pd.read_csv(path_deaths,sep=',')

    def cumulative(self,loc):
        self.cumul_cases = np.zeros((self.nDates))
        self.cumul_deaths = np.zeros((self.nDates))
        for i in range(1,self.nDates):
            self.cumul_cases[i] = self.cumul_cases[i-1] + self.cases[loc][i]
            self.cumul_deaths[i]  = self.cumul_deaths[i-1] + self.deaths[loc][i]

    def fatilityRate(self):
        self.fatility_rate = np.zeros((self.nDates))
        for i in range(self.nDates):
            if((self.cumul_cases[i] != 0) or (self.cumul_deaths[i] != 0)):
                self.fatility_rate[i] = 100*self.cumul_deaths[i]/self.cumul_cases[i]
            else:
                if(i == 0):
                    self.fatility_rate[i] = 0.0
                else:
                    self.fatility_rate[i] = self.fatility_rate[i-1]

    def plotData(self):
        self.nDates = len(self.cases['date'])
        corvidData.cumulative(self,self.where)
        corvidData.fatilityRate(self)

        fig, ax = plt.subplots(3,sharex=True)
        ax[0].set_title(self.where)
        ax[0].plot(self.cases['date'],self.cases[self.where],'b-x',linewidth=1,markersize=2,label='cases')
        ax[0].plot(self.deaths['date'],self.deaths[self.where],'r-x',linewidth=1,markersize=2,label='deaths')
        ax[0].set_ylabel('Reported Cases')
        # ax[0].set_yscale('log')
        ax[0].legend()


        ax[1].plot(self.cases['date'], self.cumul_cases,'b-+',linewidth=1,markersize=2,label='cases')
        ax[1].plot(self.cases['date'], self.cumul_deaths,'r-+',linewidth=1,markersize=2,label='Deaths')
        # ax[1].set_yscale('log')
        ax[1].legend()
        ax[1].set_ylabel('Cumulative Cases')

        ax[2].plot(self.cases['date'],self.fatility_rate)
        ax[2].set_xlabel('Date')
        ax[2].set_ylabel('fatality Rate [%]')
        ax[2].tick_params(axis='x', rotation=90)
        plt.show()

class corvidModel:
    def __init__(self, data, recovery):
        self.data = data
        self.recP = recovery
        self.time = corvidModel.dateToDays(self.data.cases['date'])

    def cumulative(self, data):
        output = np.zeros((len(data)))
        for i in range(1,len(data)):
            output[i] = output[i-1] + data[i]
        return output.astype(int)

    def dateToDays(dates):
        t = []
        count = 0
        for date in dates:
            t.append(datetime(int(date.split('-')[0]),int(date.split('-')[1]),int(date.split('-')[2])))

        times = np.zeros((len(t)))
        count = 0
        for i in range(len(t)):
            times[i] = (t[count] - t[0]).days
            count += 1
        return times

    def identifyFirst(self, data):
        for i in range(len(data)):
            if(data[i] > 0.0):
                if (i == 0):
                    return i
                else:
                    return i-1 #start on day of zero cases before any trend
        return len(data)-1 #if no cases return end of data array for that country

    def histogramPeak(self,threshold_cases,threshold_deaths):

        bin_cases = []
        bin_deaths = []
        maximum_cases = []
        maximum_deaths = []

        for country in self.data.cases.columns.values:
            if((country != 'World') and (country != 'date')):
                cumul_deaths = corvidModel.cumulative(self,self.data.deaths[country].values)
                cumul_cases = corvidModel.cumulative(self,self.data.cases[country].values)
                for i in range(len(cumul_cases)):
                    if(cumul_cases[i] >= threshold_cases):
                        maximum_cases.append(cumul_cases.max())
                        bin_cases.append(self.time[i])
                        break
                for i in range(len(cumul_deaths)):
                    if(cumul_deaths[i] >= threshold_deaths):
                        maximum_deaths.append(cumul_deaths.max())
                        bin_deaths.append(self.time[i])
                        break


        cmap = plt.cm.jet  # define the colormap
        # extract all colors from the .jet map
        cmaplist = [cmap(i) for i in range(cmap.N)]
        # force the first color entry to be grey
        cmaplist[0] = (.5, .5, .5, 1.0)

        # create the new map
        cmap = mpl.colors.LinearSegmentedColormap.from_list(
            'Custom cmap', cmaplist, cmap.N)

        # define the bins and normalize
        bounds = np.linspace(0, 10, 11)
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)


        fig, ax = plt.subplots(2,2,tight_layout=True)
        hist_cases = ax[0][0].hist2d(bin_cases,maximum_cases,bins=(len(bin_cases),
                                    len(maximum_cases)),
                                    norm=norm,
                                    cmap=cmap)
        plt.colorbar(hist_cases[3],ax=ax[0][0],
                                label='# Countries',
                                cmap=cmap, boundaries=bounds,
                                norm=norm, orientation='horizontal',
                                ticks=bounds,
                                format='%1i')
        ax[0][0].set_title("Case Threshold {}".format(threshold_cases))
        ax[0][0].set_xlabel("Time since 1st reported case [day]")
        ax[0][0].set_ylabel("Maximum number of cases")

        hist_deaths = ax[0][1].hist2d(bin_deaths,maximum_deaths,bins=(len(bin_deaths),
                                    len(maximum_deaths)),
                                    norm=norm,
                                    cmap=cmap)
        plt.colorbar(hist_deaths[3],ax=ax[0][1],
                                label='# Countries',
                                cmap=cmap, boundaries=bounds,
                                norm=norm, orientation='horizontal',
                                ticks=bounds,
                                format='%1i')
        ax[0][1].set_title("Death Threshold {}".format(threshold_deaths))
        ax[0][1].set_xlabel("Time since 1st reported death [day]")
        ax[0][1].set_ylabel("Maximum number of Deaths")



        for country in self.data.cases.columns.values:
            if((country != 'World') and (country != 'date')):
                start = corvidModel.identifyFirst(self, self.data.cases[country])
                cumul = corvidModel.cumulative(self,self.data.cases[country][start:].values)
                sc1, = ax[1][0].plot(cumul,label=country)
        ax[1][0].set_ylabel("Total Cases")
        ax[1][0].set_xlabel("Days since 1st Case")
        for country in self.data.deaths.columns.values:
            if((country != 'World') and (country != 'date')):
                start = corvidModel.identifyFirst(self, self.data.deaths[country])
                cumul = corvidModel.cumulative(self,self.data.deaths[country][start:].values)
                ax[1][1].plot(cumul,label=country)
        ax[1][1].set_ylabel("Total Deaths")
        ax[1][1].set_xlabel("Days since 1st Death")


        d = {"down" : 200, "up" : -200}
        def scroll(evt):
            if legend.contains(evt):
                bbox = legend.get_bbox_to_anchor()
                bbox = Bbox.from_bounds(bbox.x0, bbox.y0+d[evt.button], bbox.width, bbox.height)
                tr = legend.axes.transAxes.inverted()
                legend.set_bbox_to_anchor(bbox.transformed(tr))
                fig.canvas.draw_idle()


        def line_hover(event):
            for line in ax[1][0].get_lines():
                if line.contains(event)[0]:
                    print(line.get_label())
            for line in ax[1][1].get_lines():
                if line.contains(event)[0]:
                    print(line.get_label())

        fig.canvas.mpl_connect('motion_notify_event', line_hover)
        plt.show()

    def currentCases(self,country):
        length = len(self.data.cases[country])
        inC = self.data.cases[country].values
        outC = self.data.deaths[country].values
        currentC = np.zeros((length))
        for i in range(self.recP,length):
            outC[i] = outC[i] + inC[i-self.recP]
        totalC = corvidModel.cumulative(self, self.data.cases[country].values)

        for i in range(1,length):
            currentC[i] = currentC[i-1] + inC[i] - outC[i]

        plt.plot(self.time,totalC,'r-',label="total Case")
        plt.plot(self.time,currentC,'b--',label="Total Current Cases")
        plt.title(country)
        plt.xlabel("Time [d]")
        plt.ylabel("Cases")
        plt.legend()
        plt.show()







where = "United Kingdom"
data = corvidData(True)
data.location(where)
data.plotData()
model = corvidModel(data,14)
model.histogramPeak(2000.0,100.)
model.currentCases(where)
