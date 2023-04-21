import numpy as np
from matplotlib import pyplot as plt
import tifffile
from voltage_imaging_analysis import voltage_imaging_analysis_fcts as voltage_imaging_fcts

# this script is a minimal working example of the voltage imaging analysis code

full_fname = r"Z:\\soledad\\soledad_revisions\\13042023\\cell1_130423_125mW_1\\cell1_130423_125mW_1_MMStack_Pos0.ome.tif"

print("Loading " + full_fname + "... (will take some time for large datasets)...")
data = tifffile.imread(full_fname)

print("Loaded " + full_fname + "...")

init_timeseries = voltage_imaging_fcts.generate_timeseries_from_stack(data, whiten_data=True, no_border_pixels=1)

print("Generated timeseries...")

segmentation_mask = voltage_imaging_fcts.update_segmentation_mask(data)

print("Segmented data...")

ridge_coefficients = voltage_imaging_fcts.generate_pixel_weights(data, init_timeseries, segmentation_mask)

print("Calculated ridge coefficients...")

# calculate trace
upd_timeseries = np.divide(np.matmul(data.reshape(data.shape[0], -1), ridge_coefficients[1:]), np.sum(ridge_coefficients[1:]))

print("Plotting data...")

fig, ax = plt.subplots()
ax.plot(upd_timeseries)
plt.show()