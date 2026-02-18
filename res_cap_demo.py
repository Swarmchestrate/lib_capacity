
from res_cap import ResCap
import yaml
import pprint

if __name__ == "__main__":
    
    res_cap_yaml = 'res_cap.yaml'
    with open(res_cap_yaml, 'r') as f:
        app_req_dict = yaml.safe_load(f) or {}

    rescap = ResCap()
    key, data = list(app_req_dict.items())[0]
    print(f"==>{key}:")
    variables = rescap.parse(data)
    pprint.pprint(variables)

