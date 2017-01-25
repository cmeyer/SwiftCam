# -*- coding: utf-8 -*-
"""
Created on Sun Dec 11 12:59:33 2016

@author: Andi
"""
import time
import numpy as np
import os
import pyclbr
import importlib

_camera_formats = dict()

def import_camera_supplies():
    dirlist = os.listdir(os.path.dirname(__file__))
    matched_dirlist = []
    for name in dirlist:
        if os.path.splitext(name)[1] == '.py' and os.path.splitext(name.lower())[0].endswith('_supply'):
            matched_dirlist.append(os.path.splitext(name)[0])
    
    camera_classes = []
    for name in matched_dirlist:
        try:
            contents = pyclbr.readmodule(name, path=[os.path.dirname(__file__)])
        except AttributeError:
            print('Could not read module ' + name)
        else:
            for classname in contents.keys():
                if classname.lower().endswith('_camera'):
                    camera_classes.append((name, classname))
    
    for camera_module, camera_class in camera_classes:
        try:
            mod = importlib.import_module('.' + camera_module, package='SwiftCam')
            cam = getattr(mod, camera_class)
        except ImportError as detail:
            print(detail)
            print('Could not import camera class {:s} from module {:s}'.format(camera_class, camera_module))
        else:
            _camera_formats[camera_module.split('_')[0].lower()] = cam

import_camera_supplies()

class Camera():
    def __init__(self, **kwargs):
        self.format = kwargs.get('format', 'mjpeg')
        self.mode = 'Run'
        self.mode_as_index = 0
        self.exposure_ms = 0
        self.binning = 1
        self.sensor_dimensions = (512,512)
        self.readout_area = self.sensor_dimensions
        self.cam = None
        self.last_frame_taken = 0
        self.url = kwargs.get('url')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.frame_number = 0

    def set_exposure_ms(self, exposure_ms, mode_id):
        self.exposure_ms = exposure_ms

    def get_exposure_ms(self, mode_id):
        return self.exposure_ms

    def set_binning(self, binning, mode_id):
        self.binning = binning

    def get_binning(self, mode_id):
        return self.binning

    def start_live(self):
        if self.url is not None:
            self.cam = _camera_formats[self.format.lower()](self.url, user=self.user, password=self.password)

    def stop_live(self):
        time.sleep(1)
        self.cam.close()

    def acquire_image(self):
        now = time.time()
        if now - self.last_frame_taken < self.exposure_ms*0.001:
            time.sleep(self.exposure_ms*0.001 - (now - self.last_frame_taken))
        self.last_frame_taken = now
        data_element = {}
        data_element['data'] = np.array(self.cam.buffer.get(timeout=10))[..., (2, 1, 0)]
        data_element['properties'] = {'spatial_calibrations': [{'offset': 0, 'scale': 1, 'units': None}]*2,
                                      'frame_number': self.frame_number}
        self.frame_number += 1
        return data_element

    def acquire_sequence(self, n):
        raise NotImplementedError

    def open_monitor(self):
        raise NotImplementedError

    def open_configuration_interface(self):
        raise NotImplementedError