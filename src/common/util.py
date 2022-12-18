class Util:
    @staticmethod
    def ambiguous_equals(s: str, comparison: str) -> bool:
        return s.lower().replace(" ", "") == comparison.lower().replace(" ", "")

    @staticmethod
    def convert_to_property(param_name: str) -> str:
        return param_name.lower().replace(" ", "_")
