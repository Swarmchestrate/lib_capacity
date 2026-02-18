from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry()
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.dump_capacity_registry_info()

    requirements = capreg.extract_application_requirements_from_SAT("BookInfo-simple.yaml")
    matching_resources = capreg.calculate_matching_resources(requirements)
 
    for node, matching_flavors in matching_resources.items():
        for flavor_name in matching_flavors:
            print(f"                                Calculating available instances for Node '{node}' with matching flavor '{flavor_name}'")
            available_instances = capreg.calculate_available_instances_for_a_flavour(flavor_name,3)
            if available_instances > 2:
                capreg.change_resource_state(node, flavor_name, available_instances, "free", "reserved")
                capreg.dump_capacity_registry_info()
                capreg.change_resource_state(node, flavor_name, available_instances-1, "reserved", "assigned")
                capreg.dump_capacity_registry_info()
                capreg.change_resource_state(node, flavor_name, available_instances-2, "assigned", "allocated")
                capreg.dump_capacity_registry_info()




