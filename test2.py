# Importing the Capacity Registry module
import swch_capreg.capacity_registry as CapReg

def run_test():

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
    # IMPORTANT: all raw resource types must be present in the dictionary that may occur within a flavor's configuration.
    #            Minimum amount for a raw resource is the minimum amount that may occur within a flavor's configuration.
    capacity_by_raw = \
    {
        "cpu": 100,
        "ram": 100,
        "disk": 1000,
        "pub_ip": 5
    }

    # Initializing with a flavor and a raw resource dictionary
    # Keep in mind, that there were no 'amount' defined for the flavors
    CapReg.Initialize(flavor_definition=flavor_definition, capacity_by=capacity_by_raw)
    CapReg.GetCapacityRegistryInfo()

    # Example reservation dictionary
    flavor_reservation = \
        { 
            "flavor":
            {
            "l1.large": 1,
            "m1.medium": 1
            }
        }
    
    # Making a reservation. Initial reservation status is 'reserved'
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)
    CapReg.GetReservationInfo(reservation_id)
    CapReg.GetCapacityRegistryInfo()

    # Rejecting a reservation
    CapReg.RejectOfferedReservation(reservation_id)
    CapReg.GetCapacityRegistryInfo()

    # Making a new reservation offer with the same requested flavours and amounts
    reservation_id = CapReg.GetReservationOffer(res=flavor_reservation)
    CapReg.GetCapacityRegistryInfo()

    # Accepting the offered reservation
    CapReg.AcceptOfferedReservation(reservation_id)

    # Checking information about the reservation
    CapReg.GetReservationInfo(reservation_id)

    # Checking information about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Trying to make another reservation
    flavor_reservation_2 = { "flavor":
        {
            "m1.medium": 2,
            "s1.small": 1
        }
    }
    reservation_id_2 = CapReg.GetReservationOffer(res=flavor_reservation_2)

    # Checking information about the reservation
    CapReg.GetReservationInfo(reservation_id_2)

    # Accepting the offered reservation
    CapReg.AcceptOfferedReservation(reservation_id_2)

    # Checking information about the capacity registry
    CapReg.GetCapacityRegistryInfo()

    # Free up resources after an app was destroyed
    CapReg.AppHasBeenDestroyed(reservation_id)
    CapReg.AppHasBeenDestroyed(reservation_id_2)

    # Checking information about the capacity registry
    CapReg.GetCapacityRegistryInfo()

if __name__ == "__main__":
    # This example showcases when inputs are 
    # 1) flavor definition and 
    # 2) capacity by raw
    run_test()