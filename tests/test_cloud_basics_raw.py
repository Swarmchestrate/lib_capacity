from swch_capreg import SwChCapacityRegistry
import yaml
import pprint
from pathlib import Path

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-sztaki-cloud-hu")
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.dump_capacity_registry_info()

    requirements = capreg.extract_application_requirements_from_SAT_file("BookInfo-simple.yaml")
    matching_resources = capreg.calculate_matching_resources(requirements)

    swarmid="swarm123"
    for ms, matching_resources in matching_resources.items():
        for resource in matching_resources:
            res_type = list(resource.keys())[0]
            res_name = resource[res_type]
            print(f"                                Calculating available instances for MS '{ms}' with matching cloud flavor '{res_name}'")
            available_instances = capreg.calculate_available_instances_of_resources(res_type, res_name, 3)
            print(f"\tAvailable instances '{res_name}': {available_instances}")
            capreg.resource_state_init_amount(swarmid, ms, res_type, res_name, "free", available_instances)
            if available_instances > 2:
                capreg.resource_state_change(swarmid, ms, res_type, res_name, available_instances, "free", "reserved")
                capreg.dump_capacity_registry_info()
                capreg.resource_state_change(swarmid, ms, res_type, res_name, available_instances-1, "reserved", "assigned")
                capreg.dump_capacity_registry_info()
                capreg.resource_state_change(swarmid, ms, res_type, res_name, available_instances-2, "assigned", "allocated")
                capreg.dump_capacity_registry_info()




