import logging
import yaml

# Logger configuration
logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, 
    format='(%(asctime)s) %(levelname)s:\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

def Initialize(init_capacity: dict):
    """Initializes the capacity registry.

    Args:
        init_capacity (dict): A dictionary containing different resource types, eg.: disk, RAM, CPU etc.
    """

    # TO-DO: include example for usage in documentation
    
    logger.info('Initializing capacity registry...')

    with open("capreg.yaml", "w") as file:
        try:
            file.write( yaml.dump(init_capacity) )
        except yaml.YAMLError as exception:
            print(exception)
            logging.error("An error has occured!")
            # TO-DO: error handling
        
    logger.info('Successfully initialized capacity registry!')

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