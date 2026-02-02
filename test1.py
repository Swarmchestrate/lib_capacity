
from swch_capreg.capacity_registry import SwChCapacityRegistry

def run_test():

    # Create an instance of the SwChCapacityRegistry class
    capreg = SwChCapacityRegistry()

    # Example flavor dictionary for initialization
    flavor_definition = {
        "m1.medium": {
            "cpu": 4,
            "ram": 8,
            "disk": 100
        },
        "l1.large": {
            "cpu": 8,
            "ram": 32,
            "disk": 200,
            "pub_ip": 1
        },
        "s1.small": {
            "cpu": 2,
            "ram": 4,
            "disk": 50
        }
    }

    capacity_by_flavor = {
        "m1.medium": 5,
        "l1.large": 2,
        "s1.small": 10
    }

    # Initializing the capacity registry with given initial flavors

    capreg.initialize(flavor_definition=flavor_definition, capacity_by=capacity_by_flavor)
    capreg.get_capacity_registry_info()
    flavor_reservation = {
        "flavor": {
            "l1.large": 2,
            "m1.medium": 1
        }
    }
    reservation_id = capreg.get_reservation_offer(res=flavor_reservation)
    capreg.get_reservation_info(reservation_id)
    capreg.get_capacity_registry_info()
    capreg.reject_offered_reservation(reservation_id)

    # Getting info about the capacity registry
    capreg.get_capacity_registry_info()

    # Making another reservation and getting an offer
    reservation_id = capreg.get_reservation_offer(res=flavor_reservation)

    # Accepting a reservation offer. This moves the reservation from the 'reserved' status to 'assigned'
    capreg.accept_offered_reservation(reservation_id)
    capreg.get_reservation_info(reservation_id)

    # Getting info about the capacity registry
    capreg.get_capacity_registry_info()

    # Trying to make another reservation. Requesting more resources than available
    flavor_reservation_2 = {
        "flavor": {
            "m1.medium": 2,
            "s1.small": 11
        }
    }
    capreg.get_reservation_offer(res=flavor_reservation_2)

    # Checking if a given reservation with an ID exists
    capreg.does_reservation_exist(reservation_id)

    # Moving a reservation from the 'assigned' state into the 'allocated' state
    capreg.allocate_reservation(reservation_id)

    # Deallocating a reservation. This moves the reservation from the 'allocated' status to 'assigned'
    capreg.deallocate_reservation(reservation_id)

    # Free up resources after an app was destroyed. This only works if the reservation status is either 'reserved' or 'assigned'
    capreg.app_has_been_destroyed(reservation_id)

    # Getting information about the capacity registry
    capreg.get_capacity_registry_info()

if __name__ == "__main__":
    # This example showcases when inputs are 
    # 1) flavor definition and 
    # 2) capacity by flavor
    run_test()
