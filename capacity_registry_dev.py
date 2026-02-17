from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry()
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    #capreg.dump_capacity_registry_info()
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    capreg.dump_capacity_registry_info()
    requirement_SAT = capreg.extract_application_requirements_from_SAT("stressng-and-resource.yaml")
    matching_resources = capreg.get_matching_resources(requirement_SAT)
    print("Matching resources:")
    pprint.pprint(matching_resources)



    #offer = capreg.get_reservation_offer(res=req_SAT)
    #print("Offer for the reservation request:\n", yaml.dump(offer, default_flow_style=False))
