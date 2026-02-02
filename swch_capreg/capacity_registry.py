
import copy
import logging
import uuid
import yaml
from sardou import Sardou



class SwChCapacityRegistry:

    # Logger configuration
    logger = logging.getLogger()
    logging.basicConfig(
        level=logging.INFO, 
        format='(%(asctime)s) %(levelname)s:\t%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # May expand in the future
    RESOURCE_TYPES_RAW    = ["cpu", "ram", "disk", "pub_ip"]
    RESOURCE_TYPES_FLAVOR = ["cpu", "ram", "disk"] 

    def __init__(self):
        pass

    def extract_capacity_definitions_from_tosca(self, capacity_description_filename: str):
        tosca = Sardou(capacity_description_filename)

        return True

    def extract_application_requirements_from_SAT(self, application_description_filename: str):
        tosca = Sardou(application_description_filename)
        nodes = tosca.raw._to_dict().get('service_template', {}).get('node_templates', {})
        requirements = dict()
        for node_name, node in nodes.items():
            if 'requirements' in node:
                requirements[node_name] = node['requirements']
        return requirements

    def initialize(self, flavor_definition: dict, capacity_by: dict = None):
        """Initializes a capacity registry file with the given flavor definitions and
        either per-flavor amounts or raw totals.
        """
        if self.validate_flavor_definition(flavor_definition) == False:
            self.logger.info('Invalid input flavor definition. Initialization was unsuccessful.')
            return False
        if (flavor_definition is None):
            self.logger.error("No flavor types are defined. Please define the initial flavors!")
            return False
        if (capacity_by is None):
            self.logger.error("No capacity is defined. Please define the initial capacities!")
            return False
        capacity_type_raw = False
        if not isinstance(flavor_definition, dict):
            self.logger.error('Parameter flavor_definition is not a dict.')
            return False
        if not isinstance(capacity_by, dict):
            self.logger.error('Parameter capacity_by is not a dict.')
            return False
        if not capacity_by:
            self.logger.error("No capacity is defined. Please define the initial capacities!")
            return False
        keys = set(capacity_by.keys())
        if keys and all(k in self.RESOURCE_TYPES_RAW for k in keys):
            capacity_type_raw = True
        elif keys and all(k in flavor_definition.keys() for k in keys):
            capacity_type_raw = False
        else:
            self.logger.error('Second parameter must be either a raw resource totals dict or a per-flavor amounts dict.')
            return False
        if self.validate_capacity(capacity_by, flavor_definition, capacity_type_raw) == False:
            self.logger.info('Invalid capacity definition. Initialization was unsuccessful.')
            return False
        self.logger.info('Initializing capacity registry...')
        capacity = {
            "initial": {},
            "reservations": {}
        }
        capacity["initial"]["raw"] = capacity_by if capacity_type_raw else None
        capacity["initial"]["flavor"] = flavor_definition
        capacity["initial"]["flavor_amounts"] = capacity_by if not capacity_type_raw else None
        self.logger.info("Saving capacity into file...")
        self.logger.info(f'Capacity info:\n"{capacity}"\n')
        with open("capreg.yaml", "w") as file:
            try:
                file.write(yaml.dump(capacity))
            except yaml.YAMLError as exception:
                print(exception)
                self.logger.error("An error has occured!")
                return False
        self.logger.info('Successfully initialized capacity registry!')
        return True

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
        capacity = self.read_capacity_registry()
        if not self._validate_reservation(reservation, capacity):
            self.logger.info("Reservation cannot be made.")
            return ""
        remaining_capacity = self.remaining_capacity(capacity)
        can_be_reserved = True
        for req_res_type in reservation.keys():
            if req_res_type == "flavor":
                capacity_type_raw = False if capacity["initial"]["raw"] == None else True
                if capacity_type_raw:
                    for req_flavor in reservation["flavor"].keys():
                        flavor_config = copy.deepcopy(capacity["initial"]["flavor"][req_flavor])
                        for res_type, res_amount in flavor_config.items():
                            req_res_amount = res_amount * reservation["flavor"][req_flavor]
                            if req_res_amount > remaining_capacity["raw"][res_type]:
                                self.logger.warning(f'Not enough remaining "{res_type}" resources.')
                                can_be_reserved = False
                                break
                        if not can_be_reserved:
                            break
                else:
                    for req_flavor in reservation["flavor"].keys():
                        if reservation["flavor"][req_flavor] > remaining_capacity["flavor"][req_flavor]:
                            self.logger.warning(f'Not enough remaining "{req_flavor}" flavor.')
                            can_be_reserved = False
                            break
        if not can_be_reserved:
            self.logger.info("Reservation cannot be made.")
            return ""
        else:
            self.logger.info('Enough remaining resources. Registering reservation.')
            reservation_uuid = str(uuid.uuid4())
            self.logger.info(f'Reservation ID generated: {reservation_uuid}')
            reservation['status'] = 'reserved'
            capacity["reservations"][reservation_uuid] = reservation
            self.save_capacity_registry(capacity)
            return reservation_uuid

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

    def get_capacity_registry_info(self):
        capacity = self.read_capacity_registry()
        total_reserved = self.summarize_all_reservations(capacity)
        no_of_reservations = len(capacity["reservations"].keys())
        self.logger.info('Listing capacity registry information.')
        print(f"\r\n\tFlavor definitions:")
        print("\tFlavor\t\tCPU\tDISK\tRAM\tPUB_IP")
        for act_flavor_type, act_flavor_data in capacity["initial"]["flavor"].items():
            print(f'\t{act_flavor_type.upper()}', end='')
            print(f'\t{act_flavor_data["cpu"]}', end='')
            print(f'\t{act_flavor_data["disk"]}', end='')
            print(f'\t{act_flavor_data["ram"]}', end='')
            print(f'\t{act_flavor_data["pub_ip"] if "pub_ip" in act_flavor_data else ""}')
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