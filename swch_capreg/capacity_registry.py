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

def Initialize(raw_capacity: dict = None, flavor_capacity: dict = None):
    """Initializes a capacity registry file with the given initial resources.

    IMPORTANT: at least one initial resource type dictionary is required.

    Args:
        raw_capacity (dict, optional): A dictionary containing raw resource types (eg.: disk, CPU, RAM, floating IPs etc.). Defaults to None.
        flavor_capacity (dict, optional): A dictionary containing VM resource types (eg.: m1.medium, l1.large, s1.small etc.). Defaults to None.

    Returns:
        bool: True if the initialization was successful, otherwise, False.
    """

    def ValidateInitializationRawDict(raw_capacity: dict):

        # TO-DO: function documentation
        # TO-DO: input raw dict key check
        # TO-DO: input raw dict value check

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
    
    def ValidateInitializationFlavorDict(flavor_capacity: dict):

        # TO-DO: function documentation
        # TO-DO: input flavor dict key check
        # TO-DO: input flavor dict value check

        if flavor_capacity == {}:
            logger.error("Input initial flavor capacity is empty.")
            return False
        

    # TO-DO: include example for usage in documentation
    # TO-DO: include option to init from yaml file

    if (raw_capacity == None and flavor_capacity == None):
        logger.error("No initial capacity defined. Please define initial resources!")
        return False
    
    if (raw_capacity != None):
        if ValidateInitializationRawDict(raw_capacity) == False:
            logger.info('Invalid raw resource dictionary. Initialization was unsuccessful.')
            return False
    
    logger.info('Initializing capacity registry...')

    # TO-DO: dict values check

    # TO-DO: separate into constant
    
    for required_res_key in RAW_RESOURCE_TYPES:
        if required_res_key not in raw_capacity.keys():
            logger.error(f'No required raw resource type "{required_res_key}" found!')
            return False
        else:
            if isinstance( raw_capacity[required_res_key], int) == False:
                logger.error(f'Required raw resource type "{required_res_key}" found, but not integer. Please use an integer!')
                return False

    # TO-DO: dict key check for flavors

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
    
    # TO-DO: function documentation

    total_reservations = {
        "flavor": {},
        "raw": {}
        }
    
    for raw_res_type in capacity["initial"]["raw"].keys():
        total_reservations["raw"][raw_res_type] = 0
    
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

    flavor_types = list( capacity["initial"]["flavor"].keys() )
    raw_res_types = list( capacity["initial"]["raw"].keys() )

    # TO-DO: count flavor used resources

    if len(raw_res_types) > 0:
        for raw_res_type in raw_res_types:
            remaining_capacity["raw"][raw_res_type] = initial_capacity["raw"][raw_res_type]

    if len(flavor_types) > 0:
        for flavor_type in flavor_types:
            remaining_capacity["flavor"][flavor_type] = initial_capacity["flavor"][flavor_type]["amount"]
    
    for main_res_type, res_data in total_reservations.items():
        for sub_res_type, res_amount in res_data.items():
            remaining_capacity[main_res_type][sub_res_type] -= res_amount
    
    return remaining_capacity

def MakeReservation(reservation: dict):
    """Reserves the given resources in a reservation. Initial reservation status is "reserved", if the reservation could be made.

    A reservation can be made, only and if only, if enough free resources exist for the requested resource types.

    IMPORTANT: only one main resource type can be reserved in a reservation, eg.: only raw.

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
                        logger.info(f'Not enough remaining "{res_subtype}" resources.')
                        can_be_reserved = False
                        break
                
                if can_be_reserved == False:
                    break
        
        elif req_res_type == "flavor":
            for req_flavor in reservation["flavor"].keys():
                if remaining_capacity["flavor"][req_flavor] < reservation["flavor"][req_flavor]:
                    logger.info(f'Not enough remaining "{req_flavor}" flavor.')
                    can_be_reserved = False
                    break
                else:
                    flavor_config = copy.deepcopy( capacity["initial"]["flavor"][req_flavor]["config"] )

                    for res_type, res_amount in flavor_config.items():
                        req_res_amount = res_amount * reservation["flavor"][req_flavor]

                        if req_res_amount > remaining_capacity["raw"][res_type]:
                            logger.info(f'Not enough remaining "{res_type}" resources.')
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

def ListCurrentCapacity():
    """Lists the currently available capacity to the console.
    """

    capacity = ReadCapacityRegistry()

    logger.info('Listing all resource capacities.')

    total_reserved = SummarizeAllReservations(capacity)

    print("\r\n\tType\tAll\tReserv.\t(% free)")
    
    for act_resource_type, act_resource_amount in capacity["initial"]["raw"].items():
        try:
            percentage = '{:.1%}'.format(1 - (total_reserved["raw"][act_resource_type] / act_resource_amount) )
            print(f'\t{act_resource_type.upper()}\t{act_resource_amount}\t{total_reserved["raw"][act_resource_type]}\t{percentage}')
        except KeyError:
            print(f'\t{act_resource_type.upper()}\t{act_resource_amount}\t0\t0')