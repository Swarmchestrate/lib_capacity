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

    ######################################################
    # TEST1: generating offers and releasing them all
    ######################################################

    #Generating offers for 'swarm1' 
    swarmid="swarm1"
    generated_offers = capreg.resource_offer_generate_from_SAT_file(swarmid, sat_filename)
    print("Generated offers:")
    print(yaml.dump(generated_offers))
    capreg.dump_capacity_registry_info()

    #Destroying all resources and offers belonging to 'swarm1' for demonstration purposes
    swarmid="swarm1"
    capreg.resources_and_offers_destroy_all(swarmid)
    capreg.dump_capacity_registry_info()

    ######################################################
    # TEST2: partial acceptance and rejection of offers and 
    # marking resources of accepted offers as allocated
    ######################################################

    #Generating offers for 'swarm2'
    swarmid="swarm2"
    generated_offers = capreg.resource_offer_generate_from_SAT_file(swarmid, sat_filename)
    print("Generated offers:")
    pprint.pprint(generated_offers)
    capreg.dump_capacity_registry_info()
  
    #Querying offers for 'swarm2' and accepting one for each ms and rejecting others for demonstration purposes
    #NOTE: all rejected offers will be removed from the capacity registry, so only accepted offers will remain in the registry after this block
    swarmid="swarm2"
    offers = capreg.resource_offer_query_all(swarmid)
    for msid in offers.keys():
        #selecting the first offer for each ms for acceptance, and rejecting others
        winning_offerid = list(offers[msid].keys())[0]
        for offerid in offers[msid].keys():            
            offer = offers[msid][offerid]
            if offerid == winning_offerid:
                capreg.resource_offer_accept(offerid, offer)
            else:
                capreg.resource_offer_reject(offerid, offer)
    capreg.dump_capacity_registry_info()

    #Marking a set of resources as "allocated" for demonstration purposes
    #NOTE: offers_all will contain only accepted offers, so we select any of them
    swarmid="swarm2"
    msid="details_v1"
    offers_all = capreg.resource_offer_query_all(swarmid)
    #selecting the first offer for the ms for deployment, and marking resources as allocated
    offerid=list(offers_all[msid].keys())[0]
    res_set = capreg.resource_set_get_from_offer(offerid, offers_all[msid][offerid])
    if res_set is not None:
        capreg.resource_set_deployed(swarmid, msid, res_set["restype"], res_set["resid"], res_set["count"])
    capreg.dump_capacity_registry_info() 

    #Marking a set of resources as "allocated" for demonstration purposes
    #NOTE: offers_all will contain only accepted offers, so we iterate them to mark all resources as allocated
    swarmid="swarm2"
    offers_all = capreg.resource_offer_query_all(swarmid)
    #selecting the first offer for each ms for deployment, and marking resources as allocated
    #NOTE: offers_all will contain only one accepted offer per ms, so we select any of them for each ms for deployment, and marking resources as allocated
    for msid in offers_all.keys():
        offerid=list(offers_all[msid].keys())[0]
        res_set = capreg.resource_set_get_from_offer(offerid, offers_all[msid][offerid])
        if res_set is not None:
            capreg.resource_set_deployed(swarmid, msid, res_set["restype"], res_set["resid"], res_set["count"])
    capreg.dump_capacity_registry_info()

    #Querying all resource sets for 'swarm2'
    swarmid="swarm2"
    resource_sets = capreg.resource_set_query_all(swarmid)
    print("Resource sets for swarm2:")
    print(yaml.dump(resource_sets))

    #Marking all resources as undeployed i.e. back to "assigned" for demonstration purposes
    #NOTE: offers_all will contain only allocated offers, so we iterate them to mark all resources as undeployed
    swarmid="swarm2"
    offers_all = capreg.resource_offer_query_all(swarmid)
    #selecting the first offer for each ms for undeployment, and marking resources as undeployed
    for msid in offers_all.keys():
        offerid=list(offers_all[msid].keys())[0]
        res_set = capreg.resource_set_get_from_offer(offerid, offers_all[msid][offerid])
        if res_set is not None:
            capreg.resource_set_undeployed(swarmid, msid, res_set["restype"], res_set["resid"], res_set["count"])
    capreg.dump_capacity_registry_info()

    #Releasing all assigned resources for demonstration purposes, should succeed
    swarmid="swarm2"
    capreg.resources_and_offers_destroy_all(swarmid)
    capreg.dump_capacity_registry_info()
