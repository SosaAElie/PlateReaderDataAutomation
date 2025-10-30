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


def main(*args)->None:
    
    wkbk = ExcelWrapper(args[0])
    wkbk.write_excel("Tests/20240612 Luciferase Assays EAS.txt")