import numpy as np
from pathlib import Path
import snowmicropyn
from snowpyt import pit_class as pc
from snowpyt import CAAMLv6_xml as ca
import yaml


def load_config(file_path):
    '''
    Load config.yaml to get the input parameter 
    file_path(str): path to the config.yaml file 
    '''
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def caaml_filename_allocator (pnt_filename, pnt_caaml_allocation):
    '''
    This function finds the allocating caaml filename to the given pnt filename
    in the given csv table.
    Parameters:
        pnt_filename(str): name of the pnt file
        pnt_caaml_allocation(str): path to csv table
    Returns: 
        str: name of the caaml file
    '''
    allocation = np.loadtxt(pnt_caaml_allocation, skiprows=1, delimiter=';', dtype='str')
    itemindex = np.where(allocation == pnt_filename)
    if len(itemindex[0]) > 1:
        raise ValueError("PNT filename existing more than one time in CSV table")
    return str(allocation[itemindex[0],1][0])


def caaml_to_ini(pnt_caaml_allocation, pnt_path, caaml_path, scaling=False):
    '''
    This function reads the SMP profiles and the corresponding CAAML profiles
    and matches the layers of the CAAML profile to the SMP profile.
    The matching can be done by cutting the CAAML profile at the depth of the SMP profile
    or by scaling the depth of the CAAML profile to the depth of the SMP profile.
    Calculatings are done in mm, so CAAML imports (givenn in cm) are multiplied by 10.
    Parameters:
        pnt_caaml_allocation(str): path to the csv table with the allocation of the SMP profiles to the CAAML profiles
        pnt_path(str): path to the SMP profiles
        caaml_path(str): path to the CAAML profiles
        scaling(bool): Default False(=cutting)
    '''
    pnt_name_list = np.loadtxt(pnt_caaml_allocation, skiprows=1, delimiter=';', dtype='str')[:,0].tolist()

    for pnt_filename in pnt_name_list:
        # Determine the corresponding CAAML filename
        caaml_filename = caaml_filename_allocator(pnt_filename, pnt_caaml_allocation)

        print(pnt_filename)
        current_profile = snowmicropyn.Profile.load(pnt_path + pnt_filename)

        markers = current_profile.markers
        if markers:
            surface = current_profile.marker('surface')
            ground = current_profile.marker('ground')

        else:
            surface = current_profile.detect_surface()
            ground = current_profile.detect_ground()
            current_profile.save()

        caaml_layers = ca.get_layers(caaml_path + caaml_filename)

        ini_depth = ground - surface
        caaml_top = caaml_layers[0].dtop*10
        caaml_depth = (caaml_layers[0].dtop - caaml_layers[-1].dbot)*10

        # factor to scale the depth of the CAAML profile to that of the SMP measurement
        correction_factor = ini_depth / caaml_depth

        if scaling and ini_depth >= caaml_depth:
            ground = surface + caaml_depth
            current_profile.remove_marker('ground')
            current_profile.set_marker('ground', ground)


        for i, layer in enumerate(caaml_layers):
            # number added to graintype is necessary to allow multiple layers of same graintype
            # numbers are deleted later on in the SNOWDRAGON package

            graintype = layer.grain_type1 + str(i)

            # Calculate the bottom of the layer
            layer_bottom = (caaml_top - layer.dbot * 10)
            if scaling:
                layer_bottom = layer_bottom * correction_factor + surface
            else:
                layer_bottom += surface

            # Set the marker for the current layer
            if not scaling and caaml_depth > ini_depth and layer_bottom >= ground:
                current_profile.set_marker(graintype, ground)
                break
            else:
                current_profile.set_marker(graintype, layer_bottom)

        current_profile.save()

def main():
    config = load_config('config.yaml')
    #Load configs
    pnt_caaml_allocation = config['input_data']['pnt_caaml_allocation']
    pnt_path = config['input_data']['pnt_path']
    caaml_path = config['input_data']['caaml_path']
    scaling = config['scaling']
    caaml_to_ini(pnt_caaml_allocation, pnt_path, caaml_path, scaling)


if __name__ == "__main__":
    main()