# force-steadiness

This Python script is used to take uncorrected isometric force-time data, calibrate the file, filter and offset-correct, and then calculate the coefficient of variation of the force over specified intervals of time. 

## Step 1: Identify files used for analysis

The import_list function accepts two strings as input, one defining a relative path and another defining the folder containing files of interest, and returns a list of all file paths meeting criteria contained within the folder. Returns the list of file paths as an output.

## Step 2: Import calibration data

The cal_file_import function accepts a string as an input, which should be a file path to a calibration file containing two columns of data: one column of voltage values collected from a load cell, and another column containing the corresponding loads (in Newtons) producing those voltages. Returns values as a dataframe. 

## Step 3: Import force-time curve

The file_import function accepts a string as an input, which should be a file path to the force file used for analysis (this will often be one of the values in the list output from step 1). Returns the raw force-time curve as well as the trace used for visual feedback to subjects as a dataframe. 

## Step 4: Convert force-time curve to Newtons

The force_file_conversion function accepts two dataframes and one float value as an input to calibrate the force data and convert the trace to the correct relative units. The dataframes should be the raw force-time curve and the calibration data created in steps 2 and 3. The mvic_newtons argument should be the subject's maximal voluntary isometric force expressed in Newtons. 

This function will take the force-time curve and use the above-defined lowpass_filter function to apply a 4th order, low-pass Butterworth filter with a default cutoff frequency of 15 Hz to the raw force-time curve. Data are then converted to Newtons by fitting a linear regression model to the calibration data and predicting values in the force data. The visual feedback trace is then converted from a percentage value to a force value in Newtons based on the mvic_newtons value. The output is returned as a dataframe of the converted values. 

## Step 5: Calculate force steadiness

The force_steadiness function accepts one dataframe and two float values as inputs to calculate the coefficient of variation of the force signal. start_time and end_time should specify the beginning and end of the calculation window, respectively. These values are often assessed by plotting the values using the plot_data function, but can also be default values. The CV is calculated as a percentage and returned as an integer value. 

## Additional optional functions

The plot_data function is an optional function that will plot the force-time curve against the visual feedback trace to assess how well force was matched. 

The final_analysis_code function is an optional function that can be used for batch processing. Three strings are accepted as inputs: "paths" is a file path to the folder of files to be used for analysis, "input_path" is a file path to a csv file containing start and end times for each file, and "cal_path" is a file path to the calibration file used to convert the force-time curves. Files in the paths folder are iterated over, calculating CV values for each files that are then appended to a list. At the end of the for loop, the list is converted to a formatted dataframe that can be exported as a csv for further analysis. 
