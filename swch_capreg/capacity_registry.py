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

    # TO-DO: include example for usage in documentation
    # TO-DO: include option to init from yaml file

    if (raw_capacity == None and flavor_capacity == None):
        logger.error("No initial capacity defined. Please define initial resources!")
        return False
    
    logger.info('Initializing capacity registry...')

    # TO-DO: dict values check

    # TO-DO: separate into constant
    # List of raw resource type keys: CPU, RAM, DISK, Public IP (list may change and expand)
    raw_resource_keys = ['cpu', 'ram', 'disk', 'pub_ip']

    for required_res_key in raw_resource_keys:
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

    res_ids = capacity["reservations"].keys()

    for act_res_id in res_ids:

        act_res = capacity["reservations"][act_res_id]

        for res_main_type, res_reources in act_res.items():
                
            if res_main_type == "raw":
                    
                for res_sub_type, res_amount in res_reources.items():
                    try:
                        total_reservations["raw"][res_sub_type] += res_amount
                    except KeyError:
                        total_reservations["raw"][res_sub_type] = res_amount
    
    return total_reservations

def RemainingCapacity(capacity: dict):
    """Calculates the remaining capacity of the different resources.

    Args:
        capacity (dict): A dictionary containing the initial capacities and reservations. The current capacity registry.

    Returns:
        dict: A dictionary containing the remaining capacity of the different resources, grouped by the resource types ('raw' and 'flavor').
    """

    total_reservations = SummarizeAllReservations(capacity)
    initial_capacity = capacity["initial"]

    remaining_capacity = {
        "flavor": copy.deepcopy( initial_capacity["flavor"] ),
        "raw" : copy.deepcopy( initial_capacity["raw"] )
        }
    
    for res_tpye, res_data in total_reservations.items():
        
        if res_data == {}:
            continue

        for res_subtype, res_amount in res_data.items():
            try:
                remaining_capacity[res_tpye][res_subtype] -= res_amount
            except KeyError:
                remaining_capacity[res_tpye][res_subtype] = initial_capacity[res_tpye][res_subtype]
                remaining_capacity[res_tpye][res_subtype] -= res_amount

    return remaining_capacity

def MakeReservation(reservation: dict):
    """Reserves the given resources in a reservation. Initial reservation status is "reserved", if the reservation could be made.

    A reservation can be made, only and if only, if enough resources exist for all requested resource types.

    Args:
        reservation (dict): A reservation dictionary containing the requested amount of resources.

    Returns:
        str: An empty string if the reservation could not be made. If the reservation could be made, then the ID (a UUID) of the reservation as a string.
    """
    
    def ValidateReservation(reservation: dict):
        """Validates a given reservation dictionary.

        Args:
            reservation (dict): A reservation dictionary, containing the requested resources.

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
                        else:
                            # Check if raw resource is 1 or higher
                            if reservation["raw"][sub_key] <= 0:
                                logger.error(f'Requested amount of resource "{sub_key}" is less then 1.')
                                return False
        return True

    # Check if reservation can be made
    if ValidateReservation(reservation) == True:

        capacity = ReadCapacityRegistry()

        remaining_capacity = RemainingCapacity(capacity)

        can_be_reserved = True

        for res_type, res_data in reservation.items():
            for res_subtype, res_amount in res_data.items():
                if res_amount > 0:
                    if remaining_capacity[res_type][res_subtype] < res_amount:
                        logger.error(f'Not enough remaining "{res_subtype}" resources.')
                        can_be_reserved = False
                        break
            
            if can_be_reserved == False:
                break

        if (can_be_reserved == False):
            return ""
        elif (can_be_reserved == True):
            logger.info('Enough remaining resources. Registering reservation.')

            reservation_uuid = str( uuid.uuid4() )
            logger.info(f'Reservation ID generated: {reservation_uuid}')
            
            reservation['status'] = 'reserved'

            capacity["reservations"][reservation_uuid] = reservation

            #SaveCapacityRegistry(capacity)
            
            return reservation_uuid
    else:
        logger.info("Reservation cannot be made.")
        return ""
    

def ReadCapacityRegistry():
    """Reads the capacity registry file.
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