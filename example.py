# Importing the Capacity Registry module
import swch_capreg.capacity_registry as CapReg

# Example 1
def Example_1():

    # Example flavor dictionary for initialization
    flavor_init_dict = {
        "m1.medium": {          # Necessary key, must be string
            "config": {
                "cpu": 4,       # Necessary key, value must be integer
                "ram": 8,       # Necessary key, value must be integer (in GB)
                "disk": 100     # Necessary key, value must be integer (in GB)
                },
            "amount": 5         # Optional, value must be integer
            },

        "l1.large": {
            "config": {
                "cpu": 8,
                "ram": 32,
                "disk": 200,
                "pub_ip": 1     # Optional key, value must be integer
                },
            "amount": 2
            },
                
        "s1.small": {
            "config": {
                "cpu": 2,
                "ram": 4,
                "disk": 50
                },
            "amount": 10
            }
        }

    # Initializing the capacity registry with given initial flavors
    CapReg.Initialize(flavor_capacity=flavor_init_dict)

    # Getting info about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Example reservation dictionary
    flavor_reservation = { "flavor":
        {
            "l1.large": 2,
            "m1.medium": 1
            }
        }
    
    # Making a reservation. Initial reservation status is 'reserved'
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)

    # Getting info about a reservation offer
    CapReg.GetReservationInfo(reservation_id)

    # Rejecting a reservation offer.
    CapReg.RejectOfferedReservation(reservation_id)

    # Making another reservation and getting an offer
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)

    # Accepting a reservation offer. This moves the reservation from the 'reserved' status to 'assigned'
    CapReg.AcceptOfferedReservation(reservation_id)
    CapReg.GetReservationInfo(reservation_id)

    # Trying to make another reservation. Requesting more resources than available
    flavor_reservation_2 = { "flavor":
        {
            "m1.medium": 2,
            "s1.small": 11
        }
    }
    CapReg.GetReservationOffer(res=flavor_reservation_2)

    # Checking if a given reservation with an ID exists
    CapReg.DoesReservationExist(reservation_id)

    # Moving a reservation from the 'assigned' state into the 'allocated' state
    CapReg.AllocateReservation(reservation_id)

    # Deallocating a reservation. This moves the reservation from the 'allocated' status to 'assigned'
    CapReg.DeallocateReservation(reservation_id)

    # Free up resources after an app was destroyed. This only works if the reservation status is either 'reserved' or 'assigned'
    CapReg.AppHasBeenDestroyed(reservation_id)

    # Getting information about the capacity registry
    CapReg.GetCapacityRegistryInfo()

def Example_2():

    # Example flavor dictionary for initialization
    flavor_init_dict = {
        "m1.medium": {
            "config": {
                "cpu": 4,
                "ram": 8,
                "disk": 100
                }
            },

        "l1.large": {
            "config": {
                "cpu": 8,
                "ram": 32,
                "disk": 200,
                "pub_ip": 1
                }
            },
                
        "s1.small": {
            "config": {
                "cpu": 2,
                "ram": 4,
                "disk": 50
                }
            }
        }
    
    # Example raw resource dictionary for initialization
    # IMPORTANT: all raw resource types must be present in the dictionary that may occur within a flavor's configuration.
    #            Minimum amount for a raw resource is the minimum amount that may occur within a flavor's configuration.
    raw_init_dict = {
        "cpu": 100,
        "ram": 100,
        "disk": 1000,
        "pub_ip": 5
        }
    
    # Initializing with a flavor and a raw resource dictionary
    # Keep in mind, that there were no amount defined for the flavors
    CapReg.Initialize(flavor_capacity=flavor_init_dict, raw_capacity=raw_init_dict)

    # Example reservation dictionary
    flavor_reservation = { "flavor":
        {
            "l1.large": 2,
            "m1.medium": 1,
            "s1.small": 5
            }
        }
    
    # Making a reservation. Initial reservation status is 'reserved'
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)

    # Rejecting a reservation
    CapReg.RejectOfferedReservation(reservation_id)

    # Checking information about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Trying to make another reservation
    flavor_reservation_2 = { "flavor":
        {
            "m1.medium": 2,
            "s1.small": 11
        }
    }
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation_2)

    # Checking information about the reservation
    CapReg.GetReservationInfo(reservation_id)

    # Accepting the offered reservation
    CapReg.AcceptOfferedReservation(reservation_id)

    # Free up resources after an app was destroyed
    CapReg.AppHasBeenDestroyed(reservation_id)

    # Checking information about the capacity registry
    CapReg.GetCapacityRegistryInfo()

if __name__ == "__main__":
    # Example 1 - This example uses only a flavor dictionary for initialization.
    Example_1()

    # Example 2 - This example uses a flavor dictionary and a raw resources dictionary for initialization
    Example_2()