import numpy as np
from pathlib import Path
import snowmicropyn
from snowpyt import pit_class as pc
from snowpyt import CAAMLv6_xml as ca
import yaml


#pnt_caaml_allocation_filename = "pnt_caaml_allocation.csv"
#matching = 'scaling'
#matching = 'cutting'
#subdir_csv = "/data/"
#subdir_pnt = "/data/smp_pnt_files_scaled/"

parentdir = Path(__file__).parent.as_posix()

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

config_path = 'config.yaml'
config = load_config(config_path)
    
 # Zugriff auf die Konfigurationswerte
pnt_path = config['pnt_path']
scaling = config['matching']


def caaml_filename_allocator (pnt_filename, pnt_caaml_allocation_filename):
    '''
    This function finds the allocating caaml filename to the given pnt filename
    in the given csv table.
    '''
    pnt_caaml_allocation = np.loadtxt(parentdir + subdir_csv + pnt_caaml_allocation_filename, skiprows=1, delimiter=';', dtype='str')
    itemindex = np.where(pnt_caaml_allocation == pnt_filename)
    if len(itemindex[0]) > 1:
        raise ValueError("PNT filename existing more than one time in CSV table")
    return str(pnt_caaml_allocation[itemindex[0],1][0])

pnt_name_list = np.loadtxt(parentdir + subdir_csv + pnt_caaml_allocation_filename, skiprows=1, delimiter=';', dtype='str')[:,0].tolist()

for pnt_filename in pnt_name_list:

    caaml_filename = caaml_filename_allocator(pnt_filename, pnt_caaml_allocation_filename)

    print(parentdir + subdir_pnt + pnt_filename)
    current_profile = snowmicropyn.Profile.load(parentdir + subdir_pnt + pnt_filename)

    markers = current_profile.markers
    if markers:
        surface = current_profile.marker('surface')
        ground = current_profile.marker('ground')

    else:
        surface = current_profile.detect_surface()
        ground = current_profile.detect_ground()
        current_profile.save()

    subdir_caaml = '/data/caaml_files/'
    caaml_layers = ca.get_layers(parentdir + subdir_caaml + caaml_filename)

    ini_depth = ground - surface
    caaml_top = caaml_layers[0].dtop*10
    caaml_depth = (caaml_layers[0].dtop - caaml_layers[-1].dbot)*10 #warum *10

    # factor to scale the depth of the CAAML profile to that of the SMP measurement
    #TODO - at a later point add option without scaling, insteadt cut off CAAMML
    correction_factor = ini_depth / caaml_depth

    if matching == "cutting":
        if ini_depth >= caaml_depth:
            ground = surface + caaml_depth
            current_profile.remove_marker('ground')
            current_profile.set_marker('ground', ground)

    i = 0
    for layer in caaml_layers:
        #number added to graintype is necessary to allow multiple layers of same graintype
        #numbers are deleted later on in the SNOWDRAGON package
        graintype = layer.grain_type1 + str(i)
        i = i + 1
        if matching == "scaling":
            layer_bottom = (caaml_top - layer.dbot*10)*correction_factor + surface
            current_profile.set_marker(graintype, layer_bottom)
            print(graintype, layer_bottom)
        elif matching == "cutting":
            layer_bottom = (caaml_top - layer.dbot*10) + surface
            if caaml_depth > ini_depth:
                if layer_bottom < ground:
                    current_profile.set_marker(graintype, layer_bottom)
                else:
                    current_profile.set_marker(graintype, ground)
                    break
            elif ini_depth >= caaml_depth:
                current_profile.set_marker(graintype, layer_bottom)
    current_profile.save()

