
import copy
import logging
import uuid
import yaml
from sardou import Sardou
import app_req
from res_cap import ResCap
from app_req import AppReq

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
        
        app_req = AppReq()
        requirements_logic = app_req.parse(requirements)
        self.logger.debug("Requirement expression:")
        self.logger.debug("  %s", requirements_logic)
    
        return requirements_logic

    def initialize_capacity_from_file(self, filename: str):
        tosca_capacity = self.extract_capacity_definitions_from_CDT(filename)
        self.logger.debug("Capacity read from file:\n %s", yaml.dump(tosca_capacity, default_flow_style=False))
        self.initialize(init_capacity=tosca_capacity)
        return

    def initialize(self, init_capacity: dict):
        """Initializes a capacity
        """
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
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["reserved"] = dict()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["assigned"] = dict()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["allocated"] = dict()            
            if self.capacity["cloud"]["type"] == "raw":
                init_dict={}
                for prop in self.calc_res_props:
                    init_dict[prop] = 0
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["reserved"] = init_dict.copy()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["assigned"] = init_dict.copy()
                self.capacity["cloud"][self.capacity["cloud"]["type"]]["allocated"] = init_dict.copy()            
            self.logger.debug("Initialized capacity:\n %s", yaml.dump(self.capacity, default_flow_style=False))
        return True

    def get_matching_resources(self, requirement_SAT: str):
        matching_resources = []
        app_req = AppReq()
        self.logger.debug("Evaluating requirement expressions against cloud flavors:")
        for flavor_name, flavor_data in self.capacity["cloud"]["flavours"].items():
            try:
                result = app_req.eval_app_req_with_vars(requirement_SAT, [flavor_data])
                self.logger.debug(f"  {flavor_name} : {result[0]}")
                if result[0] == True:
                    matching_resources.append(flavor_name)
            except Exception as e:
                self.logger.debug(f"Error evaluating requirement expression for flavor '{flavor_name}': {e}")
        return matching_resources
    
    def get_available_instances_for_a_flavour(self, flavor_name: str, required_instance: int = 1):
        if "cloud" not in self.capacity or "flavours" not in self.capacity["cloud"]:
            return 0
        if flavor_name not in self.capacity["cloud"]["flavours"]:
            return 0
        if self.capacity["cloud"]["type"] == "flavour":
            available_amount = self.capacity["cloud"]["flavour"]["init"].get(flavor_name, 0)
            available_instances = min(required_instance, available_amount)
            self.logger.debug(f"Available amount of flavor '{flavor_name}': {available_amount}")
            self.logger.debug(f"Required instances of flavor '{flavor_name}': {required_instance}")
            self.logger.debug(f"Available instances of flavor '{flavor_name}': {available_instances}")
            return available_instances
        if self.capacity["cloud"]["type"] == "raw":
            available_props = dict((prop, value) for prop, value in self.capacity["cloud"]["raw"]["init"].items() if prop in self.calc_res_props)
            self.logger.debug(f"Available raw resources for flavor: {flavor_name}")
            self.logger.debug(f"\t\t{available_props}")
            required_props_per_flavor = dict((prop, value) for prop, value in self.capacity["cloud"]["flavours"][flavor_name].items() if prop in self.calc_res_props)
            self.logger.debug(f"Required raw resources per unit of flavor: {flavor_name}")
            self.logger.debug(f"\t\t{required_props_per_flavor}")
            self.logger.debug("Required instances of flavor: %d", required_instance)
            counter, found = required_instance, False
            while counter > 0 and not found:
                found = True
                for prop in self.calc_res_props:
                    if available_props.get(prop, 0) < (required_props_per_flavor.get(prop, 0) * counter):
                        counter -= 1
                        found = False
                        break
            self.logger.debug(f"Available amount for flavor '{flavor_name}': {counter}")
            return counter
        
    def generate_offer_for_requirements(self, swarmid: str, requirement_SAT: str):
        matching_resources = self.get_matching_resources(requirement_SAT)
        offer = {
            "matching_flavors": matching_resources
        }
        return offer
    
    def change_resource_state(self, swarmid: str, flavor_name: str, num_instances: int, from_state: str, to_state: str):
        self.logger.debug(f"Changing state: '{swarmid}', '{flavor_name}', {num_instances}, '{from_state}', '{to_state}'")  
        type = self.capacity["cloud"]["type"]
        if type == "flavour":
            self.capacity["cloud"][type][from_state][flavor_name] -= num_instances
            self.capacity["cloud"][type][to_state][flavor_name] += num_instances
        if type == "raw":
            for prop in self.calc_res_props:
                self.capacity["cloud"]["raw"][from_state][prop] -= (self.capacity["cloud"]["flavours"][flavor_name][prop] * num_instances)
                self.capacity["cloud"]["raw"][to_state][prop] += (self.capacity["cloud"]["flavours"][flavor_name][prop] * num_instances)
        return
    
    def dump_capacity_registry_info(self):
        #Dumping capacity registry information in a human-readable format
        self.logger.info('Dumping capacity registry information:')
        self.logger.info('Cloud:')
        #Dumping flavor definitions
        column_format = "\t{:25.25s}" + ("{:>10s}" * len(self.calc_res_props))
        self.logger.info(column_format.format("Flavours", *[prop.upper() for prop in self.calc_res_props]))
        for act_flavor_type, act_flavor_data in self.capacity["cloud"]["flavours"].items():
            self.logger.info(column_format.format(
                act_flavor_type.upper(),
                *[str(act_flavor_data.get(prop, 0)) for prop in self.calc_res_props]))
        #Dumping initial capacity by flavour        
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
        #Dumping initial capacity by raw
        if self.capacity["cloud"]["type"] == "raw":
            self.logger.info('')
            columns = min(len(self.calc_res_props), len(self.calc_res_props_labels))
            column_format = "\t{:25.25s}" + ("{:>10s}" * columns)
            self.logger.info(column_format.format("Capacity", *[label for label in self.calc_res_props_labels[:columns]]))
            for status in ["free", "reserved", "assigned", "allocated", "init"]:
                self.logger.info(column_format.format(
                    status.capitalize(),
                    *[str(self.capacity["cloud"]["raw"][status].get(prop, 0)) for prop in self.calc_res_props][:columns]))
        """
        print(f"\r\n\tReservations:\t{no_of_reservations}")
        for id, value in capacity["reservations"].items():
            print(f'\t{id.upper()}')
            print(f'\t\t{value["status"]}')
            print(f'\t\t', end='')
            for key, value2 in value["flavor"].items():
                print(f'{key.upper()}: {value2}', end=' ')
            print()
        if (capacity["initial"]["raw"] is not None):
            print("\r\n\tCapacity by raw:")
            print("\tType\t\tAll\tReserv.\tFree\t(% free)")
            for act_resource_type, act_resource_amount in capacity["initial"]["raw"].items():
                try:
                    percentage = '{:.1%}'.format(1 - (total_reserved["raw"][act_resource_type] / act_resource_amount))
                    free = act_resource_amount - total_reserved["raw"][act_resource_type]
                    print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t{total_reserved["raw"][act_resource_type]}\t{free}\t{percentage}')
                except KeyError:
                    print(f'\t{act_resource_type.upper()}\t\t{act_resource_amount}\t0\t0')
        else:
            print("\r\n\tCapacity by flavors:")
            print("\tFlavor\t\tAll\tReserv.\tFree\t(% free)")
            for act_flavor_type, act_flavor_data in capacity["initial"]["flavor"].items():
                percentage = 0
                free = 0
                cap_amount = capacity['initial'].get('flavor_amounts', {}).get(act_flavor_type, None)
                try:
                    percentage = '{:.1%}'.format(1 - (total_reserved["flavor"][act_flavor_type] / cap_amount))
                    free = cap_amount - total_reserved["flavor"][act_flavor_type]
                    print(f'\t{act_flavor_type.upper()}\t{cap_amount}\t{total_reserved["flavor"][act_flavor_type]}\t{free}\t{percentage}')
                except KeyError:
                    percentage = "n/a"
                    free = "n/a"
                    print(f'\t{act_flavor_type.upper()}\tn/a\t{total_reserved["flavor"][act_flavor_type]}\t{free}\t{percentage}')
        print()
        """
        #print("Capacity registry information: \n", yaml.dump(self.capacity, default_flow_style=False))


    def validate_flavor_definition(self, flavor_definition: dict):
        for a_flavor in flavor_definition.keys():
            if not isinstance(a_flavor, str):
                self.logger.error(f'Flavor "{a_flavor}" is not a string.')
                return False
            if not isinstance(flavor_definition[a_flavor], dict):
                self.logger.error(f'Flavor definition for "{a_flavor}" is not a dict.')
                return False
            if flavor_definition[a_flavor] == {}:
                self.logger.error(f'Flavor definition for "{a_flavor}" is empty.')
                return False
            for resource_key in self.RESOURCE_TYPES_FLAVOR:
                if resource_key not in flavor_definition[a_flavor].keys():
                    self.logger.error(f'No resource "{resource_key}" defined for flavor "{a_flavor}".')
                    return False
            for resource_key in flavor_definition[a_flavor].keys():
                if resource_key not in self.RESOURCE_TYPES_RAW:
                    self.logger.error(f'Unknown resource "{resource_key}" defined for flavor "{a_flavor}".')
                    return False
                else:
                    if not isinstance(flavor_definition[a_flavor][resource_key], int):
                        self.logger.error(f'Resource "{resource_key}" defined for flavor "{a_flavor}" is not an integer.')
                        return False
                    if isinstance(flavor_definition[a_flavor][resource_key], bool):
                        self.logger.error(f'Resource "{resource_key}" defined for flavor "{a_flavor}" is not an integer.')
                        return False
                    if flavor_definition[a_flavor][resource_key] < 1:
                        self.logger.error(f'Resource "{resource_key}" must be 1 or higher for flavor "{a_flavor}".')
                        return False
        return True

    def validate_capacity(self, capacity: dict, flavor_definition: dict, raw: bool):
        if capacity == {}:
            self.logger.error("Input capacity is empty.")
            return False
        resource_keys = set(self.RESOURCE_TYPES_RAW) if raw else set(flavor_definition.keys())
        for resource in resource_keys:
            if not isinstance(resource, str):
                self.logger.error(f'Resource "{resource}" is not a string.')
                return False
            if raw and resource not in self.RESOURCE_TYPES_RAW:
                self.logger.error(f'Unknown raw resource type "{resource}".')
                return False
            else:
                if not isinstance(capacity[resource], int):
                    self.logger.error(f'Resource "{resource}" is not an integer.')
                    return False
                elif isinstance(capacity[resource], bool):
                    self.logger.error(f'Resource "{resource}" is not an integer.')
                    return False
                if capacity[resource] < 1:
                    self.logger.error(f'Amount resource "{resource}" must be 1 or higher.')
                    return False
        return True

    # ...existing code...


    def summarize_all_reservations(self, capacity: dict):
        """Summarizes all reserved resources."""
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

    def remaining_capacity(self, capacity: dict):
        total_reservations = self.summarize_all_reservations(capacity)
        remaining_capacity = {
            "flavor": {},
            "raw" : {}
        }
        capacity_type_raw = False if capacity["initial"]["raw"] == None else True
        if capacity_type_raw:
            for raw_res_type in capacity["initial"]["raw"].keys():
                remaining_capacity["raw"][raw_res_type] = capacity["initial"]["raw"][raw_res_type]
            for flavor_type in capacity["initial"]["flavor"].keys():
                remaining_capacity["flavor"][flavor_type] = -1
            for raw_res_type in total_reservations["raw"].keys():
                remaining_capacity["raw"][raw_res_type] -= total_reservations["raw"][raw_res_type]
        else:
            flavor_amounts = capacity["initial"].get("flavor_amounts")
            for flavor_type in capacity["initial"]["flavor"].keys():
                for raw_res_type in capacity["initial"]["flavor"][flavor_type].keys():
                    remaining_capacity["raw"][raw_res_type] = -1
                if flavor_amounts is not None:
                    remaining_capacity["flavor"][flavor_type] = flavor_amounts.get(flavor_type, 0)
                else:
                    remaining_capacity["flavor"][flavor_type] = capacity["initial"]["flavor"][flavor_type].get("amount", 0)
            for flavor_type in total_reservations["flavor"].keys():
                remaining_capacity["flavor"][flavor_type] -= total_reservations["flavor"][flavor_type]
        return remaining_capacity

    def get_reservation_offer(self, res: dict):
        reservation = copy.deepcopy(res)
        # Basic validation of input
        if not isinstance(reservation, dict):
            self.logger.error('Reservation must be a dict.')
            return {}
        if 'flavor' not in reservation or not isinstance(reservation['flavor'], dict) or reservation['flavor'] == {}:
            self.logger.error('Reservation must contain a non-empty "flavor" dictionary.')
            return {}

        # Ensure capacity is initialized
        if not isinstance(self.capacity, dict) or 'cloud' not in self.capacity:
            self.logger.error('No in-memory capacity available for matchmaking.')
            return {}

        cloud = self.capacity.get('cloud', {})
        flavours_def = cloud.get('flavours')
        if flavours_def is None:
            self.logger.error('No flavor definitions available in capacity.')
            return {}

        cap_type = cloud.get('type')

        # Compute available counts per flavor depending on capacity type
        available_by_flavor = {}
        if cap_type == 'init_flavour':
            init_flavour = cloud.get('init_flavour', {}) or {}
            for f, amt in init_flavour.items():
                available_by_flavor[f] = int(amt)
        elif cap_type == 'init_raw':
            # determine how many of each flavor can be satisfied from raw totals
            init_raw = cloud.get('init_raw', {}) or {}
            for f, spec in flavours_def.items():
                # spec maps raw resource -> units per flavor
                max_per_resource = []
                for raw_res, per_unit in spec.items():
                    if per_unit <= 0:
                        max_per_resource.append(0)
                        continue
                    available_amount = init_raw.get(raw_res, 0)
                    max_per_resource.append(available_amount // per_unit)
                available_by_flavor[f] = min(max_per_resource) if max_per_resource else 0
        else:
            self.logger.error('Unknown capacity type for matchmaking.')
            return {}

        # Validate requested flavors against definitions and availability
        requested = reservation['flavor']
        for f, req_amt in requested.items():
            if f not in flavours_def:
                self.logger.error(f'Requested flavor "{f}" is not defined in cloud flavors.')
                return {}
            if not isinstance(req_amt, int) or isinstance(req_amt, bool) or req_amt <= 0:
                self.logger.error(f'Requested amount for flavor "{f}" must be a positive integer.')
                return {}
            avail = available_by_flavor.get(f, 0)
            if req_amt > avail:
                self.logger.info(f'Insufficient capacity for flavor "{f}": requested {req_amt}, available {avail}.')
                return {}

        # Compute raw requirements for the offered reservation
        raw_requirements = {}
        for f, req_amt in requested.items():
            spec = flavours_def[f]
            for raw_res, per_unit in spec.items():
                raw_requirements[raw_res] = raw_requirements.get(raw_res, 0) + (per_unit * req_amt)

        # Create reservation entry (in-memory) and return offer
        if 'reservations' not in self.capacity:
            self.capacity['reservations'] = {}
        reservation_id = str(uuid.uuid4())
        self.capacity['reservations'][reservation_id] = {
            'status': 'reserved',
            'flavor': requested,
            'raw': raw_requirements
        }

        offer = {
            'id': reservation_id,
            'status': 'reserved',
            'flavor': requested,
            'raw': raw_requirements
        }
        self.logger.info(f'Reservation offer created with id {reservation_id}.')
        return offer
        
    def _validate_reservation(self, reservation: dict, capacity: dict):
        if not isinstance(reservation, dict):
            self.logger.error('Reservation is not in a dictionary format.')
            return False
        if reservation == {}:
            self.logger.error('Empty reservation dictionary.')
            return False
        if "flavor" not in reservation.keys():
            self.logger.error('No "flavor" key defined in the reservation.')
            return False
        else:
            if len(reservation.keys()) > 1:
                self.logger.error('Too many keys defined in the reservation.')
                return False
            if not isinstance(reservation["flavor"], dict):
                self.logger.error('Flavor reservation is not in a dictionary format.')
                return False
            if reservation["flavor"] == {}:
                self.logger.error('Empty flavor reservation dictionary.')
                return False
            flavor_types = capacity["initial"]["flavor"].keys()
            for req_flavor in reservation["flavor"].keys():
                if not isinstance(req_flavor, str):
                    self.logger.error(f'Flavor type "{req_flavor}" is not a string.')
                    return False
                if req_flavor not in flavor_types:
                    self.logger.error(f'Unrecognized flavor type "{req_flavor}" requested.')
                    return False
                if not isinstance(reservation["flavor"][req_flavor], int):
                    self.logger.error(f'The requested amount of flavor "{req_flavor}" is not an integer.')
                    return False
                elif isinstance(reservation["flavor"][req_flavor], bool):
                    self.logger.error(f'The requested amount of flavor "{req_flavor}" is not an integer.')
                    return False
                else:
                    if reservation["flavor"][req_flavor] <= 0:
                        self.logger.error(f'The requested amount of flavor "{req_flavor}" is less than 1.')
                        return False
        return True
      
    def does_reservation_exist(self, reservation_id: str, capacity: dict = None):
        if capacity is None:
            capacity = self.read_capacity_registry()
        if not isinstance(reservation_id, str):
            self.logger.error(f'Given reservation ID is not a string.')
            return False
        if reservation_id == "":
            self.logger.warning(f'Given reservation ID is empty.')
            return False
        if reservation_id in capacity["reservations"].keys():
            self.logger.info(f'Reservation with ID "{reservation_id}" exists.')
            return True
        else:
            self.logger.info(f'Reservation with ID "{reservation_id}" not found.')
            return False

    def accept_offered_reservation(self, reservation_id: str):
        capacity = self.read_capacity_registry()
        reservation_exists = self.does_reservation_exist(reservation_id, capacity)
        if reservation_exists != True:
            return False
        else:
            if capacity["reservations"][reservation_id]["status"] != "reserved":
                self.logger.warning(f'Reservation with ID "{reservation_id}" is not in "reserved" status.')
                return False
            capacity["reservations"][reservation_id]["status"] = "assigned"
            self.logger.info(f'Reservation "{reservation_id}" found. Reservation accepted. Reservation status updated to "assigned".')
            self.save_capacity_registry(capacity)
            return True
    
    def reject_offered_reservation(self, reservation_id: str):
        capacity = self.read_capacity_registry()
        reservation_exists = self.does_reservation_exist(reservation_id, capacity)
        if reservation_exists != True:
            return False
        else:
            if capacity["reservations"][reservation_id]["status"] != "reserved":
                self.logger.warning(f'Reservation with ID "{reservation_id}" is not in "reserved" status.')
                return False
            del capacity["reservations"][reservation_id]
            self.logger.info(f'Reservation "{reservation_id}" found. Reservation rejected, reserved resources are freed.')
            self.save_capacity_registry(capacity)
            return True

    def app_has_been_destroyed(self, reservation_id: str):
        capacity = self.read_capacity_registry()
        reservation_exists = self.does_reservation_exist(reservation_id, capacity)
        if reservation_exists != True:
            return False
        else:
            if capacity["reservations"][reservation_id]["status"] not in ["assigned", "reserved"]:
                self.logger.warning(f'Reservation with ID "{reservation_id}" is not in "assigned" or "reserved" status.')
                return False
            del capacity["reservations"][reservation_id]
            self.logger.info(f'Reservation "{reservation_id}" found. Reservation destroyed, reserved resources are freed.')
            self.save_capacity_registry(capacity)
            return True

    def allocate_reservation(self, reservation_id: str):
        capacity = self.read_capacity_registry()
        reservation_exists = self.does_reservation_exist(reservation_id, capacity)
        if reservation_exists != True:
            return False
        else:
            if capacity["reservations"][reservation_id]["status"] != "assigned":
                self.logger.warning(f'Reservation with ID "{reservation_id}" is not in "assigned" status.')
                return False
            capacity["reservations"][reservation_id]["status"] = "allocated"
            self.logger.info(f'Reservation "{reservation_id}" found. Reservation status updated to "allocated".')
            self.save_capacity_registry(capacity)
            return True

    def deallocate_reservation(self, reservation_id: str):
        capacity = self.read_capacity_registry()
        reservation_exists = self.does_reservation_exist(reservation_id, capacity)
        if reservation_exists != True:
            return False
        else:
            if capacity["reservations"][reservation_id]["status"] != "allocated":
                self.logger.warning(f'Reservation with ID "{reservation_id}" is not in "allocated" status.')
                return False
            capacity["reservations"][reservation_id]["status"] = "assigned"
            self.logger.info(f'Reservation "{reservation_id}" found. Reservation status updated to "assigned".')
            self.save_capacity_registry(capacity)
            return True

    def read_capacity_registry(self):
        capacity = {}
        with open("capreg.yaml", "r") as file:
            try:
                capacity = yaml.safe_load(file)
            except yaml.YAMLError as exception:
                print(exception)
                self.logger.error("An error has occured!")
        self.logger.info('Loaded capacity registry.')
        return capacity

    def save_capacity_registry(self, capacity: dict):
        with open("capreg.yaml", "w") as file:
            try:
                file.write(yaml.dump(capacity))
                return True
            except yaml.YAMLError as exception:
                print(exception)
                self.logger.error("An error has occured!")
                return False

    def get_reservation_info(self, reservation_id: str):
        capacity = self.read_capacity_registry()
        reservation_exists = self.does_reservation_exist(reservation_id, capacity)
        if reservation_exists != True:
            return {}
        else:
            res_resources = self._sum_reservation_resources(reservation_id, capacity)
            reservation_info = {
                'id': reservation_id,
                'status': capacity["reservations"][reservation_id]['status'],
                'flavor': res_resources['flavor'],
                'raw': res_resources['raw']
            }
            self.logger.info('Listing reservation information.')
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

    def _sum_reservation_resources(self, reservation_id: str, capacity: dict):
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

