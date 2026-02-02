
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
    capreg.Initialize(flavor_definition=flavor_definition, capacity_by=capacity_by_raw)
    capreg.GetCapacityRegistryInfo()

    # Example reservation dictionary
    flavor_reservation = {
        "flavor": {
            "l1.large": 1,
            "m1.medium": 1
        }
    }

    # Making a reservation. Initial reservation status is 'reserved'
    reservation_id = capreg.GetReservationOffer(res=flavor_reservation)
    capreg.GetReservationInfo(reservation_id)
    capreg.GetCapacityRegistryInfo()

    # Rejecting a reservation
    capreg.RejectOfferedReservation(reservation_id)
    capreg.GetCapacityRegistryInfo()

    # Making a new reservation offer with the same requested flavours and amounts
    reservation_id = capreg.GetReservationOffer(res=flavor_reservation)
    capreg.GetCapacityRegistryInfo()

    # Accepting the offered reservation
    capreg.AcceptOfferedReservation(reservation_id)

    # Checking information about the reservation
    capreg.GetReservationInfo(reservation_id)

    # Checking information about the capacity registry
    capreg.GetCapacityRegistryInfo()

    # Trying to make another reservation
    flavor_reservation_2 = { "flavor": {
        "m1.medium": 2,
        "s1.small": 1
    } }
    reservation_id_2 = capreg.GetReservationOffer(res=flavor_reservation_2)

    # Checking information about the reservation
    capreg.GetReservationInfo(reservation_id_2)

    # Accepting the offered reservation
    capreg.AcceptOfferedReservation(reservation_id_2)

    # Checking information about the capacity registry
    capreg.GetCapacityRegistryInfo()

    # Free up resources after an app was destroyed
    capreg.AppHasBeenDestroyed(reservation_id)
    capreg.AppHasBeenDestroyed(reservation_id_2)

    # Checking information about the capacity registry
    capreg.GetCapacityRegistryInfo()

if __name__ == "__main__":
    # This example showcases when inputs are 
    # 1) flavor definition and 
    # 2) capacity by raw
    run_test()