
from swch_capreg.capacity_registry import SwChCapacityRegistry


def run_test():
    capreg = SwChCapacityRegistry()
    result = capreg.extract_application_requirements_from_tosca("stressng_and_resource.yaml")
    print("extract_application_requirements_from_tosca returned:", result)

if __name__ == "__main__":
    run_test()

