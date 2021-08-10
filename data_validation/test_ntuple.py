import os 
import sys
import argparse 
sys.path.append("../")
import logging 

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
import uproot3
import pytest



# a pytest fixture gives data to other functions dependent on it 

@pytest.fixture
def data(pytestconfig):
    """Reads in the data. The default and arguments you can parse are defined in conftest.py. This is automatically linked at runtime""" 

    file = uproot3.open(pytestconfig.getoption("filename"))[b'ntuplizer;1'][b'tree;8']
    data = file.pandas.df(["*"], flatten=True)
    data['r'] = np.sqrt(data['x']**2 + data['y']**2)
    return data


# the function name data is called to give the data 
def test_missing_values(data): 
    """Checks if there are any NaN values in the data""" 
    
    missing_values = data.isnull().values.any()
    assert missing_values ==False, "There are missing values in the data"



def test_duplicates(data): 
    """Checks for duplicated rows or duplicated hitids within each event""" 

    # check if any duplicated rows 
    duplications = data.duplicated().any()
    # check if any duplicated hit ids within an event 
    agg_by_entry_hitid  = data.groupby(['entry', 'hit_id']).agg({'hit_id':'count'})
    duplicated_hitid_in_event = agg_by_entry_hitid['hit_id'].max() > 1
    assert  (duplications == False ) and (duplicated_hitid_in_event == False), "There is duplicated data. Duplicated rows returned "+ duplications+ " and duplicated hitids in event returned "+ duplicated_hitid_in_event  

def test_run_lumi(data): 
    """Checks that there are single values for lumi and run throughout the dataset""" 
    
    assert (len(data['run'].unique()) == 1) and (len(data['lumi'].unique()) == 1), "There are multiple run numbers or lumi values within this data"   



def test_evt_ids(data): 
    """Check that evt is the same throguhout each event"""
    
    # check that the length of the unique values of evt is the same as the length of the event index 
    # this will also check that the same evt id is consistent through each event 

    agg_by_evt = data.groupby(['entry', 'evt']).agg({'evt':'count'})
    num_unique_evt = len(agg_by_evt.index.get_level_values(1))
    num_unique_events = len(data.index.get_level_values(0).unique())
    assert  num_unique_evt == num_unique_events, "The number of unique evt identifiers does not match the number of events in the data. For evt this is " +  str(num_unique_evt) + " and there are " + str(num_unique_events) + " events" 
   

def test_nhit(data): 
    """Number of hits in each event must be bigger than 80 000 (very arbitrary number)"""
    # it's assumed this number is constant through each event, could be double checked 
    assert (False in data['nhit'].unique() > 80000) == False, "There is one or several events that has less than 80 000 hits" 


def test_hit_position_pixel_barrel(data): 
    """ Tests that all hits are within the r posisiton of the layers in the pixel barrel """ 

    pixelBarrel = pd.read_csv('PixelBarrel.csv', index_col = None, header=None).T
    pixelBarrel.columns= pixelBarrel.iloc[0,:]
    pixelBarrel = pixelBarrel.shift(-1).iloc[0:-1] 
    pixelBarrel = pixelBarrel.apply(lambda x: x/10 if x.name in ['r', 'z_max'] else x)
    checks_passed = []
    for i in range(1,5):
        #instead of checking all values we can check just max and min, if they pass, all other hits will pass 
        checks_passed.append(min(data[(data['volume_id']== 2) & (data['layer_id'] == i)]['r']) > (pixelBarrel['r'][i-1] - 0.4))
        checks_passed.append(max(data[(data['volume_id']== 2) & (data['layer_id'] == i)]['r']) < (pixelBarrel['r'][i-1] + 0.4))
    
    assert False not in checks_passed, "There are hits in the pixel barrel that are more than 0.4 cm away from the hit layer position" 


def test_hit_position_pixel_endcaps(data): 
    """ Tests that all hits are within the z position of the pixel endcaps """ 

    pixelEndcaps = pd.read_csv('PixelEndcap.csv', index_col = None, header=None).T
    pixelEndcaps.columns= pixelEndcaps.iloc[0,:]
    pixelEndcaps = pixelEndcaps.shift(-1).iloc[0:-1] 
    pixelEndcaps = pixelEndcaps.apply(lambda x: x/10 if x.name in ['r', 'z'] else x)
    pixelEndcaps['Disk'] = range(1,13)
    checks_passed = []
    for i in range(1,12):
        # check both positive and negative endcaps, so volume 1 and 3  

        checks_passed.append(min(data[(data['volume_id']== 1) & (data['layer_id'] == i)]['z']) > (-pixelEndcaps['z'][i-1] - 0.8))
        checks_passed.append(max(data[(data['volume_id']== 1) & (data['layer_id'] == i)]['z']) < (-pixelEndcaps['z'][i-1] + 0.8))
    
        checks_passed.append(min(data[(data['volume_id']== 3) & (data['layer_id'] == i)]['z']) > (pixelEndcaps['z'][i-1] - 0.8))
        checks_passed.append(max(data[(data['volume_id']== 3) & (data['layer_id'] == i)]['z']) < (pixelEndcaps['z'][i-1] + 0.8))
    
    assert False not in checks_passed, "There are hits in the pixel endcap that are more than 0.8 cm away from the hit layer position" 


def check_particle_id(): 
    pass

def check_pt(): 
    pass

def test_volume_and_layer_id(data): 
    volume_accepted = (max(data['volume_id']) == 3) & (min(data['volume_id']) ==1)
    layer_accepted_barrel = (max(data[data['volume_id']==2]['layer_id']) == 4) & min(data[data['volume_id']==2]['layer_id']) == 1
    layer_accepted_endcaps = (max(data[data['volume_id']==1]['layer_id']) == 12) & min(data[data['volume_id']==1]['layer_id']) == 1
    layer_accepted_endcaps_2 = (max(data[data['volume_id']==3]['layer_id']) == 12) & min(data[data['volume_id']==3]['layer_id']) == 1

    assert volume_accepted & layer_accepted_barrel & layer_accepted_endcaps & layer_accepted_endcaps_2, "There are layers that are not within the specified region of interest" 


    
