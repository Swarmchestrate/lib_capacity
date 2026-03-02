from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-fuelics-cloud-hu")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.initialize_capacity_from_file("edge-capacity.yaml")
    capreg.dump_capacity_registry_info()

    """
    requirements = capreg.extract_application_requirements_from_SAT("BookInfo-simple.yaml")
    matching_cloud_flavors = capreg.calculate_matching_cloud_flavors(requirements)
    swarmid="swarm123"
    for ms, matching_flavors in matching_cloud_flavors.items():
        for flavor_name in matching_flavors:
            print(f"                                Calculating available instances for MS '{ms}' with matching cloud flavor '{flavor_name}'")
            available_instances = capreg.calculate_available_instances_for_cloud_flavour(flavor_name,3)
            capreg.resource_state_init_amount(swarmid, ms, "cloud", flavor_name, "free", available_instances)
            if available_instances > 2:
                capreg.resource_state_change(swarmid, ms, "cloud", flavor_name, available_instances, "free", "reserved")
                capreg.dump_capacity_registry_info()
                capreg.resource_state_change(swarmid, ms, "cloud", flavor_name, available_instances-1, "reserved", "assigned")
                capreg.dump_capacity_registry_info()
                capreg.resource_state_change(swarmid, ms, "cloud", flavor_name, available_instances-2, "assigned", "allocated")
                capreg.dump_capacity_registry_info()
    """



