import requests
from collections import Iterable
import multiprocessing
from datetime import datetime, timezone
from bz2 import decompress
import xarray as xr
import pandas as pd
import os
import glob
from pathlib import Path



class ICON_D2:

    '''Class to retrieve ICON D2 data from opendata.dwd.de.
    The data is extracted from a nwp gribfile
    
    Parameters
    ----------
    location : dict
        lat, lon in geographic coordinates as a dict. coords = {"lat": 47, "lon": 15}
    forecastHours : int
        The forecast hours for which the data is collected
    tmpFp : string
        The filepath to a folder where temporary files will be stored. This 
        is needed to extract data from grib2 files because with the used 
        libraries (eccodes, cfgrib) it is not possible to store the downloaded 
        grib files in memory (see https://github.com/ecmwf/cfgrib/issues/99 or 
                              https://github.com/ecmwf/eccodes-python/issues/25).
        If no path is given a default directory "tmp/icond2/" will be created.
    '''   

    def __init__(self, location, forecastHours, tmpFp = None):
        
        if tmpFp is None:
            
            p = "tmp/icond2/"
            
            self._tmpFp = p
            
            if not os.path.exists(p):
                os.makedirs(p)
            
        else:
            self._forecastHours = tmpFp
        
        self._forecastHours = forecastHours
        
        self._location = {
            "lat": location["lat"],
            "lon": location["lon"]
        }
    
        self._src = "https://opendata.dwd.de/weather/nwp/icon-d2/grib/"
    
    @property
    def location(self):
        return self._location    
    
    @property
    def forecastHours(self, value):
        return self._forecastHours    

    
    def getCurrentRun(self, now_utc):
        
        '''Gets the number of the current run by current time. 
        The latest run is fully available ~2h after initialisation.
        e.g. The 09 run will be finished at approx 11:00 UTC.
        
        Parameters
        ----------
        now_utc : datetime
            The current datetime
            
        Returns
        -------
        string
            The run hour as a string (00, 03, 06 ...)
        '''
        
        h = now_utc.hour
        run_hour = "00"
        
        if h >= 2:
            run_hour = "00"        
        if h >= 5:
            run_hour = "03"
        if h >= 8:
            run_hour = "06"        
        if h >= 11:
            run_hour = "09"
        if h >= 14:
            run_hour = "12"
        if h >= 17:
            run_hour = "15"
        if h >= 20:
            run_hour = "18"            
        if h >= 23 and h < 2:
            run_hour = "21"
            
        return run_hour
    
            
    def createDownloadUrl(self, var):

        '''Creates the download urls
        
        Parameters
        ----------
        var : string
            The variable name
            
        Returns
        -------
        list
            List with urls
        '''
        
        urls = []
        now_utc = datetime.now(timezone.utc)
        currentRun = self.getCurrentRun(now_utc)
        
        urlDate = now_utc.strftime("%Y%m%d") 
        

        url = "{src}{run}/{var}".format(src = self._src, var = var, run = currentRun) 
        
        hours = self._forecastHours
        
        if self._forecastHours is None:
            hours = 49
        
        for h in range(hours):
            
            hStr = str(h).zfill(2)
            fileName = "icon-d2_germany_regular-lat-lon_single-level_{ds}{run}_0{h}_2d_{var}.grib2.bz2".format(h = hStr,
                                                                                                      run = currentRun,
                                                                                                      var = var,
                                                                                                      ds = urlDate)
            filePath = "{url}/{fn}".format(url = url, fn = fileName) 
            
            urls.append(filePath)
    
        return urls
    
    
    def downloadAndExtractBzFile(self, url, destFp):

        '''Downloads the file from an url und extracts the content.
        
        Parameters
        ----------
        url : string
            The url for the file to download
        destFp : string 
            The path to save the file. Should be a tmp path.
        '''
        
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(destFp, 'wb') as f:
                    f.write(decompress(r.content))
                
        except Exception as err:
            print("Could not get {url}: {err}".format(err = err, url = url))        



    def extractValuesFromGrib(self, fp, ncVarName, data):
        
        '''Extract the value from the grib file for the location.
        
        Parameters
        ----------
        fp : string
            The filepath to the netCDF file
        ncVarName : string 
            The variable name inside the nc file.
        data : pd.Series
            The series is given by reference and will be filled
            iteratively.
        '''   
        
        ncFile = xr.open_dataset(fp, engine='cfgrib')
        stepValues = ncFile.step.values
        hasStepIndex = True
        
        if not isinstance(stepValues, Iterable):
            stepValues = [stepValues]
            hasStepIndex = False
            
            
        for step in stepValues:
            
            lat = self.location["lat"]
            lon = self.location["lon"] 
            
            
            if hasStepIndex is True:
                nearestPointVal = ncFile.sel(step = step,
                                             latitude=lat, 
                                             longitude=lon, 
                                             method="nearest")[ncVarName].values
            else:
                nearestPointVal = ncFile.sel(latitude=lat, 
                                             longitude=lon, 
                                             method="nearest")[ncVarName].values
                
            dt = ncFile.time.values + step
            
            data.loc[dt] = nearestPointVal
            
        os.remove(fp)
    
    
    def mainDataCollector(self, iterItem):

        '''Collects the data for all timesteps for one variable
        
        Parameters
        ----------
        iterItem : tuple
            Tuple with variable key and variable value
 
        Returns
        -------
        pd.Series
            The collected data
        '''
        
        data = pd.Series()        
        varKey = iterItem[0]
        varValues = iterItem[1] 
        
        urls = self.createDownloadUrl(varKey) # url for one variable
        
        for url in urls:
    
            print("ICON data -> Processing file: {f}".format(f = url))                
    
            tmpfn = os.path.basename(url) # tmp file name
            tmpfn = Path(tmpfn).with_suffix('')
            tmpfp = "{p}/{tmpfn}".format(tmpfn = tmpfn, p = self._tmpFp) # tmp file path
            
            # Download the zip file and save it temporarely
            self.downloadAndExtractBzFile(url, tmpfp)
            
            # Extract values from grib file
            try:
                self.extractValuesFromGrib(tmpfp, varValues["ncInternVarName"], data)
            except Exception as err:
                print("ERROR Can't extract values from grib file: {e}".format(e = err))
        
        result = {
           varKey: data 
        }        
        
        return result
    
    
    
    def collectData(self, varList, cores = None):
        
        '''Collect the whole data. Will take a bit more time 
        because every grib file has to be downloaded, extracted 
        and opened seperately.
        
        Parameters
        ----------
        varList : dict
            A dict with variables to collect data.
            (e.g. "aswdir_s": { "ncInternVarName": "ASWDIR_S" })
            
            .. highlight:: python
            .. code-block:: python
                iconVariablesToLoad = {
                    "aswdir_s": { # the key is the subdirectory name to the variable in the ftp storage
                        "ncInternVarName": "ASWDIR_S" # the value is the defined variable name  in the netCDF file
                    },
                    "aswdifd_s": {
                        "ncInternVarName": "ASWDIFD_S"
                    },
                    "t_2m": {
                        "ncInternVarName": "t2m"
                    }  
                }
        cores : int
            Number of cores to use. Default value is None. So no 
            multiprocessing is applied. On some windows machines 
            multiprocessing is problematic.
 
        Returns
        -------
        pd.DataFrame
            The data as an dataframe
        ''' 
    
        data = pd.DataFrame()
    
        if cores is None:
            
            result = []
            
            for item in varList.items():
                res = self.mainDataCollector(item)  
                result.append(res)
              
        else:
            # Parallel processing of downloading and extracting grib data
            pool = multiprocessing.Pool()
            result = pool.map(self.mainDataCollector, varList.items())
            pool.close()

        # Collect thte data
        for res in result:
            
            key = list(res.items())[0][0]
            val = list(res.items())[0][1] 
            
            data[key] = val

        # Remove all .idx files in the tmp folder
        path = "{tfp}/*grib*".format(tfp = self._tmpFp)
        fileList = glob.glob(path)

        for filePath in fileList:
            try:
                os.remove(filePath)
            except:
                print("Error while deleting file : ", filePath)
        
        data.index = data.index.tz_localize("UTC")    
        
        return data        
        


