"""
Script to convert CAAML snow profiles into INI files allocated to SMP PNT files.
This serves as a primary step to prepare training data for the SNOWDRAGON script by comparing manual snow pit data
to nearby collected SMP measuremnts.
SNOWADRAGON cannot read CAAML files, therefore the needed information has to be transfered to the existing INI file.

authors: Tamara and Felix, LWD Tirol
"""

import numpy as np
from pathlib import Path
import snowmicropyn

# Warum funktioniert es nur so? -> später lösen!
try:
    from snowpyt import pit_class as pc
except:
    pass
from snowpyt import CAAMLv6_xml as ca


pnt_caaml_allocation_filename = "pnt_caaml_allocation.csv"
matching = 'scaling'
#matching = 'cutting'
subdir_csv = "/data/"

parentdir = Path(__file__).parent.parent.as_posix()

def caaml_filename_allocator (pnt_filename, pnt_caaml_allocation_filename):
    '''
    This function finds the allocating caaml filename to the given pnt filename
    in the given csv table.
    '''
    subdir_csv = "/data/"
    pnt_caaml_allocation = np.loadtxt(parentdir + subdir_csv + pnt_caaml_allocation_filename, skiprows=1, delimiter=';', dtype='str')
    itemindex = np.where(pnt_caaml_allocation == pnt_filename)
    if len(itemindex[0]) > 1:
        raise ValueError("PNT filename existing more than one time in CSV table")
    return str(pnt_caaml_allocation[itemindex[0],1][0])

pnt_name_list = np.loadtxt(parentdir + subdir_csv + pnt_caaml_allocation_filename, skiprows=1, delimiter=';', dtype='str')[:,0].tolist()

for pnt_filename in pnt_name_list:
    
    caaml_filename = caaml_filename_allocator(pnt_filename, pnt_caaml_allocation_filename)
    subdir_pnt = "/data/smp_pnt_files_scaled/"
    #subdir_pnt = "/data/smp_pnt_files_cutted/"
    
    print(parentdir + subdir_pnt + pnt_filename)
    p = snowmicropyn.Profile.load(parentdir + subdir_pnt + pnt_filename)
    
    markers = p.markers
    if markers:
        surface = p.marker('surface')
        ground = p.marker('ground')
    
    else:
        surface = p.detect_surface()
        ground = p.detect_ground()
        p.save()
    
    subdir_caaml = '/data/caaml_files/'
    caaml_layers = ca.get_layers(parentdir + subdir_caaml + caaml_filename)
    
    ini_depth = ground - surface
    caaml_top = caaml_layers[0].dtop*10
    caaml_depth = (caaml_layers[0].dtop - caaml_layers[-1].dbot)*10
    
    # factor to scale the depth of the CAAML profile to that of the SMP measurement
    #TODO - at a later point add option without scaling, insteadt cut off CAAMML
    correction_factor = ini_depth / caaml_depth
    
    if matching == "cutting":        
        if ini_depth >= caaml_depth:
            ground = surface + caaml_depth
            p.remove_marker('ground')
            p.set_marker('ground', ground)
    
    i = 0
    for layer in caaml_layers:
        #number added to graintype is necessary to allow multiple layers of same graintype
        #numbers are deleted later on in the SNOWDRAGON package
        graintype = layer.grain_type1 + str(i)
        i = i + 1
        if matching == "scaling":
            layer_bottom = (caaml_top - layer.dbot*10)*correction_factor + surface
            p.set_marker(graintype, layer_bottom)
        elif matching == "cutting":
            layer_bottom = (caaml_top - layer.dbot*10) + surface
            if caaml_depth > ini_depth:
                if layer_bottom < ground:
                    p.set_marker(graintype, layer_bottom)
                else:
                    p.set_marker(graintype, ground)
                    break
            elif ini_depth >= caaml_depth:
                p.set_marker(graintype, layer_bottom)
    p.save()

