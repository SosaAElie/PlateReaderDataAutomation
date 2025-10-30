from Classes.ExcelWrapper import ExcelWrapper
from Classes.Sample import Sample
from typing import Callable
import statistics
import math
import os
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import scipy.optimize
import numpy as np
from PIL import Image
import io


async def main(data_filepath:str, template_filepath:str, destination:str, regression_type:str = "linear", make_excel:bool = False, graph_title:str = "")->None:
    
    '''User selects whether the samples were run in duplicates or triplicates. The average of the replicates of the samples, standards and any controls are calculated, using
        linear regression the concentration of the samples is determined from the slope of the linear regression calculated from the standards.
        Assumes the standards are always on the right hand side of the plate and the IgG isotype control is on the bottom of the standards, the rest of the wells contain samples.
        Assumes the highest concentration of the standard is 1 ug/mL and the dilution factor is 2x by default
    '''
    
    ewrapper = ExcelWrapper(data_filepath)
    regression = ""
    if regression_type == "Linear":
        regression = "-Linear-"
    elif regression_type == "Logarithmic":
        regression = "-Logarithmic-"
    elif regression_type == "5PL":
        regression = "-5PL-"
    
    new_dest = '/'.join([destination,data_filepath.replace(".txt", f"{regression}.xlsx").split('/')[-1]])
    
    plate = ewrapper.get_matrix(top_offset=3, left_offset=3, width=12, height=8, val_only=True)
    template = ExcelWrapper(template_filepath).get_matrix(top_offset=2, left_offset=2, width = 12, height=8, val_only=True)
    samples, standards, units = merge_plate_template(plate, template)
    
    if regression_type == "Linear":
        inverse_equation,equation, extra_info = get_linear_regression_function([standard.ab_concentration for standard in standards if standard.sample_type == "standard"], [standard.average for standard in standards if standard.sample_type == "standard"])
    elif regression_type == "Logarithmic":
        inverse_equation, equation, extra_info = get_logarithmic_regression_function([standard.ab_concentration for standard in standards if standard.sample_type == "standard"], [standard.average for standard in standards if standard.sample_type == "standard"])
    elif regression_type == "5PL":
        inverse_equation, equation, extra_info  = get_five_parameter_logistic_curve([standard.ab_concentration for standard in standards if standard.sample_type == "standard"], [standard.average for standard in standards if standard.sample_type == "standard"])
       
    for sample in samples:
        diff = []
        for standard in standards:
            if standard.sample_type == "standard":
                diff.append(abs(sample.average - standard.average))
        
        sample.closest_conc = standards[diff.index(min(diff))].ab_concentration
        
    
    if regression_type == "5PL":
        for standard in standards: standard.calculated_ab = inverse_equation(standard.average, standard.ab_concentration)
            
        for sample in samples: sample.calculated_ab = inverse_equation(sample.average, sample.closest_conc)
    else:
        for standard in standards: standard.calculated_ab = inverse_equation(standard.average)
            
        for sample in samples: sample.calculated_ab = inverse_equation(sample.average)
    
    figure = regression_plot(equation,[standard for standard in standards if standard.sample_type == "standard"], samples, extra_info, units, regression_type, figure_name = new_dest.split("/")[-1] if graph_title == "" else graph_title)
    
    if make_excel:
        ewrapper.save_image(figure, f"A{ewrapper.get_last_row()}")
        write_to_excel(ewrapper, samples, standards, extra_info=extra_info)
        ewrapper.write_excel(new_dest)
        os.system(f'start excel "{new_dest}"')

def write_to_excel(ewrapper:ExcelWrapper, samples:list[Sample], standards:list[Sample], extra_info:list[float]|float = None)->None: 
    '''Writes the label, values, average(std), ab_concentration stored in the Sample instance horizontally'''
    sample_headers = ["Samples"]
    standard_headers = ["Standards"]

    sample_wells = max([len(sample.values) for sample in samples])
    standard_wells = max([len(standard.values) for standard in standards])

    for num in range(1, sample_wells+1):sample_headers.append(f"Well {num}")
    for num in range(1, standard_wells+1):standard_headers.append(f"Well {num}")
    sample_headers.append("OD Average (std)")
    sample_headers.append("Calculated Ab")
    standard_headers.append("OD Average (std)")
    standard_headers.append("Calculated Ab")

    sample_data_length = len(sample_headers)
    standard_data_length = len(standard_headers)

    ewrapper.add_row(row=1, data=standard_headers, start_col="Q")
    
    for row, standard in zip(range(2, len(standards)+2), standards):
        standard_data = standard.get_all_values()

        if len(standard_data) != standard_data_length:
            while len(standard_data) != standard_data_length:
                standard_data.insert(-2, "")

        last_col = ewrapper.add_row(row=row, data=standard_data, start_col="Q")
    if type(extra_info) == list:
        descriptions = ["Parameters", "A (The lower asymptote)","B (The slope factor)", "C (The EC50)","D (The upper asymptote)","G (The asymmetry factor, when 1 results in the 4PL Curve)"]
        ewrapper.add_column(last_col+1,descriptions, start_row=1)
        ewrapper.add_column(last_col+2,["Optimized Values", *extra_info], start_row=1)
    else:
        ewrapper.add_column(last_col+1, ["R-Squared", extra_info], start_row=1)

    ewrapper.add_row(row=1, data=sample_headers, start_col=last_col+3)
    for row, sample in zip(range(2, len(samples)+2),samples):
        sample_data = sample.get_all_values()
        if len(sample_data) != sample_data_length:
            while len(sample_data) != sample_data_length:
                sample_data.insert(-2, "")
        ewrapper.add_row(row=row, data=sample_data, start_col=last_col+3)
    
    return None

def get_linear_regression_function(x_values:list[float], y_values:list[float])->tuple[Callable[[float], float], Callable[[float], float], float]:
    '''Returns the inverse linear regression function, linear regression function and R-squared value that are derived from standards, 
    the inverse linear function is used to calculate the concentration of AB relative to the OD values of the standards'''
    slope, intercept = statistics.linear_regression(x_values, y_values)
    
    r_squared = statistics.correlation(x_values, y_values)**2 #The square of the pearson coeffecient is the coefficient of determination
    print("The slope of the linear regression line is: ", slope, "\nThe intercept is: ", intercept, "\nThe R-squared value is: ", r_squared)
    return lambda y: (y-intercept)/slope, lambda x:slope*x+intercept, r_squared

def get_logarithmic_regression_function(x_values:list[float], y_values:list[float])->tuple[Callable[[float], float], Callable[[float], float], float]:
    '''Returns the inverse logarithmic regression function, logarithmic regression function and R-squared value that are derived from standards, 
    the inverse logarithmic function is used to calculate the concentration of AB relative to the OD values of the standards'''
  
    ln_x_values = [math.log(x) for x in x_values if x != 0]
    filtered_y_values = [y for y,x in zip(y_values, x_values) if x != 0]
    
    slope, intercept = statistics.linear_regression(ln_x_values, filtered_y_values)
    r_squared = statistics.correlation(ln_x_values, filtered_y_values)**2
    print("The slope of the logarithmic regression line is: ", slope, "\nThe intercept is: ", intercept, "\nThe R-squared value is: ", r_squared)
    return lambda y: math.exp((y-intercept)/slope), lambda x: slope*math.log(x)+intercept, r_squared

def get_five_parameter_logistic_curve(x_values:list[float], y_values:list[float])->tuple[Callable[[float,float], float], Callable[[float], float], list[float]]:
    '''Returns the inverse 5 parameter logistic curve function and 5 parameter logistic curve function that are derived from standards, 
    the inverse function is used to calculate the concentration of AB relative to the OD values of the standards'''

    # A = 0.1 #The lower asymptote -> Assumes that the lowest measured y value is the lowest asymptote
    # B = max(y_values) #The upper asymptote -> Assumes that the highest measured y value is the lowest asymptote
    # C = max(x_values)/2 #Inflection point -> Assumes that the inflection point is the middle value of the measured concentrations
    # D = (B-A)/(max(x_values)-min(x_values)) #Slope at the inflection point
    # G = 1 #Asymmetry factor, assumes the sigmodial curve is symmetrical indicated by the value 1
    # bounds =  (0, [np.inf, np.inf, np.max(x_values), np.inf, np.inf]) # -> Including these bounds causes inaccurate regression models to be created
    five_pl = lambda x, a,b,c,d,e: d + (a - d) / ((1 + (x / c) ** b) ** e) 
    optimal_params, _ = scipy.optimize.curve_fit(f = five_pl, xdata=x_values, ydata=y_values, maxfev=100000) #->Including best guess parameters can cause crashes because the best guesses are essentially terrible
    
    A,B,C,D,G = optimal_params
    
    print(f'''
        The optimized parameters are:
        
        A (The lower asymptote): {A}
        B (The slope factor): {B}
        C (The EC50): {C}
        D (The upper asymptote): {D} 
        G (The asymmetry factor, when 1 results in the 4PL Curve): {G} 
        
          
        ''')
    
    optimized_5_pl = lambda x: D + (A - D) / ((1 + (x / C) ** B) ** G)
    
    inverse_5_pl = lambda response, starting_estimate: scipy.optimize.fsolve(lambda x: optimized_5_pl(x)-response, starting_estimate, maxfev=100000)[0]
    
    return  inverse_5_pl, optimized_5_pl, [A,B,C,D,G]

def regression_plot(equation:Callable[[float], float], standards:list[Sample], samples:list[Sample], extra_info:float, unit:str, regression_type:str = "Linear", figure_name:str = "")->Image:
    '''Adds a set of data points to the matplotlib graph instance to show later'''
    
    #Create a large set of x_values between the max and the min of the standards to give the appearance of a smooth line
    max_ab = max([standard.ab_concentration for standard in standards])
    min_ab = min([standard.ab_concentration for standard in standards])
    filler = np.linspace(min_ab, max_ab, 100)

    plt.figure(figure_name)
    # plt.xlim((0,math.log(max_ab*1.10)))
    plt.plot([standard.ab_concentration for standard in standards], [standard.average for standard in standards], "go")
    for standard in standards:plt.text(standard.ab_concentration, standard.average, standard.label)
    
    if regression_type == "Linear":
        plt.plot([standard.ab_concentration for standard in standards],[equation(standard.ab_concentration) for standard in standards], label = f"R-squared: {round(extra_info, 3)}")
        plt.legend(loc = "upper center")
    elif regression_type == "Logarithmic":
        plt.plot([x for x in filler if x!= 0], [equation(x) for x in filler if x != 0], label = f"R-squared: {round(extra_info, 3)}")
        plt.legend(loc = "upper center")
    elif regression_type == "5PL":
        A,B,C,D,G = [round(val, 3) for val in extra_info]
        plt.plot(filler, equation(filler), label = f'''
        The optimized parameters are:
        
        A (The lower asymptote): {A}
        B (The slope factor): {B}
        C (The EC50): {C}
        D (The upper asymptote): {D} 
        G (The asymmetry factor, when 1 results in the 4PL Curve): {G} 
        ''')
        plt.legend(loc = "upper left")
        
    
    plt.plot([sample.calculated_ab for sample in samples if sample.calculated_ab <= max_ab], [sample.average for sample in samples if sample.calculated_ab <= max_ab], "ro")
    for sample in samples: plt.text(sample.calculated_ab, sample.average, sample.label) 

    plt.title(figure_name)
    plt.xlabel(f"Ab Concentration ({unit})")
    plt.ylabel("Optical Density")
    plt.xscale("log")
    figure = io.BytesIO()
    plt.savefig(figure,format = "jpeg")
    plt.draw()
    plt.show()
    
    # plt.get_current_fig_manager().full_screen_toggle()
    figure_bytes = io.BytesIO()
    plt.savefig(figure_bytes,format = "jpeg")
    return Image.open(figure_bytes)

def merge_plate_template(plate:list[str], template:list[str])->tuple[list[Sample], list[Sample]]:
    '''Iterates through each list and creates two lists that contains only unique values from the template list, Sample and Standards.
    The lists are seperated based on the prefix given to the name of the sample/standard/control, i.e 'Unknown', 'Standards', 'Control'. '''
    STANDARD = "standard"
    CONTROL = "control"
    SAMPLE = "sample"
    
    samples:dict[str, Sample] = {}
    standards:dict[str, Sample] = {}
    units = ""
    prefixes = get_prefixes(template)
    labels = remove_prefixes(template)

    for prefix, label, od in zip(prefixes, labels, plate):
        od = float(od) #-> Need to ask HuiTing whether or not convert negative OD values into 0
        if prefix == STANDARD:
            conc = float(remove_unit(label))
            units = get_unit(label)
            check_and_append(standards, label, od, prefix, conc)
        elif prefix == CONTROL:
            check_and_append(standards, label, od, prefix)
        elif prefix == SAMPLE:
            check_and_append(samples, label, od, prefix)

    s = []
    s2 = []

    for sample in samples.values():
        sample.average = round(statistics.mean(sample.values), 4)
        sample.std = round(statistics.stdev(sample.values),4) if len(sample.values) > 1 else 0
        s.append(sample)

    for standard in standards.values():
        standard.average = round(statistics.mean(standard.values), 4)
        standard.std = round(statistics.stdev(standard.values),4) if len(standard.values) > 1 else 0
        s2.append(standard)

    return s, s2, units

def check_and_append(storage:dict[str, Sample], label:str, od:float, sample_type:str, conc:float = None)->None:
    if current := storage.get(label,False):
        current.values.append(od)
    else:
        current = Sample(label, ab_concentration=conc, sample_type=sample_type) if conc != None else Sample(label)
        current.values.append(od)
        storage[label] = current

def remove_prefixes(vals:list[str], sep:str = "-")->list[str]:
    '''Removes the prefix from the rest of the string using the 'seperator' as the barrier between both of them'''
    return [val.split(sep, 1)[-1] for val in vals]

def get_prefixes(vals:list[str], seperator:str = "-")->list[str]:
    '''Returns a list of prefixes from the rest of the string using the 'seperator' as the barrier between both of them'''
    return [val.split(sep=seperator)[0].lower() for val in vals]

def remove_unit(val:str)->str:
    '''Assumes the units are 4 characters and are located at the end of the string'''
    return val[:-5]

def get_unit(val:str)->str:
    '''Assumes the units are 4 characters and are located at the end of the string'''
    return val[-5:]

 
def temp()->None:
    ewrapper = ExcelWrapper("C:\\\\Users\\elie\\Desktop\\20240305 Mirimus_results.xlsx")
    samps = ewrapper.get_column("A", start_row=2, end_row=173, values_only=True)
    samp_ods = [np.float32(od) for od in ewrapper.get_column("C", start_row=2, end_row=173, values_only=True)]
    samples:list[Sample] = []
    
    for s, od in zip(samps, samp_ods):
        samples.append(Sample(s, average=od))
    
    print(samples[0])
    concentrations = ewrapper.get_column("F", start_row=2, end_row=7, values_only=True)
    optical_densities = ewrapper.get_column("G", start_row=2, end_row=7, values_only=True)
    standards:list[Sample] = []
    for conc, od in zip(concentrations, optical_densities):
        c = np.float32(remove_unit(conc))
        od = np.float32(od)
        standards.append(Sample(conc, average=od, ab_concentration=c))
        
    inverse, equation, r = get_five_parameter_logistic_curve([standard.ab_concentration for standard in standards], [standard.average for standard in standards])
    
    for sample in samples:
        diff = []
        for standard in standards:
            diff.append(abs(sample.average - standard.average))
        
        sample.closest_conc = standards[diff.index(min(diff))].ab_concentration
        
    for standard in standards: standard.calculated_ab = inverse(standard.average, standard.ab_concentration)
            
    for sample in samples: sample.calculated_ab = inverse(sample.average, sample.closest_conc)
    
    ewrapper.add_column("H", [sample.label for sample in samples])
    ewrapper.add_column("I", [round(sample.average, 3) for sample in samples])
    ewrapper.add_column("J", [sample.calculated_ab for sample in samples])
    ewrapper.write_excel("C:\\\\Users\\elie\\Desktop\\20240305 Mirimus_results Reanalyzed.xlsx")
    
    regression_plot(equation, standards, samples, r, "ng/mL", "5PL", "20240305 Mirimus Results Reanalyzed")