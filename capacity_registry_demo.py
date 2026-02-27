from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-sztaki-cloud-hu")
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.dump_capacity_registry_info()

    requirements = capreg.extract_application_requirements_from_SAT("BookInfo-simple.yaml")
    """
    {
        'one': "lambda vals: ((vals['host.num-cpus'] >= 1) and (vals['host.mem-size'] == 2) and (vals['locality.city'] == 'budapest'))",
        'two': "lambda vals: ((vals['host.num-cpus'] >= 2) and (vals['host.mem-size'] >= 4))"
    }
    """
    matching_cloud_flavors = capreg.calculate_matching_cloud_flavors(requirements)
    """
    {
        'one': ['m2-medium-sztaki'], 
        'two': ['m2-large-sztaki','m2-xlarge-sztaki']
    }
    """
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




