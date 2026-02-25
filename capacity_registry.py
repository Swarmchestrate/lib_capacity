
import copy
import logging
import uuid
import yaml
from sardou import Sardou
import app_req
from res_cap import ResCap
from app_req import AppReq

"""
Data structure of the capacity registry:
capacity = {
    "swarm": {
        <swarmid>: {
            "nodes": {
                <node_name>: {
                    "flavors": {
                        <flavor_name>: {
                            "free": <amount>,
                            "reserved": <amount>,
                            "assigned": <amount>,
                            "allocated": <amount>,
                            "init": <amount>
                        }
                    }
                }
            }
        }
    },
    "cloud": {
        "type": "flavour" or "raw",
        "flavours": {
            <flavor_name>: {
                <resource_key>: <amount>,
                ...
            },
            ...
        },
        "flavour": {  # only if type is 'flavour'
            "init": {
                <flavor_name>: <amount>,
                ...
            },
            "free": {
                <flavor_name>: <amount>,
                ...
            },
            "reserved": {
                <flavor_name>: <amount>,
                ...
            },
            "assigned": {
                <flavor_name>: <amount>,
                ...
            },
            "allocated": {
                <flavor_name>: <amount>,
                ...
            }
        },
        "raw": {  # only if type is 'raw'
            "init": {
                <resource_key>: <amount>,
                ...
            },
            "free": {
                <resource_key>: <amount>,
                ...
            },
            "reserved": {
                <resource_key>: <amount>,
                ...
            },
            "assigned": {
                <resource_key>: <amount>,
                ...
            },
            "allocated": {
                <resource_key>: <amount>,
                ...
            }
        }
    }
}
"""
class SwChCapacityRegistry:

    # Logger configuration
    logger = logging.getLogger()
    logging.basicConfig(
        level=logging.DEBUG, 
        format='(%(asctime)s) %(levelname)s:\t%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    #Name of properties to be used in calculations
    calc_res_props = ["host.num-cpus", "host.mem-size", "host.disk-size"]
    calc_res_props_labels = ["CPU", "RAM", "DISK"]
    capacity: dict = {}

    RESOURCE_TYPES_RAW    = ["cpu", "ram", "disk", "pub_ip"]
    RESOURCE_TYPES_FLAVOR = ["cpu", "ram", "disk"] 

    def __init__(self):
        pass

    def extract_capacity_definitions_from_CDT(self, capacity_description_filename: str):
        tosca = Sardou(capacity_description_filename)
        return tosca.get_capacities()

    def extract_application_requirements_from_SAT(self, application_description_filename: str):
        tosca = Sardou(application_description_filename)
        nodes = tosca.raw._to_dict().get('service_template', {}).get('node_templates', {})
        requirements = dict()
        for node_name, node in nodes.items():
            if 'requirements' in node:
                requirements[node_name] = node['requirements']
        
        self.logger.debug("Requirement expression for nodes:")
        app_req = AppReq()
        requirements_logic = dict()
        for node_name, reqs in requirements.items():
            requirements_logic[node_name] = app_req.parse(reqs)
            self.logger.debug("  %s:  %s", node_name,requirements_logic[node_name])
    
        return requirements_logic

    def initialize_capacity_from_file(self, filename: str):
        tosca_capacity = self.extract_capacity_definitions_from_CDT(filename)
        self.logger.debug("Capacity read from file:\n %s", yaml.dump(tosca_capacity, default_flow_style=False))
        self.initialize(init_capacity=tosca_capacity)
        return

    def initialize(self, init_capacity: dict):
        """Initializes a capacity
        """
        self.capacity["swarm"] = dict()

        if "flavour" in init_capacity:
            self.capacity["cloud"] = dict()
            self.capacity["cloud"]["flavours"] = dict()
            rescap = ResCap()
            for act_flavor, act_flavor_data in init_capacity["flavour"].items():
                self.capacity["cloud"]["flavours"][act_flavor] = rescap.parse(act_flavor_data)
            if "capacity_flavour" in init_capacity:
                self.capacity["cloud"]["type"] = "flavour"
                self.capacity["cloud"]["flavour"] = dict()
                self.capacity["cloud"]["flavour"]["init"] = init_capacity.get("capacity_flavour", dict())
            elif "capacity_raw" in init_capacity:
                self.capacity["cloud"]["type"] = "raw"
                #temporary workaround: convert raw capacity values to int if they are not already
                init_raw_temp = init_capacity.get("capacity_raw", None)
                init_raw = dict()
                if init_raw_temp:
                    for key, value in init_raw_temp.items():
                        if isinstance(value, str) and value.isdigit():
                            init_raw["host." + key] = int(value)
                        else:
                            init_raw["host." + key] = value            
                self.capacity["cloud"]["raw"] = dict()
                self.capacity["cloud"]["raw"]["init"] = init_raw
            else:
                self.logger.info('Cloud flavour detected, but capacity is missing. Initialization was unsuccessful.')
                return False
            self.capacity["cloud"][self.capacity["cloud"]["type"]]["free"] = \
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["init"].copy()
            if self.capacity["cloud"]["type"] == "flavour":
                init_dict = self.capacity["cloud"][self.capacity["cloud"]["type"]]["init"].copy()
                for flavors in init_dict.keys():
                    init_dict[flavors] = 0
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["reserved"] = init_dict.copy()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["assigned"] = init_dict.copy()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["allocated"] = init_dict.copy() 
            if self.capacity["cloud"]["type"] == "raw":
                init_dict={}
                for prop in self.calc_res_props:
                    init_dict[prop] = 0
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["reserved"] = init_dict.copy()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["assigned"] = init_dict.copy()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["allocated"] = init_dict.copy()            
            self.logger.debug("Initialized capacity:\n %s", yaml.dump(self.capacity, default_flow_style=False))
        return True

    def calculate_matching_cloud_flavors(self, requirements: list = []):
        matching_flavors = dict()
        app_req = AppReq()
        self.logger.debug("Calculating matching cloud flavors:")
        for node in requirements.keys():
            self.logger.debug(f"  {node}")
            matching_flavors[node] = []
            for flavor_name, flavor_data in self.capacity["cloud"]["flavours"].items():
                try:
                    result = app_req.eval_app_req_with_vars(requirements[node], [flavor_data])
                    self.logger.debug(f"    {flavor_name} : {result[0]}")
                    if result[0] == True:
                        matching_flavors[node].append(flavor_name)
                except Exception as e:
                    self.logger.debug(f"Error evaluating requirement expression for cloud flavor '{flavor_name}': {e}")
        return matching_flavors
    
    def calculate_available_instances_for_cloud_flavour(self, flavor_name: str, required_instance: int = 1):
        if "cloud" not in self.capacity or "flavours" not in self.capacity["cloud"]:
            return 0
        if flavor_name not in self.capacity["cloud"]["flavours"]:
            return 0
        if self.capacity["cloud"]["type"] == "flavour":
            available_amount = self.capacity["cloud"]["flavour"]["free"].get(flavor_name, 0)
            available_instances = min(required_instance, available_amount)
            self.logger.debug(f"\tFree amount of cloud flavor '{flavor_name}': {available_amount}")
            self.logger.debug(f"\tRequired instances of cloud flavor '{flavor_name}': {required_instance}")
            self.logger.debug(f"\tAvailable instances of cloud flavor '{flavor_name}': {available_instances}")
            return available_instances
        if self.capacity["cloud"]["type"] == "raw":
            available_props = dict((prop, value) for prop, value in self.capacity["cloud"]["raw"]["free"].items() if prop in self.calc_res_props)
            self.logger.debug(f"\tFree resources for cloud flavor '{flavor_name}':")
            self.logger.debug("\t\t"+", ".join([f"{label}: {available_props.get(prop, 0)}" for label, prop in zip(self.calc_res_props_labels, self.calc_res_props)]))
            required_props_per_flavor = dict((prop, value) for prop, value in self.capacity["cloud"]["flavours"][flavor_name].items() if prop in self.calc_res_props)
            self.logger.debug(f"\tRequired resources per unit of cloud flavor '{flavor_name}':")
            self.logger.debug("\t\t"+", ".join([f"{label}: {required_props_per_flavor.get(prop, 0)}" for label, prop in zip(self.calc_res_props_labels, self.calc_res_props)]))
            self.logger.debug(f"\tRequired instances of cloud flavor '{flavor_name}': {required_instance}")
            counter, found = required_instance, False
            while counter > 0 and not found:
                found = True
                for prop in self.calc_res_props:
                    if available_props.get(prop, 0) < (required_props_per_flavor.get(prop, 0) * counter):
                        counter -= 1
                        found = False
                        break
            self.logger.debug(f"\tAvailable instances of cloud flavor '{flavor_name}': {counter}")
            self.logger.debug(f"\tCalculated amount for '{counter}' instances of cloud flavor '{flavor_name}':")
            self.logger.debug("\t\t"+", ".join([f"{label}: {required_props_per_flavor.get(prop, 0)*counter}" for label, prop in zip(self.calc_res_props_labels, self.calc_res_props)]))
            return counter
        
    def generate_offer_for_requirements(self, swarmid: str, requirement_SAT: str):
        matching_flavors = self.get_matching_cloud_flavors(requirement_SAT)
        offer = {
            "matching_flavors": matching_flavors
        }
        return offer

    def resource_state_init_amount(self, swarmid: str, msid: str, restype: str, resid: str, state: str, amount: int):
        self.logger.debug(f"Initializing resource amount: '{swarmid}', '{msid}', '{restype}', '{resid}', '{state}', {amount}")
        self.capacity["swarm"].setdefault(swarmid, dict())
        self.capacity["swarm"][swarmid].setdefault(msid, dict())
        self.capacity["swarm"][swarmid][msid].setdefault(restype, dict())
        if restype == "cloud":
            rstate = self.capacity["swarm"][swarmid][msid][restype].setdefault(resid, {"free": 0, "reserved": 0, "assigned": 0, "allocated": 0})
            rstate[state] = amount
        if restype == "edge":
            rstate = self.capacity["swarm"][swarmid][msid][restype].setdefault(resid, {"free": 1})
            rstate[state] = amount

    def resource_state_change(self, swarmid: str, msid: str, restype: str, resid: str, count: int, from_state: str, to_state: str) -> int:
        self.logger.debug(f"Changing state: '{swarmid}', '{msid}', '{restype}', '{resid}', {count}, '{from_state}', '{to_state}'")
        self.logger.debug(f"Changing state: registering swarm...")
             
        if restype == "cloud":
            rstate = self.capacity["swarm"][swarmid][msid][restype].setdefault(resid, {"free": 0, "reserved": 0, "assigned": 0, "allocated": 0})
        if restype == "edge":
            rstate = self.capacity["swarm"][swarmid][msid][restype].setdefault(resid, {"free": 1})

        if rstate[from_state] < count:
            self.logger.warning(f"Trying to change state of resource '{resid}' in swarm '{swarmid}', ms '{msid}', type '{restype}' from state '{from_state}' with count {count}, but only {rstate[from_state]} is available.")
            return None
        else:
            rstate[from_state] -= count
            rstate[to_state] += count

        self.logger.debug(f"Changing state: registering amount...")
        if restype == "cloud":   
            type = self.capacity["cloud"]["type"]
            if type == "flavour":
                self.capacity["cloud"][type][from_state][resid] -= count
                self.capacity["cloud"][type][to_state][resid] += count
            if type == "raw":
                for prop in self.calc_res_props:
                    self.capacity["cloud"]["raw"][from_state][prop] -= (self.capacity["cloud"]["flavours"][resid][prop] * count)
                    self.capacity["cloud"]["raw"][to_state][prop] += (self.capacity["cloud"]["flavours"][resid][prop] * count)
        else:
            self.logger.error(f"Unknown resource type '{restype}' for state change.")
        return count
    
    def dump_capacity_registry_info(self):
        #Dumping capacity registry information in a human-readable format
        self.logger.info('Dumping capacity registry information:')
        self.logger.info('Cloud:')
        #Dumping flavor definitions
        column_format = "\t{:25.25s}" + ("{:>10s}" * len(self.calc_res_props))
        self.logger.info(column_format.format("Flavours", *[label for label in self.calc_res_props_labels]))
        for act_flavor_type, act_flavor_data in self.capacity["cloud"]["flavours"].items():
            self.logger.info(column_format.format(
                act_flavor_type.upper(),
                *[str(act_flavor_data.get(prop, 0)) for prop in self.calc_res_props]))
        #Dumping capacity by flavour        
        if self.capacity["cloud"]["type"] == "flavour":
            self.logger.info('')
            column_format = "\t{:25.25s}{:>10s}{:>10s}{:>10s}{:>10s}{:>10s}"
            self.logger.info(column_format.format("Capacity", "Free", "Reserved", "Assigned", "Allocated", "Init"))
            for act_flavor_type, act_flavor_amount in self.capacity["cloud"]["flavour"]["init"].items():
                free = self.capacity["cloud"]["flavour"]["free"].get(act_flavor_type, 0)
                reserved = self.capacity["cloud"]["flavour"]["reserved"].get(act_flavor_type, 0)
                assigned = self.capacity["cloud"]["flavour"]["assigned"].get(act_flavor_type, 0)
                allocated = self.capacity["cloud"]["flavour"]["allocated"].get(act_flavor_type, 0)
                init = self.capacity["cloud"]["flavour"]["init"].get(act_flavor_type, 0)
                self.logger.info(column_format.format(act_flavor_type.upper(), str(free), \
                                                      str(reserved), str(assigned), str(allocated), str(init)))
        #Dumping capacity by raw
        if self.capacity["cloud"]["type"] == "raw":
            self.logger.info('')
            columns = min(len(self.calc_res_props), len(self.calc_res_props_labels))
            column_format = "\t{:25.25s}" + ("{:>10s}" * columns)
            self.logger.info(column_format.format("Capacity", *[label for label in self.calc_res_props_labels[:columns]]))
            for status in ["free", "reserved", "assigned", "allocated", "init"]:
                self.logger.info(column_format.format(
                    status.capitalize(),
                    *[str(self.capacity["cloud"]["raw"][status].get(prop, 0)) for prop in self.calc_res_props][:columns]))
                
        #Dumping swarms and reservations
        def _printaline(SwarmID='', MSID='', FlavourID='', State='', Count=''):
            self.logger.info(f"\t{SwarmID:15s} {MSID:15s} {FlavourID:20s} {State:10s}{Count:>5s}")

        self.logger.info('Swarm:')
        _printaline(SwarmID='Swarm', MSID='Microservice', FlavourID='Flavour/Edge', State='State', Count='Count')
        for swarmid, swarm in self.capacity["swarm"].items():
            _printaline(SwarmID=swarmid)
            for msid, ms in swarm.items():
                _printaline(MSID=msid)
                for _, resources in ms.items():
                    for resid, rstate in resources.items():
                        for state, count in rstate.items():
                            if count > 0:
                                _printaline(FlavourID=resid, State=state, Count=str(count))
                        
    