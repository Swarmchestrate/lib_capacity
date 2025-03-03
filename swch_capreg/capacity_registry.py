import copy
import logging
import uuid
import yaml

# Logger configuration
logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, 
    format='(%(asctime)s) %(levelname)s:\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

# Constants
MAIN_RESOURCE_TYPES = ["raw", "flavor"]                 # May expand in the future
RAW_RESOURCE_TYPES = ["cpu", "ram", "disk", "pub_ip"]   # May expand in the future
FLAVOR_CONFIG_KEYS_MIN = ["cpu", "ram", "disk"]         # May expand in the future
FLAVOR_TYPE_KEYS = ["config", "amount"]                 # May expand in the future

def Initialize(flavor_capacity: dict, raw_capacity: dict = None):
    """Initializes a capacity registry file with the given initial flavors. A dictionary containing the initial flavors is required for initialization.

    Args:
        flavor_capacity (dict): A dictionary containing flavor (VM) types (eg.: m1.medium, l1.large, s1.small etc.).
        raw_capacity (dict, optional): A dictionary containing raw resource types (eg.: disk, CPU, RAM, public IPs etc.). Defaults to None.
    
    Returns:
        bool: True if the initialization was successful, otherwise, False.
    """

    def ValidateInitializationRawDict(raw_capacity: dict):

        # TO-DO: function documentation
        # TO-DO: input raw dict key check
        # TO-DO: input raw dict value check

        # Check if not dict
        if isinstance( raw_capacity, dict ) == False:
            logger.error("Input initial raw capacity is not a dict.")
            return False

        # Check if empty
        if raw_capacity == {}:
            logger.error("Input initial raw capacity is empty.")
            return False
        
        # Check keys
        for init_raw_type in raw_capacity.keys():

            # Check if not string
            if isinstance( init_raw_type, str) == False:
                logger.error(f'Raw resource dictionary key "{init_raw_type}" is not a string.')
                return False

            # Check if unknown raw resource type
            if init_raw_type not in RAW_RESOURCE_TYPES:
                logger.error(f'Unknown raw resource type "{init_raw_type}".')
                return False
            else:
                # Check if integer
                if isinstance( raw_capacity[init_raw_type], int ) == False:
                    logger.error(f'Raw resource type "{init_raw_type}" is not an integer.')
                    return False
                elif isinstance( raw_capacity[init_raw_type], bool ) == True:
                    logger.error(f'Raw resource type "{init_raw_type}" is not an integer.')
                    return False
                
                # Check if 1 or higher
                if raw_capacity[init_raw_type] < 1:
                    logger.error(f'Amount of initial raw resource type "{init_raw_type}" must be 1 or higher.')
                    return False
        
        return True
    
    def ValidateInitializationFlavorDict(flavor_capacity: dict, raw_given: bool = False):

        # Check if dict
        if isinstance( flavor_capacity, dict ) == False:
            logger.error("Input initial flavor capacity is not a dict.")
            return False

        # Check if empty
        if flavor_capacity == {}:
            logger.error("Input initial flavor capacity is empty.")
            return False
    
        # Check flavor keys
        for init_flavor_type in flavor_capacity.keys():

            # Check if key is not string
            if isinstance( init_flavor_type, str) == False:
                logger.error(f'Flavor type key "{init_flavor_type}" is not a string.')
                return False
            
            # Check if flavor is not dict
            if isinstance( flavor_capacity[init_flavor_type], dict) == False:
                logger.error(f'Flavor type definition for "{init_flavor_type}" is not a dict.')
                return False
            
            # Check if flavor is not dict
            if flavor_capacity[init_flavor_type] == {}:
                logger.error(f'Flavor type definition for "{init_flavor_type}" is empty.')
                return False
            
            # Check for unknown keys in flavor
            for flavor_key in flavor_capacity[init_flavor_type].keys():
                if flavor_key not in FLAVOR_TYPE_KEYS:
                    logger.error(f'Uknown key "{flavor_key}" defined for flavor type "{init_flavor_type}".')
                    return False
            
            # Check for necessary keys
            if "config" not in flavor_capacity[init_flavor_type].keys():
                logger.error(f'No "config" defined for flavor type "{init_flavor_type}".')
                return False
            else:
                # Check if config not dict
                if isinstance(flavor_capacity[init_flavor_type]["config"], dict) == False:
                    logger.error(f'Config defined for flavor type "{init_flavor_type}" is not a dictionary.')
                    return False
                
                # Check if config is empty
                if flavor_capacity[init_flavor_type]["config"] == {}:
                    logger.error(f'Config defined for flavor type "{init_flavor_type}" is empty.')
                    return False
                
                # Check for nevessary keys in flavor's config
                for config_key in FLAVOR_CONFIG_KEYS_MIN:
                    if config_key not in flavor_capacity[init_flavor_type]["config"].keys():
                        logger.error(f'No key "{config_key}" defined in the config of flavor type "{init_flavor_type}".')
                        return False
            
                # Check for unknown keys in flavor's config
                for config_key in flavor_capacity[init_flavor_type]["config"].keys():
                    if config_key not in RAW_RESOURCE_TYPES:
                        logger.error(f'Unknown configuration key "{config_key}" defined in flavor "{init_flavor_type}".')
                        return False
                    else:
                        # Check if integer
                        if isinstance( flavor_capacity[init_flavor_type]["config"][config_key], int ) == False:
                            logger.error(f'Config key "{config_key}" defined for flavor "{init_flavor_type}" is not an integer.')
                            return False
                        
                        # Check if bool
                        if isinstance( flavor_capacity[init_flavor_type]["config"][config_key], bool ) == True:
                            logger.error(f'Config key "{config_key}" defined for flavor "{init_flavor_type}" is not an integer.')
                            return False
                        
                        # Check if over 1
                        if flavor_capacity[init_flavor_type]["config"][config_key] < 1:
                            logger.error(f'Config key "{config_key}" must be 1 or higher for flavor "{init_flavor_type}".')
                            return False
            
            if raw_given == True:
                if "amount" in flavor_capacity[init_flavor_type].keys():
                    logger.error(f'Raw resources were given, no "amount" key is necessary for flavor type "{init_flavor_type}".')
                    return False
            else:
                if "amount" not in flavor_capacity[init_flavor_type].keys():
                    logger.error(f'No "amount" key given for flavor type "{init_flavor_type}".')
                    return False

                # Check "amount" key and value
                if "amount" in flavor_capacity[init_flavor_type].keys():
                    # Check if integer
                    if isinstance( flavor_capacity[init_flavor_type]["amount"], int ) == False:
                        logger.error(f'Amount defined for flavor "{init_flavor_type}" is not an integer.')
                        return False
                    
                    # Check if bool
                    if isinstance( flavor_capacity[init_flavor_type]["amount"], bool ) == True:
                        logger.error(f'Amount defined for flavor "{init_flavor_type}" is not an integer.')
                        return False
                    
                    # Check if over 1
                    if flavor_capacity[init_flavor_type]["amount"] < 1:
                        logger.error(f'Invalid amount defined for flavor "{init_flavor_type}".')
                        return False
    
    # TO-DO: include example for usage in documentation
    # TO-DO: include option to init from yaml file

    if (flavor_capacity == None):
        logger.error("No flavor types defined defined. Please define initial flavors!")
        return False
    else:
        if (raw_capacity != None):
            if ValidateInitializationRawDict(raw_capacity) == False:
                logger.info('Invalid initial raw resource dictionary. Initialization was unsuccessful.')
                return False
            
            if ValidateInitializationFlavorDict(flavor_capacity, raw_given=True) == False:
                logger.info('Invalid initial flavor dictionary. Initialization was unsuccessful.')
                return False
        else:
            if ValidateInitializationFlavorDict(flavor_capacity, raw_given=False) == False:
                logger.info('Invalid initial flavor dictionary. Initialization was unsuccessful.')
                return False
    
    logger.info('Initializing capacity registry...')

    capacity = {
        "initial": {},
        "reservations": {}
        }
    
    capacity["initial"]["raw"] = raw_capacity
    capacity["initial"]["flavor"] = flavor_capacity

    # TO-DO: ask for permission to reinitialize
    with open("capreg.yaml", "w") as file:
        try:
            file.write( yaml.dump(capacity) )
        except yaml.YAMLError as exception:
            print(exception)
            logging.error("An error has occured!")
            # TO-DO: error handling

            return False
        
    logger.info('Successfully initialized capacity registry!')
    return True

def SummarizeAllReservations(capacity: dict):
    """Summarizes all reserved resources.

    Args:
        capacity (dict): A dictionary containing the initial capacities and reservations. The current capacity registry.

    Returns:
        dict: A dictionary of the overall amount of reserved resources. Contains the reserved amount of raw and flavor type resources.
    """

    total_reservations = {
        "flavor": {},
        "raw": {}
        }
    
    if capacity["initial"]["raw"] is not None:
        for raw_res_type in capacity["initial"]["raw"].keys():
            total_reservations["raw"][raw_res_type] = 0
    
    if capacity["initial"]["flavor"] is not None:
        for flavor_type in capacity["initial"]["flavor"].keys():
            total_reservations["flavor"][flavor_type] = 0

    if len( capacity["reservations"].keys() ) > 0:
        for res_id in capacity["reservations"].keys():
            if "raw" in capacity["reservations"][res_id].keys():
                for res_type, res_amount in capacity["reservations"][res_id]["raw"].items():
                    total_reservations["raw"][res_type] += res_amount

            elif "flavor" in capacity["reservations"][res_id].keys():
                for flavor_type, res_amount in capacity["reservations"][res_id]["flavor"].items():
                    total_reservations["flavor"][flavor_type] += res_amount

                    for config_res_type, config_res_amount in capacity["initial"]["flavor"][flavor_type]["config"].items():
                        total_reservations["raw"][config_res_type] += (res_amount * config_res_amount)
    else:
        pass
    
    return total_reservations

def RemainingCapacity(capacity: dict):
    """Calculates the remaining capacity of the different resources.

    Args:
        capacity (dict): A dictionary containing the initial capacities and reservations. The current capacity registry.

    Returns:
        dict: A dictionary containing the remaining capacity of the different resources, grouped by the main resource types (eg.: raw, flavor etc.).
    """

    total_reservations = SummarizeAllReservations(capacity)
    initial_capacity = capacity["initial"]
    
    remaining_capacity = {
        "flavor": {},
        "raw" : {}
        }
    
    raw_res_types = list( capacity["initial"]["raw"].keys() )

    if len(raw_res_types) > 0:
        for raw_res_type in raw_res_types:
            remaining_capacity["raw"][raw_res_type] = initial_capacity["raw"][raw_res_type]

    if capacity["initial"]["flavor"] != None:
        flavor_types = list( capacity["initial"]["flavor"].keys() )
        if len(flavor_types) > 0:
            for flavor_type in flavor_types:
                remaining_capacity["flavor"][flavor_type] = initial_capacity["flavor"][flavor_type]["amount"]
    
    for main_res_type, res_data in total_reservations.items():
        for sub_res_type, res_amount in res_data.items():
            remaining_capacity[main_res_type][sub_res_type] -= res_amount
    
    return remaining_capacity

def GetReservationOffer(reservation: dict):
    """Gets a reservation offer with the given resources. Initial reservation status is "reserved", if the reservation could be made.

    A reservation can be made, only and if only, enough free resources exist for the requested resource types.
    
    Args:
        reservation (dict): A reservation dictionary containing the requested amount of resources.

    Returns:
        str: An empty string if the reservation could not be made. If the reservation could be made, then the ID (a UUID) of the reservation as a string.
    """

    capacity = ReadCapacityRegistry()
    
    def ValidateReservation(reservation: dict):
        """Validates a given reservation dictionary.

        Args:
            reservation (dict): A reservation dictionary, containing the requested resources.
            capacity (dict): A dictionary containing the initial capacities and reservations. The current capacity registry.

        Returns:
            bool: True if the reservation dictionary is in an acceptable format. Otherwise, False.
        """

        # Check reservation type
        if isinstance( reservation, dict ) == False:
            logger.error('Reservation not in a dictionary format.')
            return False
        
        # Check for empty dict
        if reservation == {}:
            logger.error('Empty reservation dictionary.')
            return False
        
        # Check for invalid main resource type
        for key in reservation.keys():
            if key not in MAIN_RESOURCE_TYPES:
                logger.error(f'Invalid main resource type "{key}".')
                return False
            
            if reservation[key] == {}:
                logger.error(f'Empty "{key}" reservation dictionary.')
                return False
            
            # Check if multiple main resource types were requested
            if len( reservation.keys() ) > 1:
                logger.error(f'Too many resource types requested.')
                return False
            
            # Raw resource check
            if key == "raw":
                for sub_key in reservation[key].keys():
                    if sub_key not in RAW_RESOURCE_TYPES:
                        logger.error(f'Invalid raw resource type "{sub_key}".')
                        return False
                    else:
                        # Check if raw resource is integer
                        if isinstance( reservation["raw"][sub_key], int) == False:
                            logger.error(f'Requested amount of resource "{sub_key}" is not an integer.')
                            return False
                        elif isinstance( reservation["raw"][sub_key], bool) == True:
                            logger.error(f'Requested amount of resource "{sub_key}" is not an integer.')
                            return False
                        else:
                            # Check if raw resource is 1 or higher
                            if reservation["raw"][sub_key] <= 0:
                                logger.error(f'Requested amount of resource "{sub_key}" is less then 1.')
                                return False
                
                return True
            
            # Flavor resource check
            elif key == "flavor":

                # Check if there were any flavors defined
                if capacity["initial"]["flavor"] is None:
                    logger.error("There are no flavors types defined.")
                    return False

                # Check for invalid flavor
                flavor_types = capacity["initial"]["flavor"].keys()
                for req_flavor in reservation["flavor"].keys():
                    if req_flavor not in flavor_types:
                        logger.error(f'Unrecognized flavor type "{req_flavor}" requested.')
                        return False
                
                    # Check if flavor amount is not integer
                    if isinstance( reservation["flavor"][req_flavor], int) == False:
                        logger.error(f'Requested amount of flavor "{req_flavor}" is not an integer.')
                        return False
                    elif isinstance( reservation["flavor"][req_flavor], bool) == True:
                        logger.error(f'Requested amount of flavor "{req_flavor}" is not an integer.')
                        return False
                    else:
                        # Check if flavor amount is 1 or higher
                        if reservation["flavor"][req_flavor] <= 0:
                            logger.error(f'Requested amount of flavor "{req_flavor}" is less then 1.')
                            return False
   
                return True
    
    # Check if reservation can be made
    if ValidateReservation(reservation) == True:

        req_res_type = list( reservation.keys() )[0]
        remaining_capacity = RemainingCapacity(capacity)
        can_be_reserved = True

        if req_res_type == "raw":
            for res_type, res_data in reservation.items():
                for res_subtype, res_amount in res_data.items():
                    if remaining_capacity[res_type][res_subtype] < res_amount:
                        logger.warning(f'Not enough remaining "{res_subtype}" resources.')
                        can_be_reserved = False
                        break
                
                if can_be_reserved == False:
                    break
        
        elif req_res_type == "flavor":
            for req_flavor in reservation["flavor"].keys():
                if remaining_capacity["flavor"][req_flavor] < reservation["flavor"][req_flavor]:
                    logger.warning(f'Not enough remaining "{req_flavor}" flavor.')
                    can_be_reserved = False
                    break
                else:
                    flavor_config = copy.deepcopy( capacity["initial"]["flavor"][req_flavor]["config"] )

                    for res_type, res_amount in flavor_config.items():
                        req_res_amount = res_amount * reservation["flavor"][req_flavor]

                        if req_res_amount > remaining_capacity["raw"][res_type]:
                            logger.warning(f'Not enough remaining "{res_type}" resources.')
                            can_be_reserved = False
                            break
                
                    if can_be_reserved == False:
                        break

        if (can_be_reserved == False):
            logger.info("Reservation cannot be made.")
            return ""
        
        elif (can_be_reserved == True):
            logger.info('Enough remaining resources. Registering reservation.')

            reservation_uuid = str( uuid.uuid4() )
            logger.info(f'Reservation ID generated: {reservation_uuid}')
            
            reservation['status'] = 'reserved'

            capacity["reservations"][reservation_uuid] = reservation

            SaveCapacityRegistry(capacity)
            
            return reservation_uuid
    else:
        logger.info("Reservation cannot be made.")
        return ""

def AcceptOfferedReservation(reservation_id: str):

    # TO-DO: function documentation

    if isinstance( reservation_id, str) == False:
        logger.error(f'Given reservation ID is not a string.')
        return False

    if reservation_id == "":
        logger.warning(f'Please use a valid reservation ID.')
        return False

    capacity = ReadCapacityRegistry()

    if reservation_id in capacity["reservations"].keys():
        if capacity["reservations"][reservation_id]["status"] != "reserved":
            logger.warning(f'Reservation with ID "{reservation_id}" is not in "RESERVED" status.')
            return False

        logger.info(f'Reservation "{reservation_id}" found. Reservation status updated to "ASSIGNED".')
        capacity["reservations"][reservation_id]["status"] = "assigned"

        SaveCapacityRegistry(capacity)

        return True
    else:
        logger.warning(f'Reservation with ID "{reservation_id}" not found.')
        return False

def ReadCapacityRegistry():
    """Reads the capacity registry file.

    Returns:
        dict: A dictionary containing the contents of the capacity registry file.
    """

    capacity = {}

    with open("capreg.yaml", "r") as file:
        try:
            capacity = yaml.safe_load( file )
        except yaml.YAMLError as exception:
            print(exception)
            logging.error("An error has occured!")
            # TO-DO: error handling
    
    logger.info('Loaded capacity registry.')

    return capacity

def SaveCapacityRegistry(capacity: dict):
    """Saves a given capacity registry into a file. Filename is "capreg.yaml".

    Args:
        capacity (dict): A capacity registry dictionary.

    Returns:
        bool: True if saving was successful. False if an error has occured.
    """

    # TO-DO: function documentation
    # TO-DO: dict key check
    # TO-DO: dict value check
    
    with open("capreg.yaml", "w") as file:
        try:
            file.write( yaml.dump(capacity) )
            return True
        except yaml.YAMLError as exception:
            print(exception)
            logging.error("An error has occured!")
            # TO-DO: error handling

            return False

def GetCapacityRegistryInfo():
    """Lists information about the current capacity registry.
    """

    capacity = ReadCapacityRegistry()
    total_reserved = SummarizeAllReservations(capacity)
    no_of_reservations = len( capacity["reservations"].keys() )

    logger.info('Listing all resource capacities.')

    print(f"\r\n\tTotal number of reservations: {no_of_reservations}")


    if (capacity["initial"]["raw"] is not None):
        print("\r\n\tRAW resources:")
        print("\tType\t\tAll\tReserv.\tFree\t(% free)")

        # Listing raw resources  
        for act_resource_type, act_resource_amount in capacity["initial"]["raw"].items():
            try:
                percentage = '{:.1%}'.format(1 - (total_reserved["raw"][act_resource_type] / act_resource_amount) )
                free = act_resource_amount - total_reserved["raw"][act_resource_type]
                print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t{total_reserved["raw"][act_resource_type]}\t{free}\t{percentage}')
            except KeyError:
                print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t0\t0')
    
    # Listing flavor resources
    if (capacity["initial"]["flavor"] is not None):
        print("\r\n\tDefined flavors:")
        print("\tFlavor\t\tAll\tReserv.\tFree\t(% free)")

        for act_flavor_type, act_flavor_data in capacity["initial"]["flavor"].items():
            percentage = '{:.1%}'.format(1 - (total_reserved["flavor"][act_flavor_type] / act_flavor_data["amount"]) )
            free = act_flavor_data["amount"] - total_reserved["flavor"][act_flavor_type]
            print(f'\t{act_flavor_type.upper()}\t{act_flavor_data["amount"]}\t{total_reserved["flavor"][act_flavor_type]}\t{free}\t{percentage}')
    else:
        print("\r\n\tThere were no flavor types defined.")
    
    print()