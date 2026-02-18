from app_req import AppReq
import yaml


if __name__ == "__main__":
    yaml_path = "app_req.yaml"
    with open(yaml_path, 'r') as f:
        app_req_dict = yaml.safe_load(f) or {}

    app_req = AppReq()
    lambda_str = app_req.parse(app_req_dict)
    print("Lambda string:", lambda_str)
    var_names = app_req.extract_vars(lambda_str)
