from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-sztaki-cloud-hu")
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.dump_capacity_registry_info()

    sat_filename="BookInfo-simple.yaml"
    #Generating offers for swarm 'swarm1' based on the requirements in 'BookInfo-simple.yaml'
    swarmid="swarm1"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(offers)
    capreg.dump_capacity_registry_info()
    #Rejecting all offers for demonstration purposes
    for offer_id, offer in offers.items():
        print(f"REJECTING OFFER:")
        pprint.pprint(offer)
        capreg.resource_offer_rejected(offer)
    capreg.dump_capacity_registry_info()

    #Generating offers for swarm 'swarm2' based on the requirements in 'BookInfo-simple.yaml'
    swarmid="swarm2"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(offers)
    capreg.dump_capacity_registry_info()
    #Accepting all offers for demonstration purposes
    for offer_id, offer in offers.items():
        print(f"ACCEPTING OFFER:")
        pprint.pprint(offer)
        capreg.resource_offer_accepted(offer)
    capreg.dump_capacity_registry_info()

    #Generating offers for swarm 'swarm3' based on the requirements in 'BookInfo-simple.yaml'
    swarmid="swarm3"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(offers)
    capreg.dump_capacity_registry_info()
    #Accepting one of three offers
    print(f"ACCEPTING OFFER:")
    offer = offers[list(offers.keys())[0]]
    pprint.pprint(offer)
    capreg.resource_offer_accepted(offer)
    capreg.dump_capacity_registry_info()
    #Rejecting one of three offers
    print(f"REJECTING OFFER:")
    offer = offers[list(offers.keys())[1]]
    pprint.pprint(offer)
    capreg.resource_offer_rejected(offer)
    capreg.dump_capacity_registry_info()



