import logging
import yaml

# Logger configuration
logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, 
    format='(%(asctime)s) %(levelname)s:\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )

class CapacityRegistry:
    """Represents a capacity registry.
    
    The capacity registry handles tasks related to different capacity types (e.g. vCPU, RAM, disk, etc.).
    Tasks include reserving, freeing, freezing, etc. of the different capacity types.
    """
    
    def __init__(self):
        """Initializes a CapacityRegistry instance.
        
        The constructor relies on the "init.yaml" file, which stores the available initial capacity.
        The constructor reads "init.yaml", and initializes the capacity according to it.
        """

        self.capacity = {}

        logger.info('Initializing capacity registry...')

        with open("init.yaml", "r") as file:
            try:
                self.capacity = yaml.safe_load(file)
            except yaml.YAMLError as exception:
                print(exception)
        
        logger.info('Successfully initialized capacity registry!')