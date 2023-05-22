import datetime as dt

import numpy as np

import cdflib

cdf = cdflib.cdfwrite.CDF("test.cdf")

var_spec = {}
var_spec["Variable"] = "time"
var_spec["Data_Type"] = "CDF_EPOCH"
var_spec["Num_Elements"] = 10
var_spec["Rec_Vary"] = True
var_spec["Dim_Sizes"] = []

time = np.array(
    [
        dt.datetime(2001, 1, 1),
        dt.datetime(2001, 1, 2),
        dt.datetime(2001, 1, 3),
        dt.datetime(2001, 1, 4),
        dt.datetime(2001, 1, 5),
        dt.datetime(2001, 1, 6),
        dt.datetime(2001, 1, 7),
        dt.datetime(2001, 1, 8),
        dt.datetime(2001, 1, 9),
        dt.datetime(2001, 1, 10),
    ]
)

time_list = [[f.year, f.month, f.day, 0, 0, 0, 0] for f in time]
var_data = [cdflib.cdfepoch.compute(t) for t in time_list]

cdf.write_var(var_spec, var_data=var_data)
cdf.close()
