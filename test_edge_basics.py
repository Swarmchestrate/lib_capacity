from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-fuelics-cloud-hu")
    capreg.initialize_capacity_from_file("edge-capacity.yaml")
    capreg.dump_capacity_registry_info()

    requirements = capreg.extract_application_requirements_from_SAT_file("BookInfo-edge.yaml")
    matching_resources = capreg.calculate_matching_resources(requirements)

    swarmid="swarm1"
    for ms, matching_resource in matching_resources.items():
        for resource in matching_resource:
            res_type = list(resource.keys())[0]
            res_name = resource[res_type]
            print(f"                                Calculating available instances for MS '{ms}' with matching resource '{res_name}' ('{res_type}')... ")
            available_instances = capreg.calculate_available_instances_of_resources(res_type, res_name, 1)
            print(f"\tAvailable instances of resource '{res_name}' ('{res_type}'): {available_instances}")
            capreg.resource_state_init_amount(swarmid, ms, res_type, res_name, "free", available_instances)
            capreg.resource_state_change(swarmid, ms, res_type, res_name, available_instances, "free", "reserved")
            capreg.dump_capacity_registry_info()
            capreg.resource_state_change(swarmid, ms, res_type, res_name, available_instances, "reserved", "assigned")
            capreg.dump_capacity_registry_info()
            capreg.resource_state_change(swarmid, ms, res_type, res_name, available_instances, "assigned", "allocated")
            capreg.dump_capacity_registry_info()




