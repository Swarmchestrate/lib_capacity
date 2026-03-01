from capacity_registry import SwChCapacityRegistry
import yaml
import pprint

if __name__ == "__main__":
    capreg = SwChCapacityRegistry("ra-sztaki-cloud-hu")
    capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
    #capreg.initialize_capacity_from_file("sztaki-capacity-flavor.yaml")
    capreg.dump_capacity_registry_info()

    #sat_filename="BookInfo-simple.yaml"
    sat_filename="BookInfo.yaml"
    #Generating offers for 'swarm1' and rejecting all offers for demonstration purposes
    swarmid="swarm1"
    offers = capreg.resource_offer_generate(swarmid, sat_filename)
    print("Generated offers:")
    print(yaml.dump(offers))
    capreg.dump_capacity_registry_info()

    #Rejecting all offers for demonstration purposes
    for ms_id, ms_offer in offers.items():
        for offer_id, offer in ms_offer.items():
            if offer_id != "colocated":
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
    #Accepting one of the offers
    offerid = list(offers[list(offers.keys())[0]].keys())[0]
    capreg.resource_offer_accepted(offerid, 
                                   offers[list(offers.keys())[0]][offerid])
    capreg.dump_capacity_registry_info()
    #Rejecting another one of the offers
    offerid = list(offers[list(offers.keys())[1]].keys())[0]
    capreg.resource_offer_rejected(offerid, 
                                   offers[list(offers.keys())[1]][offerid])
    capreg.dump_capacity_registry_info()





