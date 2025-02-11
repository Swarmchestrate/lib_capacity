import logging
import yaml

# Logger configuration
logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, 
    format='(%(asctime)s) %(levelname)s:\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

def Initialize(raw_capacity: dict = None, flavor_capacity: dict = None):


    # TO-DO: include example for usage in documentation
    # TO-DO: include option to init from yaml file

    if (raw_capacity == None and flavor_capacity == None):
        logger.error("No initial capacity defined. Please define initial resources!")
        return False
    
    logger.info('Initializing capacity registry...')

    capacity = {
        "initial": {},
        "reserved": []
        }
    capacity["initial"]["raw"] = raw_capacity
    capacity["initial"]["flavor"] = flavor_capacity
    capacity["reserved"] = []

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

def ReadCapacityRegistry():
    """Reads the capacity registry.
    """
    
    capacity_registry = {}

    with open("capreg.yaml", "r") as file:
        try:
            capacity_registry = yaml.safe_load( file )
        except yaml.YAMLError as exception:
            print(exception)
            logging.error("An error has occured!")
            # TO-DO: error handling
    
    logger.info('Loaded capacity registry.')

    return capacity_registry

def ListCurrentCapacity():
    """Lists the currently available capacity.
    """

    # TO-DO: pretty print

    capacity_registry = ReadCapacityRegistry()

    logger.info('Listing all resource capacities.')

    print(capacity_registry)