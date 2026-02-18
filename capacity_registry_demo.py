from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry()
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    capreg.dump_capacity_registry_info()

    requirement_SAT = capreg.extract_application_requirements_from_SAT("stressng-and-resource.yaml")

    matching_resources = capreg.get_matching_resources(requirement_SAT)
 
    swarmid = "swarm1"
    for flavor_name in matching_resources:
        available_instances = capreg.get_available_instances_for_a_flavour(flavor_name,12)
        capreg.change_resource_state(swarmid, flavor_name, available_instances, "free", "reserved")
        capreg.dump_capacity_registry_info()
        capreg.change_resource_state(swarmid, flavor_name, available_instances-1, "reserved", "assigned")
        capreg.dump_capacity_registry_info()
        capreg.change_resource_state(swarmid, flavor_name, available_instances-2, "assigned", "allocated")
        capreg.dump_capacity_registry_info()




