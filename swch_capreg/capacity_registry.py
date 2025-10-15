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
RESOURCE_TYPES_RAW    = ["cpu", "ram", "disk", "pub_ip"]        # May expand in the future
RESOURCE_TYPES_FLAVOR = ["cpu", "ram", "disk"]                  # May expand in the future

def Initialize(flavor_definition: dict, capacity_by: dict = None):
    """Initializes a capacity registry file with the given flavor definitions and
    either per-flavor amounts or raw totals.

    Args:
        flavor_definition (dict): A dictionary containing flavor (VM) types' configs
            (eg.: m1.medium, l1.large, s1.small etc.).
        capacity_by (dict, optional): Either a per-flavor amounts dict
            (e.g. {"m1.medium": 5, ...}) or a raw totals dict
            (e.g. {"cpu": 100, "ram": 100, ...}).

    Returns:
        bool: True if the initialization was successful, otherwise, False.
    """
   
    def ValidateFlavorDefinition(flavor_definition: dict):
        """Validates a given flavor definition dictionary.

        Args:
            flavor_definition (dict): A dictionary containing flavor (VM) types (eg.: m1.medium, l1.large, s1.small etc.).

        Returns:
            bool: True, if the given flavor types dictionary complies with the required format. Otherwise, False.
        """

        # Check flavor keys
        for a_flavor in flavor_definition.keys():
            # Check if key is not string
            if isinstance( a_flavor, str) == False:
                logger.error(f'Flavor "{a_flavor}" is not a string.')
                return False
            
            # Check if flavor is not dict
            if isinstance( flavor_definition[a_flavor], dict) == False:
                logger.error(f'Flavor definition for "{a_flavor}" is not a dict.')
                return False
            
            # Check if flavor is not dict
            if flavor_definition[a_flavor] == {}:
                logger.error(f'Flavor definition for "{a_flavor}" is empty.')
                return False
               
            # Check for necessary keys in flavor's config
            for resource_key in RESOURCE_TYPES_FLAVOR:
                if resource_key not in flavor_definition[a_flavor].keys():
                    logger.error(f'No resource "{resource_key}" defined for flavor "{a_flavor}".')
                    return False
            
            # Check for unknown keys in flavor's config
            for resource_key in flavor_definition[a_flavor].keys():
                if resource_key not in RESOURCE_TYPES_RAW:
                    logger.error(f'Unknown resource "{resource_key}" defined for flavor "{a_flavor}".')
                    return False
                else:
                    # Check if integer
                    if isinstance( flavor_definition[a_flavor][resource_key], int ) == False:
                        logger.error(f'Resource "{resource_key}" defined for flavor "{a_flavor}" is not an integer.')
                        return False
                    
                    # Check if bool
                    if isinstance( flavor_definition[a_flavor][resource_key], bool ) == True:
                        logger.error(f'Resource "{resource_key}" defined for flavor "{a_flavor}" is not an integer.')
                        return False
                    
                    # Check if over 1
                    if flavor_definition[a_flavor][resource_key] < 1:
                        logger.error(f'Resource "{resource_key}" must be 1 or higher for flavor "{a_flavor}".')
                        return False

    def ValidateCapacity(capacity: dict, flavor_definition: dict, raw: bool):
        """Validates a given raw capacity dictionary.

        Args:
            capacity (dict): A dictionary defining raw resources (eg.: disk, CPU, RAM, public IPs etc.).
            flavor_definition (dict): A dictionary containing flavor (VM) types (eg.: m1.medium, l1.large, s1.small etc.).
            raw (bool): Whether the capacity dict is raw totals (True) or per-flavor amounts (False).

        Returns:
            bool: True, if the given capacity dictionary complies with the required format. Otherwise, False.
        """

        # Check if empty
        if capacity == {}:
            logger.error("Input capacity is empty.")
            return False        
        # Check keys
        resource_keys = set(RESOURCE_TYPES_RAW) if raw else set(flavor_definition.keys())
        for resource in resource_keys:
            # Check if not string
            if isinstance( resource, str) == False:
                logger.error(f'Resource "{resource}" is not a string.')
                return False

            # Check if unknown raw resource type
            if raw and resource not in RESOURCE_TYPES_RAW:
                logger.error(f'Unknown raw resource type "{resource}".')
                return False
            else:
                # Check if integer
                if isinstance( capacity[resource], int ) == False:
                    logger.error(f'Resource "{resource}" is not an integer.')
                    return False
                elif isinstance( capacity[resource], bool ) == True:
                    logger.error(f'Resource "{resource}" is not an integer.')
                    return False                
                # Check if 1 or higher
                if capacity[resource] < 1:
                    logger.error(f'Amount resource "{resource}" must be 1 or higher.')
                    return False
        
        return True
    
    # Basic presence check
    if (flavor_definition == None):
        logger.error("No flavor types are defined. Please define the initial flavors!")
        return False

    # Basic presence check
    if (capacity_by == None):
        logger.error("No capacity is defined. Please define the initial capacities!")
        return False
    
    # Determine whether capacity_by contains raw totals or per-flavor amounts
    capacity_type_raw = False

    if isinstance(flavor_definition, dict) == False:
        logger.error('Parameter flavor_definition is not a dict.')
        return False
    
    if isinstance(capacity_by, dict) == False:
        logger.error('Parameter capacity_by is not a dict.')
        return False

    if not capacity_by:
        logger.error("No capacity is defined. Please define the initial capacities!")
        return False

    keys = set(capacity_by.keys())
    if keys and all(k in RESOURCE_TYPES_RAW for k in keys):
        capacity_type_raw = True
    elif keys and all(k in flavor_definition.keys() for k in keys):
        capacity_type_raw = False
    else:
        logger.error('Second parameter must be either a raw resource totals dict or a per-flavor amounts dict.')
        return False

    # Validate inputs

    # Validate flavor definitions;
    if ValidateFlavorDefinition(flavor_definition) == False:
        logger.info('Invalid input flavor definition. Initialization was unsuccessful.')
        return False

    # Validate raw totals and flavor definitions (no amounts expected in flavors)
    if ValidateCapacity(capacity_by, flavor_definition, capacity_type_raw) == False:
        logger.info('Invalid capacity definition. Initialization was unsuccessful.')
        return False
   
    logger.info('Initializing capacity registry...')
    capacity = {
        "initial": {},
        "reservations": {}
        }
    capacity["initial"]["raw"] = capacity_by if capacity_type_raw else None
    capacity["initial"]["flavor"] = flavor_definition
    capacity["initial"]["flavor_amounts"] = capacity_by if not capacity_type_raw else None

    # TO-DO: ask for permission to reinitialize
    logger.info("Saving capacity into file...")
    logger.info(f'Capacity info:\n"{capacity}"\n')
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
    
    for flavor_type in capacity["initial"]["flavor"].keys():
        total_reservations["flavor"][flavor_type] = 0

        for raw_res_type in capacity["initial"]["flavor"][flavor_type]:
            if raw_res_type not in total_reservations["raw"].keys():
                total_reservations["raw"][raw_res_type] = 0

    for reservation_id in capacity["reservations"].keys():
        
        for res_type in capacity["reservations"][reservation_id].keys():

            # May expand in the future
            if res_type == "flavor":
                for flavor_type, amount in capacity["reservations"][reservation_id][res_type].items():
                    try:
                        total_reservations["flavor"][flavor_type] += amount
                    except KeyError:
                        total_reservations["flavor"][flavor_type] = 0
                        total_reservations["flavor"][flavor_type] += amount
                    
                    for raw_res_type, config_amount in capacity["initial"]["flavor"][flavor_type].items():
                        try:
                            total_reservations["raw"][raw_res_type] += (amount * config_amount)
                        except KeyError:
                            total_reservations["raw"][raw_res_type] = 0
                            total_reservations["raw"][raw_res_type] += (amount * config_amount)
    
    return total_reservations

def RemainingCapacity(capacity: dict):
    """Calculates the remaining capacity of the different resources.

    Args:
        capacity (dict): A dictionary containing the initial capacities and reservations. The current capacity registry.

    Returns:
        dict: A dictionary containing the remaining capacity of the different resources, grouped by the main resource types (eg.: raw, flavor etc.).
    """

    total_reservations = SummarizeAllReservations(capacity)

    remaining_capacity = {
        "flavor": {},
        "raw" : {}
        }
    
    capacity_type_raw = False if capacity["initial"]["raw"] == None else True
    
    if capacity_type_raw == True:
        
        for raw_res_type in capacity["initial"]["raw"].keys():
            remaining_capacity["raw"][raw_res_type] = capacity["initial"]["raw"][raw_res_type]
        
        for flavor_type in capacity["initial"]["flavor"].keys():
            remaining_capacity["flavor"][flavor_type] = - 1

        for raw_res_type in total_reservations["raw"].keys():
            remaining_capacity["raw"][raw_res_type] -= total_reservations["raw"][raw_res_type]
        
    else:
        flavor_amounts = capacity["initial"].get("flavor_amounts")

        for flavor_type in capacity["initial"]["flavor"].keys():
            for raw_res_type in capacity["initial"]["flavor"][flavor_type].keys():
                remaining_capacity["raw"][raw_res_type] = -1

            # Read from new mapping or fallback to old inlined amount
            if flavor_amounts is not None:
                remaining_capacity["flavor"][flavor_type] = flavor_amounts.get(flavor_type, 0)
            else:
                remaining_capacity["flavor"][flavor_type] = capacity["initial"]["flavor"][flavor_type].get("amount", 0)

        for flavor_type in total_reservations["flavor"].keys():
            remaining_capacity["flavor"][flavor_type] -= total_reservations["flavor"][flavor_type]
    
    return remaining_capacity

def GetReservationOffer(res: dict):
    """Gets a reservation offer for the given flavor(s). Initial reservation status is "reserved", if the reservation could be made.

    A reservation can be made, only and if only, enough free resources exist for the requested resource types.
    
    Args:
        res (dict): A reservation dictionary containing the requested resources and their amount.

    Returns:
        str: An empty string if the reservation cannot be made. If the reservation can be made, then the ID (a UUID) of the reservation as a string.
    """

    reservation = copy.deepcopy( res )

    capacity = ReadCapacityRegistry()
    
    def ValidateReservation(reservation: dict):
        """Validates a given reservation dictionary.

        Args:
            reservation (dict): A reservation dictionary, containing the requested flavor type(s) and their amount.

        Returns:
            bool: True, if the given reservation dictionary complies with the required format. Otherwise, False.
        """

        # Check reservation type
        if isinstance( reservation, dict ) == False:
            logger.error('Reservation is not in a dictionary format.')
            return False
        
        # Check for empty dict
        if reservation == {}:
            logger.error('Empty reservation dictionary.')
            return False
        
        # Check keys reservation
        if "flavor" not in reservation.keys():
            logger.error('No "flavor" key defined in the reservation.')
            return False
        else:
            if len( reservation.keys() ) > 1:
                logger.error('Too many keys defined in the reservation.')
                return False
            
            # Check if flavor reservation is dict
            if isinstance( reservation["flavor"], dict ) == False:
                logger.error('Flavor reservation is not in a dictionary format.')
                return False
        
            # Check for empty dict
            if reservation["flavor"] == {}:
                logger.error('Empty flavor reservation dictionary.')
                return False

            # Check for invalid flavor
            flavor_types = capacity["initial"]["flavor"].keys()
            for req_flavor in reservation["flavor"].keys():

                # Check if flavor type is string
                if isinstance(req_flavor, str) == False:
                    logger.error(f'Flavor type "{req_flavor}" is not a string.')
                    return False

                if req_flavor not in flavor_types:
                    logger.error(f'Unrecognized flavor type "{req_flavor}" requested.')
                    return False
            
                # Check if flavor amount is not integer
                if isinstance( reservation["flavor"][req_flavor], int) == False:
                    logger.error(f'The requested amount of flavor "{req_flavor}" is not an integer.')
                    return False
                
                elif isinstance( reservation["flavor"][req_flavor], bool) == True:
                    logger.error(f'The requested amount of flavor "{req_flavor}" is not an integer.')
                    return False
                
                else:
                    # Check if flavor amount is 1 or higher
                    if reservation["flavor"][req_flavor] <= 0:
                        logger.error(f'The requested amount of flavor "{req_flavor}" is less than 1.')
                        return False

        return True               
    
    # Check if reservation can be made
    if ValidateReservation(reservation) == True:

        remaining_capacity = RemainingCapacity(capacity)
        can_be_reserved = True

        for req_res_type in reservation.keys():

            if req_res_type == "flavor":
                
                capacity_type_raw = False if capacity["initial"]["raw"] == None else True

                if capacity_type_raw == True:
                    for req_flavor in reservation["flavor"].keys():
                        flavor_config = copy.deepcopy( capacity["initial"]["flavor"][req_flavor] )

                        for res_type, res_amount in flavor_config.items():

                            req_res_amount = res_amount * reservation["flavor"][req_flavor]

                            if req_res_amount > remaining_capacity["raw"][res_type]:
                                logger.warning(f'Not enough remaining "{res_type}" resources.')
                                can_be_reserved = False
                                break
                    
                        if can_be_reserved == False:
                            break
                
                else:
                    for req_flavor in reservation["flavor"].keys():
                        
                        if reservation["flavor"][req_flavor] > remaining_capacity["flavor"][req_flavor]:
                            logger.warning(f'Not enough remaining "{req_flavor}" flavor.')
                            can_be_reserved = False
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
      
def DoesReservationExist(reservation_id: str, capacity: dict = None):
    """Check if the given a given reservation exists with the given ID (UUID).

    Args:
        reservation_id (str): A reservation ID (UUID).
        capacity (dict, optional): A dictionary containing the initial capacities and reservations. The current capacity registry. Defaults to None.

    Returns:
        bool: True, if the a reservation with the given ID exists in the capacity registry. Otherwise, False.
    """

    if (capacity == None):
        capacity = ReadCapacityRegistry()

    if isinstance( reservation_id, str) == False:
        logger.error(f'Given reservation ID is not a string.')
        return False

    if reservation_id == "":
        logger.warning(f'Given reservation ID is empty.')
        return False

    if reservation_id in capacity["reservations"].keys():
        logger.info(f'Reservation with ID "{reservation_id}" exists.')
        return True
    else:
        logger.info(f'Reservation with ID "{reservation_id}" not found.')
        return False

def AcceptOfferedReservation(reservation_id: str):
    """Accepts a reservation, making its status 'assigned'.

    Args:
        reservation_id (str): A reservation ID (UUID).

    Returns:
        bool: True, if the reservation could be accepted. Otherwise, False.
    """

    capacity = ReadCapacityRegistry()
    reservation_exists = DoesReservationExist(reservation_id, capacity)
    
    if reservation_exists != True:
        return False
    else:
        if capacity["reservations"][reservation_id]["status"] != "reserved":
            logger.warning(f'Reservation with ID "{reservation_id}" is not in "reserved" status.')
            return False
        
        capacity["reservations"][reservation_id]["status"] = "assigned"
        logger.info(f'Reservation "{reservation_id}" found. Reservation accepted. Reservation status updated to "assigned".')
        
        SaveCapacityRegistry(capacity)

        return True
    
def RejectOfferedReservation(reservation_id: str):
    """Rejects a reservation, freeing all related resources.

    Args:
        reservation_id (str): A reservation ID (UUID).

    Returns:
        bool: True, if the reservation was rejected successfully. Otherwise, False.
    """

    capacity = ReadCapacityRegistry()
    reservation_exists = DoesReservationExist(reservation_id, capacity)
    
    if reservation_exists != True:
        return False
    else:
        if capacity["reservations"][reservation_id]["status"] != "reserved":
            logger.warning(f'Reservation with ID "{reservation_id}" is not in "reserved" status.')
            return False
        
        del capacity["reservations"][reservation_id]
        logger.info(f'Reservation "{reservation_id}" found. Reservation rejected, reserved resources are freed.')
        
        SaveCapacityRegistry(capacity)

        return True

def AppHasBeenDestroyed(reservation_id: str):
    """Frees up a reservation (and related resources) that is in the "assigned" or "reserved" state. Deletes the reservation from the capacity registry.

    Args:
        reservation_id (str): A reservation ID (UUID).

    Returns:
        bool: True, if the reservation was deleted successfully. Otherwise, False.
    """

    capacity = ReadCapacityRegistry()
    reservation_exists = DoesReservationExist(reservation_id, capacity)

    if reservation_exists != True:
        return False
    else:
        if (capacity["reservations"][reservation_id]["status"] not in ["assigned", "reserved"]):
            logger.warning(f'Reservation with ID "{reservation_id}" is not in "assigned" or "reserved" status.')
            return False
        
        del capacity["reservations"][reservation_id]
        logger.info(f'Reservation "{reservation_id}" found. Reservation destroyed, reserved resources are freed.')
        
        SaveCapacityRegistry(capacity)

        return True

def AllocateReservation(reservation_id: str):
    """Makes a reservation move to the "allocated" state.

    Args:
        reservation_id (str): A reservation ID (UUID).

    Returns:
        bool: True, if the reservation could be moved to the allocated state. Otherwise, False.
    """

    capacity = ReadCapacityRegistry()
    reservation_exists = DoesReservationExist(reservation_id, capacity)

    if reservation_exists != True:
        return False
    else:
        if capacity["reservations"][reservation_id]["status"] != "assigned":
            logger.warning(f'Reservation with ID "{reservation_id}" is not in "assigned" status.')
            return False
        
        capacity["reservations"][reservation_id]["status"] = "allocated"
        logger.info(f'Reservation "{reservation_id}" found. Reservation status updated to "allocated".')
        
        SaveCapacityRegistry(capacity)

        return True

def DeallocateReservation(reservation_id: str):

    capacity = ReadCapacityRegistry()
    reservation_exists = DoesReservationExist(reservation_id, capacity)

    if reservation_exists != True:
        return False
    else:
        if capacity["reservations"][reservation_id]["status"] != "allocated":
            logger.warning(f'Reservation with ID "{reservation_id}" is not in "allocated" status.')
            return False
        
        capacity["reservations"][reservation_id]["status"] = "assigned"
        logger.info(f'Reservation "{reservation_id}" found. Reservation status updated to "assigned".')
        
        SaveCapacityRegistry(capacity)

        return True

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
        capacity (dict): A dictionary containing the initial capacities and reservations. The current capacity registry.

    Returns:
        bool: True if saving was successful. False if an error has occurred.
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

def GetReservationInfo(reservation_id: str):
    """Lists information about a given reservation.

    Args:
        reservation_id (str): A reservation ID (UUID).
    
    Returns:
        dict: A dictionary containing information about the reservation (Id, status, used resources etc.). Otherwise, an empty ({}) dictionary.
    """

    def SumReservationResources(reservation_id: str, capacity: dict):

        # TO-DO: function documentation
        total_reservations = {
            "flavor": {},
            "raw": {}
        }

        for flavor_type in capacity["reservations"][reservation_id]["flavor"].keys():
            total_reservations["flavor"][flavor_type] = 0

            for raw_res_type in capacity["initial"]["flavor"][flavor_type]:
                if raw_res_type not in total_reservations["raw"].keys():
                    total_reservations["raw"][raw_res_type] = 0

        for res_type in capacity["reservations"][reservation_id].keys():

            # May expand in the future
            if res_type == "flavor":
                for flavor_type, amount in capacity["reservations"][reservation_id][res_type].items():
                    try:
                        total_reservations["flavor"][flavor_type] += amount
                    except KeyError:
                        total_reservations["flavor"][flavor_type] = 0
                        total_reservations["flavor"][flavor_type] += amount
                    
                    for raw_res_type, config_amount in capacity["initial"]["flavor"][flavor_type].items():
                        try:
                            total_reservations["raw"][raw_res_type] += (amount * config_amount)
                        except KeyError:
                            total_reservations["raw"][raw_res_type] = 0
                            total_reservations["raw"][raw_res_type] += (amount * config_amount)
            
            return total_reservations

    capacity = ReadCapacityRegistry()
    reservation_exists = DoesReservationExist(reservation_id, capacity)

    if reservation_exists != True:
        return {}
    else:
        res_resources = SumReservationResources(reservation_id, capacity)
        
        reservation_info = {
            'id': reservation_id,
            'status': capacity["reservations"][reservation_id]['status'],
            'flavor': res_resources['flavor'],
            'raw': res_resources['raw']
            }

        logger.info('Listing reservation information.')
        print(f'\r\n\tId: {reservation_info["id"]}')
        print(f'\tStatus: {reservation_info["status"]}')
        print('\tFlavor(s):')

        for flavor, amount in reservation_info['flavor'].items():
            print(f'\t\t- {flavor.upper()}: {amount}')

        print('\r\n\tRaw resources:')
        
        for res, amount in reservation_info['raw'].items():
            print(f'\t\t- {res.upper()}: {amount}')

        print()

        return reservation_info

def GetCapacityRegistryInfo():
    """Lists information about the current capacity registry.
    """

    capacity = ReadCapacityRegistry()
    total_reserved = SummarizeAllReservations(capacity)
    no_of_reservations = len( capacity["reservations"].keys() )

    logger.info('Listing capacity registry information.')
    print(f"\r\n\tFlavor definitions:")
    print("\tFlavor\t\tCPU\tDISK\tRAM\tPUB_IP")
    for act_flavor_type, act_flavor_data in capacity["initial"]["flavor"].items():
        print(f'\t{act_flavor_type.upper()}',end='')
        print(f'\t{act_flavor_data["cpu"]}',end='')
        print(f'\t{act_flavor_data["disk"]}',end='')
        print(f'\t{act_flavor_data["ram"]}',end='')
        print(f'\t{act_flavor_data["pub_ip"] if "pub_ip" in act_flavor_data else ""}')

    print(f"\r\n\tReservations:\t{no_of_reservations}")
    for id, value in capacity["reservations"].items():
        print(f'\t{id.upper()}')
        print(f'\t\t{value["status"]}')
        print(f'\t\t',end='')
        for key, value in value["flavor"].items():
            print(f'{key.upper()}: {value}',end=' ')
        print()

    if (capacity["initial"]["raw"] is not None):
        # Listing raw resources  
        print("\r\n\tCapacity by raw:")
        print("\tType\t\tAll\tReserv.\tFree\t(% free)")
        for act_resource_type, act_resource_amount in capacity["initial"]["raw"].items():
            try:
                percentage = '{:.1%}'.format(1 - (total_reserved["raw"][act_resource_type] / act_resource_amount) )
                free = act_resource_amount - total_reserved["raw"][act_resource_type]
                print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t{total_reserved["raw"][act_resource_type]}\t{free}\t{percentage}')
            except KeyError:
                print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t0\t0')
    else:
        # Listing flavor resources
        print("\r\n\tCapacity by flavors:")
        print("\tFlavor\t\tAll\tReserv.\tFree\t(% free)")
        for act_flavor_type, act_flavor_data in capacity["initial"]["flavor"].items():
            percentage = 0
            free = 0
            cap_amount = capacity['initial'].get('flavor_amounts', {}).get(act_flavor_type, None)
            try:
                percentage = '{:.1%}'.format(1 - (total_reserved["flavor"][act_flavor_type] / cap_amount) )
                free = cap_amount - total_reserved["flavor"][act_flavor_type]
                print(f'\t{act_flavor_type.upper()}\t{cap_amount}\t{total_reserved["flavor"][act_flavor_type]}\t{free}\t{percentage}')
            except KeyError:
                percentage = "n/a"
                free = "n/a"
                print(f'\t{act_flavor_type.upper()}\tn/a\t{total_reserved["flavor"][act_flavor_type]}\t{free}\t{percentage}')
    
    print()