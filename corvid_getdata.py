import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import socket
import os
from datetime import datetime

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

data = corvidData()
data.location("Singapore")
data.plotData()
