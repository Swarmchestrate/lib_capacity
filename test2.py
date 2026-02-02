
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

    # Example raw resource dictionary for initialization
    capacity_by_raw = {
        "cpu": 100,
        "ram": 100,
        "disk": 1000,
        "pub_ip": 5
    }

    # Initializing with a flavor and a raw resource dictionary

    capreg.initialize(flavor_definition=flavor_definition, capacity_by=capacity_by_raw)
    capreg.get_capacity_registry_info()
    flavor_reservation = {
        "flavor": {
            "l1.large": 1,
            "m1.medium": 1
        }
    }
    reservation_id = capreg.get_reservation_offer(res=flavor_reservation)
    capreg.get_reservation_info(reservation_id)
    capreg.get_capacity_registry_info()
    capreg.reject_offered_reservation(reservation_id)
    capreg.get_capacity_registry_info()
    reservation_id = capreg.get_reservation_offer(res=flavor_reservation)
    capreg.get_capacity_registry_info()

    # Accepting the offered reservation
    capreg.accept_offered_reservation(reservation_id)

    # Checking information about the reservation
    capreg.get_reservation_info(reservation_id)

    # Checking information about the capacity registry
    capreg.get_capacity_registry_info()

    # Trying to make another reservation
    flavor_reservation_2 = { "flavor": {
        "m1.medium": 2,
        "s1.small": 1
    } }
    reservation_id_2 = capreg.get_reservation_offer(res=flavor_reservation_2)

    # Checking information about the reservation
    capreg.get_reservation_info(reservation_id_2)

    # Accepting the offered reservation
    capreg.accept_offered_reservation(reservation_id_2)

    # Checking information about the capacity registry
    capreg.get_capacity_registry_info()

    # Free up resources after an app was destroyed
    capreg.app_has_been_destroyed(reservation_id)
    capreg.app_has_been_destroyed(reservation_id_2)
    # Checking information about the capacity registry
    capreg.get_capacity_registry_info()

if __name__ == "__main__":
    # This example showcases when inputs are 
    # 1) flavor definition and 
    # 2) capacity by raw
    run_test()