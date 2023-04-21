import numpy as np
from voltage_imaging_analysis import voltage_imaging_analysis_fcts as voltage_imaging_fcts
import os
import tifffile
from matplotlib import pyplot as plt
import PyQt5
import sys
import pyqtgraph as pg

class main_plot_window(PyQt5.QtWidgets.QWidget):
    def __init__(self):
        super(main_plot_window, self).__init__()

        # initialize variables
        self.data_directory = None
        self.correlation_img = None
        self.segmentation_mask = None
        self.weighted_coefficients = None

        self.init_ui()
        self.online_analysis_connections()

    def init_ui(self):
        self.setWindowTitle('Plot experimental data GUI')
        hbox = PyQt5.QtWidgets.QVBoxLayout()
        self.setLayout(hbox)

        plot_widgets = PyQt5.QtWidgets.QHBoxLayout()

        self.plotwidget = pg.PlotWidget()

        self.maincurve = pg.PlotDataItem()
        self.plotwidget.setLabel(axis='left', text='Counts (a.u.)')
        self.plotwidget.setLabel(axis='bottom', text='Time (a.u.)')

        self.maincurve = pg.PlotDataItem()

        self.current_plot_items = [self.maincurve]

        self.plotwidget.addItem(self.maincurve)

        plot_widgets.addWidget(self.plotwidget)

        hbox.addLayout(plot_widgets)

        data_fdir_label_widget = PyQt5.QtWidgets.QLabel("Set data directory: ")
        hbox.addWidget(data_fdir_label_widget)

        self.experimental_data_fdir = PyQt5.QtWidgets.QLineEdit(self)
        self.experimental_data_fdir.setEnabled(False)
        self.set_experimental_data_fdir_button = PyQt5.QtWidgets.QToolButton(self)
        self.set_experimental_data_fdir_button.setText("...")

        file_dir_layout = PyQt5.QtWidgets.QHBoxLayout()
        file_dir_layout.addWidget(self.experimental_data_fdir)
        file_dir_layout.addWidget(self.set_experimental_data_fdir_button)
        hbox.addLayout(file_dir_layout)

        current_file_label_widget = PyQt5.QtWidgets.QLabel("Current file(s): ")
        hbox.addWidget(current_file_label_widget)
        self.current_filename = PyQt5.QtWidgets.QLineEdit(self)
        self.current_filename.setEnabled(False)
        hbox.addWidget(self.current_filename)

        self.plot_latest_acquisition_button = PyQt5.QtWidgets.QPushButton("Plot data from latest acquistion")
        hbox.addWidget(self.plot_latest_acquisition_button)

        self.plot_specific_data_button = PyQt5.QtWidgets.QPushButton("Plot data from specific file(s)")
        hbox.addWidget(self.plot_specific_data_button)

        self.display_summary_data_button = PyQt5.QtWidgets.QPushButton("Display summary data")
        hbox.addWidget(self.display_summary_data_button)

        self.save_data_button = PyQt5.QtWidgets.QPushButton("Save data")
        hbox.addWidget(self.save_data_button)

        self.clear_plot_button = PyQt5.QtWidgets.QPushButton("Clear plot")
        hbox.addWidget(self.clear_plot_button)
    
        # self.setGeometry(10, 10, 1000, 600)
        self.show()

    def online_analysis_connections(self):
        self.set_experimental_data_fdir_button.clicked.connect(self.set_data_fdir)
        self.plot_latest_acquisition_button.clicked.connect(self.plot_latest_acquisition)
        self.plot_specific_data_button.clicked.connect(self.plot_specific_data)
        self.display_summary_data_button.clicked.connect(self.display_summary_data)
        self.clear_plot_button.clicked.connect(self.clear_plot)
        self.save_data_button.clicked.connect(self.save_data_from_plot)

        return
    
    def save_data_from_plot(self):
        print("Saving data to file (current directory)...")

        # separate concatenated filenames string into list of separate filenames 
        all_filenames = self.current_filename.text()

        separate_filenames = all_filenames.split()
        
        if len(self.current_plot_items) > len(separate_filenames):
            no_names_to_add = len(self.current_plot_items) - len(separate_filenames)

            for idx in np.arange(no_names_to_add):
                separate_filenames.insert(0, "unknown_" + str(idx))

        for fname_idx, fname in enumerate(separate_filenames):
            data = self.current_plot_items[fname_idx].getData()

            if any(item is None for item in data) is False:
                full_fname = self.experimental_data_fdir.text() + "\\" + fname.split('.')[0] + "_prelim_analysis.csv"
                # only save y axis since x axis doesnt mean anything 
                np.savetxt(full_fname, data[1])
        return

    def clear_plot(self):
        print("Clearing plots (not sure why but this is pretty slow)")
        for plot_item in self.current_plot_items:
            plot_item.clear()
        return

    def set_data_fdir(self):
        dlg = PyQt5.QtWidgets.QFileDialog()
        selected_dir = dlg.getExistingDirectory(self, "Select folder")
        self.experimental_data_fdir.setText(selected_dir)
        self.data_directory = selected_dir
        return

    def plot_specific_data(self):
        
        # only load image data
        supportedFormats = PyQt5.QtGui.QImageReader.supportedImageFormats()
        text_filter = "Images ({})".format(" ".join(["*.{}".format(fo.data().decode()) for fo in supportedFormats]))

        dlg = PyQt5.QtWidgets.QFileDialog()
        dlg.setFileMode(PyQt5.QtWidgets.QFileDialog.ExistingFiles)
        
        # if directory already specified, navigate here
        if self.data_directory is not None:
            file_dir = self.data_directory
        else:
            file_dir = "E:\\Experimental\\"
        
        selected_filenames = dlg.getOpenFileNames(self, "Open files", file_dir, filter=text_filter)

        selected_filenames =  selected_filenames[0]

        # set data directory 
        self.experimental_data_fdir.setText(os.path.commonpath(selected_filenames))
        self.data_directory = os.path.commonpath(selected_filenames)

        # set current files
        all_basenames = []

        for fname in selected_filenames:
            all_basenames.append(os.path.basename(fname))
    
        # generate a string from the list         
        self.current_filename.setText(" ".join(all_basenames))

        line_colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']

        no_replicates = np.ceil(np.divide(len(selected_filenames), len(line_colors))).astype(int)

        line_colors = line_colors*no_replicates

        # plot data
        for fidx, fname in enumerate(selected_filenames):

            pen = pg.mkPen(line_colors[fidx])
            
            self.curve_i = pg.PlotDataItem()
            self.current_plot_items.append(self.curve_i)
            self.plotwidget.addItem(self.curve_i)

            print("Loading " + fname + "...")

            data = tifffile.imread(fname)

            print("Loaded " + fname + "...")

            init_timeseries = voltage_imaging_fcts.generate_timeseries_from_stack(data, whiten_data=True, no_border_pixels=1)

            segmentation_mask = voltage_imaging_fcts.update_segmentation_mask(data)
            ridge_coefficients = voltage_imaging_fcts.generate_pixel_weights(data, init_timeseries, segmentation_mask)
            
            # calculate trace
            upd_timeseries = np.divide(np.matmul(data.reshape(data.shape[0], -1), ridge_coefficients[1:]), np.sum(ridge_coefficients[1:]))

            self.curve_i.setData(upd_timeseries, pen=pen)
                            
    def plot_latest_acquisition(self):
        # clear data from existing plot
        self.clear_plot()

        if self.data_directory is not None:
            all_matching_files = []

            for root, _, filenames in os.walk(self.data_directory):
                for filename in filenames:
                    if filename.endswith(('.tif')):
                            all_matching_files.append(os.path.join(root, filename))
            
            if len(all_matching_files) > 0:
                fname_latest_acquisition = max(all_matching_files, key=os.path.getctime)

                print("Loading " + fname_latest_acquisition + "...")

                self.current_filename.setText(os.path.basename(fname_latest_acquisition))

                data = tifffile.imread(fname_latest_acquisition)

                print("Loaded " + fname_latest_acquisition + "...")

                print("Processing: " + fname_latest_acquisition + "...")

                init_timeseries = voltage_imaging_fcts.generate_timeseries_from_stack(data, whiten_data=True, no_border_pixels=1)

                segmentation_mask = voltage_imaging_fcts.update_segmentation_mask(data)
                ridge_coefficients = voltage_imaging_fcts.generate_pixel_weights(data, init_timeseries, segmentation_mask)

                self.correlation_img = voltage_imaging_fcts.compute_local_correlation_image(data, no_neighbours=8, to_whiten_data=False)

                self.segmentation_mask = segmentation_mask
                self.weighted_coefficients = ridge_coefficients[1:].reshape(segmentation_mask.shape[0], segmentation_mask.shape[1])

                # calculate trace
                upd_timeseries = np.divide(np.matmul(data.reshape(data.shape[0], -1), ridge_coefficients[1:]), np.sum(ridge_coefficients[1:]))

                # background_pixels = voltage_imaging_fcts.background_segmentation(data, all_idxs_laser_on)

                # # calculate trace
                # background_trace = np.divide(np.matmul(data.reshape(data.shape[0], -1), np.ravel(background_pixels)), np.sum(background_pixels))

                # self.maincurve.setData(upd_timeseries - background_trace)
                self.maincurve.setData(upd_timeseries)
                
            else:
                print("No matching files found")
        else: 
            print("Need to specify a directory")
        return

    def display_summary_data(self):
        self.summary_data = summaryData(self.correlation_img, self.segmentation_mask, self.weighted_coefficients) 
        self.summary_data.show()      

class summaryData(PyQt5.QtWidgets.QWidget):
    def __init__(self, correlation_img, segmentation_mask, weighted_coefficients):
        super(summaryData, self).__init__()

        # initialize variables
        self.correlation_img = correlation_img
        self.segmentation_mask = segmentation_mask
        self.weighted_coefficients = weighted_coefficients

        # setup gui
        main_layout = PyQt5.QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.main_widget = pg.GraphicsLayoutWidget()
        main_layout.addWidget(self.main_widget)

        # imshow data
        self.viewer1 = self.main_widget.addViewBox(row = 1, col = 0)
        self.viewer2 = self.main_widget.addViewBox(row = 1, col = 1)
        self.viewer3 = self.main_widget.addViewBox(row = 1, col = 2)

        # lock the aspect ratio so pixels are always square
        self.viewer1.setAspectLocked(True)
        self.viewer2.setAspectLocked(True)
        self.viewer3.setAspectLocked(True)
    
        # Create image item
        self.img1 = pg.ImageItem(border='w')
        self.img2 = pg.ImageItem(border='w')
        self.img3 = pg.ImageItem(border='w')

        self.viewer1.addItem(self.img1)
        self.viewer2.addItem(self.img2)
        self.viewer3.addItem(self.img3)

        self.img1.setImage(self.correlation_img)
        self.img2.setImage(self.segmentation_mask)
        self.img3.setImage(self.weighted_coefficients)

        img1_text = pg.TextItem("Correlation image")
        img2_text = pg.TextItem("Segmentation")
        img3_text = pg.TextItem("Weighted coefficients")

        self.viewer1.addItem(img1_text)
        self.viewer2.addItem(img2_text)
        self.viewer3.addItem(img3_text)

def main():
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Online data plotting')
    ex = main_plot_window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()