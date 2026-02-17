import yaml

class ResCap:
    def __init__(self):
        pass

    def parse(self, data: dict) -> dict:
        """
        Reads the YAML file and returns a flat dict where each key is a dot-separated path to a leaf value.
        """
        result = {}

        def extract_flat(d, prefix=None):
            if prefix is None:
                prefix = []
            if isinstance(d, dict):
                for k, v in d.items():
                    extract_flat(v, prefix + [k])
            else:
                key = ".".join(prefix)
                #temporary workaround: convert integers to string
                if key.endswith('.mem-size') or key.endswith('.disk-size'):
                    value = int(d)
                else:
                    value = d.lower() if isinstance(d, str) else d
                result[key] = value

        extract_flat(data)
        return result
