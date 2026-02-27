from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-sztaki-cloud-hu")
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.dump_capacity_registry_info()

    sat_filename="BookInfo-simple.yaml"
    #Generating offers for 'swarm1' and rejecting all offers for demonstration purposes
    swarmid="swarm1"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(offers)
    capreg.dump_capacity_registry_info()
    #Rejecting all offers for demonstration purposes
    for ms_id, ms_offer in offers.items():
        for offer_id, offer in ms_offer.items():
            capreg.resource_offer_rejected(offer_id, offer)
    capreg.dump_capacity_registry_info()

    #Generating offers for 'swarm2' and accepting all offers for demonstration purposes
    swarmid="swarm2"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(offers)
    capreg.dump_capacity_registry_info()
    #Accepting all offers for demonstration purposes
    for ms_id, ms_offers in offers.items():
        for offer_id, offer in ms_offers.items():
            capreg.resource_offer_accepted(offer_id, offer)
    capreg.dump_capacity_registry_info()

    #Generating offers for 'swarm3' and partially accept and reject offers for demonstration purposes
    swarmid="swarm3"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(offers)
    capreg.dump_capacity_registry_info()
    #Accepting one of three offers
    offerid = list(offers["one"].keys())[0]
    capreg.resource_offer_accepted(offerid, 
                                   offers["one"][offerid])
    capreg.dump_capacity_registry_info()
    #Rejecting one of three offers
    offerid = list(offers["two"].keys())[0]
    capreg.resource_offer_rejected(offerid, 
                                   offers["two"][offerid])
    capreg.dump_capacity_registry_info()



