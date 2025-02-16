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

    # TO-DO: dict key check
    # TO-DO: dict values check

    capacity = {
        "initial": {},
        "reservations": {}
        }
    
    capacity["initial"]["raw"] = raw_capacity
    capacity["initial"]["flavor"] = flavor_capacity

    if "pub_ip" in capacity["initial"]["raw"].keys():
        pub_ips = {
            "pub_ips": raw_capacity["pub_ip"],
            "amount": len( raw_capacity["pub_ip"] )
            }

        capacity["initial"]["raw"]["pub_ip"] = pub_ips

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

def SummarizeAllReservations():
    """Summarizes all reserved resources.

    Returns:
        dict: A dictionary of the overall amount of reserved resources. Contains the reserved amount of raw and flavor type resources.
    """
    
    # TO-DO: function documentation

    capacity = ReadCapacityRegistry()

    total_reservations = {"raw": {}, "flavor": {}}

    res_ids = capacity["reservations"].keys()

    for act_res_id in res_ids:

        act_res = capacity["reservations"][act_res_id]

        for res_main_type, res_reources in act_res.items():
                
            if res_main_type == "raw":
                    
                for res_sub_type, res_amount in res_reources.items():
                    # TO-DO: count reserved IP addresses

                    try:
                        total_reservations["raw"][res_sub_type] += res_amount
                    except KeyError:
                        total_reservations["raw"][res_sub_type] = res_amount
    
    return total_reservations
            
def MakeReservation(reservation: dict):
    
    # TO-DO: function documentation
    # TO-DO: dict key check
    # TO-DO: dict value check
    reservation_uuid = str( uuid.uuid4() )

    capacity = ReadCapacityRegistry()

    can_be_reserved = True

    for reservation_type in reservation.keys():
        print(reservation_type)

    #reservation = {
    #    reservation_uuid: reservation
    #    }

    # if ...
    capacity["reservations"][reservation_uuid] = reservation

    # Check if reservation can be made
    # If it can be made, make the reservation and return (True, reservation_uuid)
    # If it cannot be made, return (False, None)

    SaveCapacityRegistry(capacity)
    

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
    # TO-DO: function documentation
    # TO-DO: dict key check
    # TO-DO: dict value check
    
    with open("capreg.yaml", "w") as file:
        try:
            file.write( yaml.dump(capacity) )
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

    total_reserved = SummarizeAllReservations()

    print("\r\n\tType\t\tAll\tReserved\t(% reserved)")
    
    for act_resource_type, act_resource_amount in capacity["initial"]["raw"].items():
        if (act_resource_type != 'pub_ip'):
            print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t{total_reserved["raw"][act_resource_type]}')
        else:
            print(f'\tPub.IP\t\t{ len(act_resource_amount["pub_ips"]) }')