
import copy
from itertools import count
import logging
import yaml
from sardou import Sardou
from .res_cap import ResCap
from .app_req import AppReq

"""
Data structure of the capacity registry:
capacity = {
    "swarms": {
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

    def __init__(self, ra_id: str, logger: logging.Logger | None = None):
        self.ra_id = ra_id
        self.logger = logger if logger is not None else self.__class__.logger

    def extract_capacity_definitions_from_CDT(self, capacity_description_filename: str):
        tosca = Sardou(capacity_description_filename)
        return tosca.get_capacities()

    def extract_application_requirements_from_SAT_file(self, application_description_filename: str):
        self.logger.debug(f"Extracting application requirements from '{application_description_filename}'...")
        tosca = Sardou(application_description_filename)

        return tosca.get_requirements()

    def initialize_capacity_by_content(self, content: str):
        # FIXME: This is a workaround to initialize the capacity registry from content instead of file,
        # since Sardou currently support reading from physical file. Remove this workaround once Sardou 
        # is fixed to support reading from content directly.
        import tempfile
        CDTtempfile = tempfile.NamedTemporaryFile(prefix='SWCH_CDT_', suffix='.yaml', dir='/tmp')
        try:
            with open(CDTtempfile.name, 'w') as f:
                f.write(content)
            self.initialize_capacity_from_file(CDTtempfile.name)
        finally:
            CDTtempfile.close()
        return

    def initialize_capacity_from_file(self, filename: str):
        tosca_capacity = self.extract_capacity_definitions_from_CDT(filename)
        # FIXME: a workaround to test edge capacity handling, 
        # the next 4 lines must be removed once Sardou is fixed.
        a_flavor = list(tosca_capacity["flavour"].keys())[0]
        if tosca_capacity["flavour"].get(a_flavor, {}).get("resource", {}).get("type", "") == "edge":
            del tosca_capacity["capacity_flavour"]
            tosca_capacity["edge"] = tosca_capacity.pop("flavour")
        self.logger.debug("Capacity read from file:\n %s", yaml.dump(tosca_capacity, default_flow_style=False))
        self.initialize(init_capacity=tosca_capacity)
        return

    def initialize(self, init_capacity: dict):
        """Initializes a capacity
        """
        self.capacity["swarms"] = dict()
        self.capacity["offers"] = dict()

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
        if "edge" in init_capacity:
            self.capacity["edge"] = dict()
            self.capacity["edge"]["capacities"] = dict()
            rescap = ResCap()
            for act_instance, act_instance_data in init_capacity["edge"].items():
                self.capacity["edge"]["capacities"][act_instance] = rescap.parse(act_instance_data)

            init_dict = self.capacity["edge"]["capacities"].copy()
            self.capacity["edge"]["instances"] = dict()
            for instance in init_dict.keys():
                init_dict[instance] = 1
            self.capacity["edge"]["instances"]["init"] = init_dict.copy()
            self.capacity["edge"]["instances"]["free"] = init_dict.copy()
            for instance in init_dict.keys():
                init_dict[instance] = 0
            self.capacity["edge"]["instances"]["reserved"] = init_dict.copy()
            self.capacity["edge"]["instances"]["assigned"] = init_dict.copy()
            self.capacity["edge"]["instances"]["allocated"] = init_dict.copy() 
            self.logger.debug("Initialized capacity:\n %s", yaml.dump(self.capacity, default_flow_style=False))
        return True

    def calculate_matching_resources(self, requirements: list = []):
        matching_resources = dict()
        app_req = AppReq()
        self.logger.debug("Calculating matching cloud flavors and edge instances:")
        for msid in requirements.keys():
            self.logger.debug(f"\t{msid}")
            matching_resources[msid] = []
            if "cloud" in self.capacity:
                for flavor_name, flavor_data in self.capacity["cloud"]["flavours"].items():
                    try:
                        result = app_req.eval_app_req_with_vars(requirements[msid]["expression"], [flavor_data])
                        self.logger.debug(f"\t\t{flavor_name} : {result[0]}")
                        if result[0] == True:
                            matching_resources[msid].append({"cloud":flavor_name})
                    except Exception as e:
                        self.logger.debug(f"\t\tError evaluating requirement expression for cloud flavor '{flavor_name}': {e}")
            if "edge" in self.capacity:
                for instance_name, instance_data in self.capacity["edge"]["capacities"].items():
                    try:
                        result = app_req.eval_app_req_with_vars(requirements[msid]["expression"], [instance_data])
                        self.logger.debug(f"\t\t{instance_name} : {result[0]}")
                        if result[0] == True:
                            matching_resources[msid].append({"edge":instance_name})
                    except Exception as e:
                        self.logger.debug(f"\t\tError evaluating requirement expression for edge instance '{instance_name}': {e}")
        return matching_resources
    
    def calculate_available_instances_of_resources(self, res_type: str, res_name: str, required_instance: int = 1):
        self.logger.debug(f"Calculating available instances for {res_type} '{res_name}' with required instance count {required_instance}...")
        if res_type == "cloud":
            if "cloud" not in self.capacity or "flavours" not in self.capacity["cloud"]:
                return 0
            if res_name not in self.capacity["cloud"]["flavours"]:
                return 0
            if self.capacity["cloud"]["type"] == "flavour":
                available_amount = self.capacity["cloud"]["flavour"]["free"].get(res_name, 0)
                available_instances = min(required_instance, available_amount)
                self.logger.debug(f"\tFree amount of cloud flavor '{res_name}': {available_amount}")
                self.logger.debug(f"\tRequired instances of cloud flavor '{res_name}': {required_instance}")
                self.logger.debug(f"\tAvailable instances of cloud flavor '{res_name}': {available_instances}")
                return available_instances
            if self.capacity["cloud"]["type"] == "raw":
                available_props = dict((prop, value) for prop, value in self.capacity["cloud"]["raw"]["free"].items() if prop in self.calc_res_props)
                self.logger.debug(f"\tFree resources for cloud flavor '{res_name}':")
                self.logger.debug("\t\t"+", ".join([f"{label}: {available_props.get(prop, 0)}" for label, prop in zip(self.calc_res_props_labels, self.calc_res_props)]))
                required_props_per_flavor = dict((prop, value) for prop, value in self.capacity["cloud"]["flavours"][res_name].items() if prop in self.calc_res_props)
                self.logger.debug(f"\tRequired resources per unit of cloud flavor '{res_name}':")
                self.logger.debug("\t\t"+", ".join([f"{label}: {required_props_per_flavor.get(prop, 0)}" for label, prop in zip(self.calc_res_props_labels, self.calc_res_props)]))
                self.logger.debug(f"\tRequired instances of cloud flavor '{res_name}': {required_instance}")
                counter, found = required_instance, False
                while counter > 0 and not found:
                    found = True
                    for prop in self.calc_res_props:
                        if available_props.get(prop, 0) < (required_props_per_flavor.get(prop, 0) * counter):
                            counter -= 1
                            found = False
                            break
                self.logger.debug(f"\tAvailable instances of cloud flavor '{res_name}': {counter}")
                self.logger.debug(f"\tCalculated amount for '{counter}' instances of cloud flavor '{res_name}':")
                self.logger.debug("\t\t"+", ".join([f"{label}: {required_props_per_flavor.get(prop, 0)*counter}" for label, prop in zip(self.calc_res_props_labels, self.calc_res_props)]))
                return counter
        if res_type == "edge":
            if "edge" not in self.capacity or "instances" not in self.capacity["edge"]:
                return 0
            if res_name not in self.capacity["edge"]["capacities"]:
                return 0
            available_amount = self.capacity["edge"]["instances"]["free"].get(res_name, 0)
            available_instances = min(required_instance, available_amount)
            self.logger.debug(f"\tFree amount of edge instance '{res_name}': {available_amount}")
            self.logger.debug(f"\tRequired instances of edge instance '{res_name}': {required_instance}")
            self.logger.debug(f"\tAvailable instances of edge instance '{res_name}': {available_instances}")
            return available_instances
        return 0
        
    def resource_state_init_amount(self, swarmid: str, msid: str, restype: str, resid: str, state: str, amount: int):
        self.logger.debug(f"Initializing resource amount: '{swarmid}', '{msid}', '{restype}', '{resid}', '{state}', {amount}")
        self.capacity["swarms"].setdefault(swarmid, dict())
        self.capacity["swarms"][swarmid].setdefault(msid, dict())
        self.capacity["swarms"][swarmid][msid].setdefault(restype, dict())
        rstate = self.capacity["swarms"][swarmid][msid][restype].setdefault(resid, {"free": 0, "reserved": 0, "assigned": 0, "allocated": 0})
        rstate[state] = amount
        return amount

    def resource_state_change(self, swarmid: str, msid: str, restype: str, resid: str, count: int, from_state: str, to_state: str) -> int:
        self.logger.debug(f"Changing state: '{swarmid}', '{msid}', '{restype}', '{resid}', {count}, '{from_state}', '{to_state}'")
        rstate = self.capacity["swarms"][swarmid][msid][restype][resid]
        if rstate[from_state] < count:
            self.logger.warning(f"Trying to change state of resource '{resid}' in swarm '{swarmid}', ms '{msid}', type '{restype}' from state '{from_state}' with count {count}, but only {rstate[from_state]} is available.")
            return None
        else:
            rstate[from_state] -= count
            if to_state != "free":
                rstate[to_state] += count
        if restype == "cloud":   
            type = self.capacity["cloud"]["type"]
            if type == "flavour":
                self.capacity["cloud"][type][from_state][resid] -= count
                self.capacity["cloud"][type][to_state][resid] += count
            if type == "raw":
                for prop in self.calc_res_props:
                    self.capacity["cloud"]["raw"][from_state][prop] -= (self.capacity["cloud"]["flavours"][resid][prop] * count)
                    self.capacity["cloud"]["raw"][to_state][prop] += (self.capacity["cloud"]["flavours"][resid][prop] * count)
        if restype == "edge":   
            self.capacity["edge"]["instances"][from_state][resid] -= count
            self.capacity["edge"]["instances"][to_state][resid] += count
        return count
    
    def resource_set_deployed(self, swarmid: str, msid: str, restype: str, resid: str, count: int):
        self.logger.debug(f"Setting resource as deployed: '{swarmid}', '{msid}', '{restype}', '{resid}', {count}")
        count = self.resource_state_change(swarmid, msid, restype, resid, count, "assigned", "allocated")        
        return count

    def resource_set_undeployed(self, swarmid: str, msid: str, restype: str, resid: str, count: int):
        self.logger.debug(f"Setting resource as undeployed: '{swarmid}', '{msid}', '{restype}', '{resid}', {count}")
        count = self.resource_state_change(swarmid, msid, restype, resid, count, "allocated", "assigned")        
        return count

    def resource_set_get_from_offer(self, offerid: str, offer: list | dict):
        if offerid == "colocated":
            self.logger.warning(f"Offerid '{offerid}' is a colocation.")
            return None
        offers = list([offer]) if isinstance(offer, dict) else offer
        res_set = dict()
        res_set['swarmid'] = offer["ids"]["swarm_id"]
        res_set['msid'] = offer["ids"]["ms_id"]
        res_set['resid'] = offer["ids"]["res_id"]
        res_set['restype'] = offer["ids"]["res_type"]
        res_set['count'] = len(offers) if isinstance(offer, list) else 1
        return res_set
    
    def resource_set_query_all(self, swarmid: str, msid: str=None):
        return copy.deepcopy(self.capacity.get("swarms", {}).get(swarmid, {}).get(msid, {}) if msid else self.capacity.get("swarms", {}).get(swarmid, {}))
    

    def resource_offer_generate_by_SAT_content(self, swarmid: str, sat_content: str):
        import tempfile
        SATtempfile = tempfile.NamedTemporaryFile(prefix='SWCH_SAT_', suffix='.yaml', dir='/tmp')
        try:
            with open(SATtempfile.name, 'w') as f:
                f.write(sat_content)
            return self.resource_offer_generate_from_SAT_file(swarmid, SATtempfile.name)
        finally:
            SATtempfile.close()

    def resource_offer_generate_from_SAT_file(self, swarmid: str, sat_filename: str):
        import random
        self.logger.debug(f"Generating offer for swarm '{swarmid}' with requirements from '{sat_filename}'...")
        reqs = self.extract_application_requirements_from_SAT_file(sat_filename)
        matching_resources = self.calculate_matching_resources(reqs)
        offers = dict()
        for msid, matching_resources in matching_resources.items():
            #instance_count_required=random.randint(1,2) #FIX: should read this number from SAT, currently unspecified
            instance_count_required = 1
            for resource in matching_resources:
                resource_type = list(resource.keys())[0]
                resource_name = resource[resource_type]
                self.logger.debug(f"AAAAAA '{resource_name}' of type '{resource_type}' for ms '{msid}' with required instance count {instance_count_required}...")
                available_instances = self.calculate_available_instances_of_resources(resource_type, resource_name, instance_count_required)
                if available_instances >= instance_count_required:
                    self.resource_state_init_amount(swarmid, msid, resource_type, resource_name, "free", available_instances)
                    self.resource_state_change(swarmid, msid, resource_type, resource_name, available_instances, "free", "reserved")
                    #query provider information for the flavor
                    flavor_or_edge = "flavours" if resource_type == "cloud" else "capacities"
                    self.logger.debug(f"BBBBBB '{flavor_or_edge}' of type '{resource_type}'...")
                    provider_id = self.capacity[resource_type][flavor_or_edge][resource_name]["resource.provider"]
                    #query characteristics for the flavor
                    characteristic_names = ["pricing.cost",
                                            "energy.consumption",
                                            "host.bandwidth"]
                    characteristics = dict()
                    for characteristic_name in characteristic_names:
                        characteristics[characteristic_name] = self.capacity[resource_type][flavor_or_edge][resource_name].get(characteristic_name, None)
                    #compose offer
                    offerid = self.ra_id + "_" + swarmid + "_" + msid + "_" + resource_name
                    if available_instances > 1:
                        instance_list = list() 
                        for instance_index in range(available_instances):
                            instance_list.append(dict({
                                    "ids": {
                                        "offer_id": offerid+"_"+str(instance_index),
                                        "ra_id": self.ra_id,
                                        "swarm_id": swarmid,
                                        "ms_id": msid,
                                        "provider_id": provider_id,
                                        "res_type": resource_type,
                                        "res_id": resource_name
                                    },
                                    "characteristics": characteristics,
                                    "properties": reqs[msid].get("properties", {})}))
                        offers.setdefault(msid,dict())
                        offers[msid][offerid]=instance_list
                    else:
                        offers.setdefault(msid,dict())
                        offers[msid][offerid]=dict({
                                    "ids": {
                                        "offer_id": offerid,
                                        "ra_id": self.ra_id,
                                        "swarm_id": swarmid,
                                        "ms_id": msid,
                                        "provider_id": provider_id,
                                        "res_type": resource_type,
                                        "res_id": resource_name
                                    },
                                    "characteristics": characteristics,
                                    "properties": reqs[msid].get("properties", {})})
            if reqs[msid].get("colocated", []):
                for col_node in reqs[msid]["colocated"]:
                    offers[col_node]= dict({"colocated": msid})
        self.logger.debug(f"Generating offer for swarm '{swarmid}' with requirements from '{sat_filename}' finished.")
        self.capacity["offers"]=dict()
        self.capacity["offers"][swarmid]=offers
        return offers
    
    def resource_offer_query_all(self, swarmid: str):
        return copy.deepcopy(self.capacity.get("offers", {}).get(swarmid, {}))

    def resource_offer_accept(self, offerid: str, offer: list | dict):
        if offerid == "colocated":
            self.logger.warning(f"Offerid '{offerid}' is a colocation, skipping state change.")
            return True
        offers = list([offer]) if isinstance(offer, dict) else offer
        for offer in offers:
            swarmid = offer["ids"]["swarm_id"]
            msid = offer["ids"]["ms_id"]
            resid = offer["ids"]["res_id"]
            restype = offer["ids"]["res_type"]
            # Change state of resource from reserved to assigned
            if self.resource_state_change(swarmid, msid, restype, resid, 1, "reserved", "assigned"):
                self.logger.debug(f"Accepting offer '{offerid}' for swarm '{swarmid}' succeeded.")
            else:
                self.logger.error(f"Failed to change state for resource in offer '{offerid}' for swarm '{swarmid}'")
                return False
        return True

    def resource_offer_reject(self, offerid: str, offer: list | dict):
        if offerid == "colocated":
            self.logger.warning(f"Offerid '{offerid}' is a colocation, skipping state change.")
            return True
        offers = list([offer]) if isinstance(offer, dict) else offer
        for offer in offers:
            swarmid = offer["ids"]["swarm_id"]
            msid = offer["ids"]["ms_id"]
            resid = offer["ids"]["res_id"]
            restype = offer["ids"]["res_type"]
            # Change state of resource from reserved to free
            if self.resource_state_change(swarmid, msid, restype, resid, 1, "reserved", "free"):
                del self.capacity["offers"][swarmid][msid][offerid]
                self.logger.debug(f"Rejecting offer '{offerid}' for swarm '{swarmid}' succeeded.")
            else:
                self.logger.error(f"Rejecting offer '{offerid}' for swarm '{swarmid}' failed.")
                return False
        return True

    def resources_and_offers_destroy_all(self, swarmid: str):
        swarm = self.capacity["swarms"].get(swarmid, {})
        for msid, ms in swarm.items():
            for restype, resources in ms.items():
                for resid, rstate in resources.items():
                    for state, count in rstate.items():
                        if count > 0:
                            self.logger.debug(f"Releasing resource: '{swarmid}', '{msid}', '{restype}', '{resid}', '{state}': {count}")
                            self.resource_state_change(swarmid, msid, restype, resid, count, state, "free")
        del self.capacity["offers"][swarmid]
        del self.capacity["swarms"][swarmid]
        return True

    def dump_capacity_registry_info(self):
        #Dumping capacity registry information in a human-readable format
        self.logger.info('Dumping capacity registry information:')
        if "cloud" in self.capacity:
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

        if "edge" in self.capacity:
            self.logger.info('Edge:')
            #Dumping edge instances:
            column_format = "\t{:25.25s}" + ("{:>10s}" * len(self.calc_res_props))
            self.logger.info(column_format.format("Capacities", *[label for label in self.calc_res_props_labels]))
            for act_instance, act_instance_data in self.capacity["edge"]["capacities"].items():
                self.logger.info(column_format.format(
                    act_instance.upper(),
                    *[str(act_instance_data.get(prop, 0)) for prop in self.calc_res_props]))

            #Dumping edge status
            self.logger.info('')
            column_format = "\t{:25.25s}{:>10s}{:>10s}{:>10s}{:>10s}{:>10s}"
            self.logger.info(column_format.format("Instances", "Free", "Reserved", "Assigned", "Allocated", "Init"))
            for instance in self.capacity["edge"]["capacities"].keys():
                instance_data = self.capacity["edge"]["instances"]
                free = instance_data["free"].get(instance, 0)
                reserved = instance_data["reserved"].get(instance, 0)
                assigned = instance_data["assigned"].get(instance, 0)
                allocated = instance_data["allocated"].get(instance, 0)
                init = instance_data["init"].get(instance, 0)
                self.logger.info(column_format.format(instance.upper(), str(free), \
                                                    str(reserved), str(assigned), str(allocated), str(init)))

        #Dumping swarms and reservations
        def _printaline(SwarmID='', MSID='', FlavourID='', State='', Count=''):
            self.logger.info(f"\t{SwarmID:15s} {MSID:15s} {FlavourID:20s} {State:10s}{Count:>5s}")

        self.logger.info('Swarm:')
        _printaline(SwarmID='Swarm', MSID='Microservice', FlavourID='Flavour/Edge', State='State', Count='Count')
        for swarmid, swarm in self.capacity["swarms"].items():
            _printaline(SwarmID=swarmid)
            for msid, ms in swarm.items():
                _printaline(MSID=msid)
                for _, resources in ms.items():
                    for resid, rstate in resources.items():
                        for state, count in rstate.items():
                            if count > 0:
                                _printaline(FlavourID=resid, State=state, Count=str(count))
                        
    