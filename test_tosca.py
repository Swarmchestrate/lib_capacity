
from swch_capreg.capacity_registry import SwChCapacityRegistry
import yaml

def run_test_SAT():
    capreg = SwChCapacityRegistry()
    result = capreg.extract_application_requirements_from_SAT("test_SAT.yaml")
    print("extract_application_requirements_from_SAT returned:", result)

def run_test_CDT():
    capreg = SwChCapacityRegistry()
    result = capreg.extract_capacity_definitions_from_CDT("sztaki-capacity-overall.yaml")
    print("extract_capacity_definitions_from_CDT returned:\n", 
        yaml.dump(result, default_flow_style=False))

if __name__ == "__main__":
    #run_test_SAT()
    run_test_CDT()

