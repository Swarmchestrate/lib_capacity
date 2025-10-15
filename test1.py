# Importing the Capacity Registry module
import swch_capreg.capacity_registry as CapReg

def run_test():

    # Example flavor dictionary for initialization
    flavor_definition = {
        "m1.medium": {          # Necessary key, must be string
            "cpu": 4,       # Necessary key, value must be integer
            "ram": 8,       # Necessary key, value must be integer (in GB)
            "disk": 100     # Necessary key, value must be integer (in GB)
            },

        "l1.large": {
            "cpu": 8,
            "ram": 32,
            "disk": 200,
            "pub_ip": 1     # Optional key, value must be integer
            },
                
        "s1.small": {
            "cpu": 2,
            "ram": 4,
            "disk": 50
            }
        }

    capacity_by_flavor = \
    {
        "m1.medium": 5,
        "l1.large": 2,
        "s1.small": 10
    }

    # Initializing the capacity registry with given initial flavors
    CapReg.Initialize(flavor_definition=flavor_definition, capacity_by=capacity_by_flavor)

    # Getting info about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Example reservation dictionary
    flavor_reservation = \
        { 
            "flavor":
            {
                "l1.large": 2,
                "m1.medium": 1
            }
        }
    
    # Making a reservation. Initial reservation status is 'reserved'
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)

    # Getting info about a reservation offer
    CapReg.GetReservationInfo(reservation_id)

    # Getting info about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Rejecting a reservation offer.
    CapReg.RejectOfferedReservation(reservation_id)

    # Getting info about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Making another reservation and getting an offer
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)

    # Accepting a reservation offer. This moves the reservation from the 'reserved' status to 'assigned'
    CapReg.AcceptOfferedReservation(reservation_id)
    CapReg.GetReservationInfo(reservation_id)

    # Getting info about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Trying to make another reservation. Requesting more resources than available
    flavor_reservation_2 = \
        { 
            "flavor":
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

if __name__ == "__main__":
    # This example showcases when inputs are 
    # 1) flavor definition and 
    # 2) capacity by flavor
    run_test()
