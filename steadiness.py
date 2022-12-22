# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 12:37:37 2022

@author: ncoker
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.signal import butter,filtfilt


def import_list(base_path, folder): #Defines function for batch-importing submaximal ramp files in subdirectory
    '''
    Parameters
    -----------
    base_path: string
        file path to where data is generally stored
    folder: string
        relative path to specific subject folder where actual data files are 
        stored.
        
    Returns
    -----------
    paths: Path object
        returns list of all submaximal trapezoid file names in the folder 
        specified.
    '''
    paths = [path for path in Path(base_path + folder).resolve().glob('**/*%_MVIC_*.csv*')] # Creates variable path, which stores file paths for all submaximal ramp files contained in subdirectory
    return paths

def cal_file_import(cal_filename): # Defines function for importing load cell calibration file
    '''

    Parameters
    ----------
    cal_filename : string
        file path where load cell calibration is stored.

    Returns
    -------
    cal_data : DataFrame
        returns calibration file that will be used to convert MVIC to newtons.

    '''
    cal_data = pd.read_csv(cal_filename,sep = ',',names=['volts','force'],header=0) #Reads load cell calibration file and stores as dataframe
    return cal_data

def file_import(filename): #Defines function for importing force-time curve from submaximal contractions
    '''
    Parameters
    ----------
    filename : string
        Full file path, usually taken from the output of import_list.
    mvic_volts : float
        MVIC in volts. If "active offset" is used, should just be 
    MVIC + offset.if "quiet offset" is used, should be MVIC + (offset*2).
    offset_volts : float
        Offset in volts. If active offset used, should be whatever offset 
        shown on a plot. If quiet offset used, should be the quiet offset.

    Returns
    -------
    data : DataFrame
        Returns a pandas dataframe of the force output and the trace trajectory.

    '''
    data = pd.read_csv(filename,sep='\t',usecols=[8,9,10,11],names=['time','force','trace_time','trace'],header=0) # from submaximal ramp file, import timing info, force, and the force trace used for visual feedback
    offset_volts = data.loc[100:4444,'force'].mean() # Calculate offset value for force data based on average force over first two seconds
    data['force_corrected'] = data['force'] - offset_volts #Offset-correct force based on calculated offset
    return data
 
def lowpass_filter(force_data, samplefreq = 2222, order = 4, cutoff = 15): # Define function for filtering force data with 4th order, low-pass Butterworth filter (15Hz cutoff)
    nyquist = samplefreq * 0.5 #Calculates Nyquist frequency
    cut = cutoff / nyquist # Calculates cutoff frequency relative to Nyquist frequency
    b,a = butter(order,cut,'lowpass',analog=False) #Calculate Butterworth coefficients based on provided inputs
    if 'force_corrected' in force_data.columns: #Define process for filtering offset-corrected data
        force_data['filtered'] = filtfilt(b,a,force_data['force_corrected']) # Create column of filtered data based on offset-corrected raw force
    else: #Define process for filtering raw uncorrected force data
        force_data['filtered'] = filtfilt(b,a,force_data['force']) #Create column of filtered data based on uncorrected raw force
    return force_data

def force_file_conversion(force_data,cal_data,mvic_newtons): #Define function for converting uncorrected force in Volts to filtered force in Newtons
    '''
    Parameters
    ----------
    force_data : DataFrame
        force-time curve expressed in volts.
    cal_data : DataFrame
        calibration dataframe consisting of input voltages and weights in N.

    Returns
    -------
    force_data : dataFrame
        Predicts Force values in Newtons using linear regression applied to 
        cal file.

    '''
    force_data = lowpass_filter(force_data) # Filter force data
    calibration = LinearRegression() #Create linear regression to use in converting force from volts to newtons
    calibration.fit(cal_data['volts'].to_numpy().reshape(-1,1),cal_data['force'].to_numpy().reshape(-1,1)) #Fit linear regression based on volts and force outputs form load cell calibration file
    force_data['force_newtons'] = calibration.predict(force_data['filtered'].to_numpy().reshape(-1,1)) #Based on fitted regression, predict force values during submaximal ramp contraction
    force_data['trace_converted'] = (force_data['trace'] / 100) * mvic_newtons # Convert force trace to values expressed relative to observed force
    return force_data
           
def force_steadiness(data,start_time,end_time,samplefreq=2222): #Define function for calculating force steadiness within specific time window
    '''
    Parameters
    ------------
    data: DataFrame
        dataframe of force-time curve during submaximal contractions
    samplefreq: int
        sampling frequency of equipment in Hz (Delsys default is 2222)
    start_time: float
        Time where subject was able to match the target template, as confirmed 
        visually. 
    end_time: float
        End of interval over which steadiness will be calculated. Typically use 
        5 seconds for 30% and 3 seconds for 70%
        
    Returns
    ------------
    cv: float
        coefficient of variation of the force-time signal from start_time to 
        end_time. 
    '''
    start_index = data.time.searchsorted(start_time,side='left') # Store index corresponding to time value identified in start_time
    end_index = data.time.searchsorted(end_time,side='left') #Store index corresponding to time value identified in end_time
    mean = data.loc[start_index:end_index,'force_newtons'].mean() #Mean of corrected force value over interval between start time and end time
    sd = data.loc[start_index:end_index,'force_newtons'].std() # SD of corrected force value over interval between start time and end time
    cv = (sd/mean)*100 # Calculate coefficient of variation based on Mean and SD outlined above
    return cv

def plot_data(data): #Defines function for standardized data results plotting
    plt.plot(data['time'],data['force_newtons'],label='force') # Plot force-time curve from submax contraction
    plt.plot(data['trace_time'],data['trace_converted'],label='trace') # Plot trace used for visual feedback
    plt.xlabel('Time (s)') # Label x-axis
    plt.ylabel('Force (N)') # Label y-axis
    plt.legend() #Generate legend

def final_analysis_code(paths,input_path,cal_path): # Define function for batch processing of multiple files within subdirectory if other inputs are already determined
    cal_data = cal_file_import(cal_path) #import cal data from load cell calibration .csv file
    frame = [] # Initiate empty list for writing results info
    inputs = pd.read_csv(input_path) #Read file that will provide inputs for steadiness calculation (time to match, ttm_end, and mvic_newtons)
    for i in range(len(paths)):
        mvic_newtons = inputs.loc[i,'mvic_newtons'] # Read input data and store MVIC value in newtons
        data = file_import(paths[i]) # import force-time curve contained in file "i"
        data = force_file_conversion(data,cal_data,mvic_newtons) # Convert force-time curve to filtered data expressed in newtons
        time_to_match = inputs.loc[i,'ttm'] # Read input data and store time_to_match value 
        ttm_end = inputs.loc[i,'ttm_end'] #Read input data and store end of calculation window
        cv = force_steadiness(data,time_to_match,ttm_end) #Calculate force steadiness over window defined by ttm, ttm_end
        frame.append([inputs.loc[i,'subject'],paths[i],time_to_match,ttm_end,cv]) # Append list to include subject number, file path, timing window values, and 
    df = pd.DataFrame(frame,columns = ['subject', # convert list to dataframe which will be saved as a .csv for final data analysis
                                       'filename',
                                       'ttm',
                                       'ttm_end',
                                       'cv'])
    return df