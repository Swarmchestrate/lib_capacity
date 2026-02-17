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
                result[".".join(prefix)] = d

        extract_flat(data)
        return result
