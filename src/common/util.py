class Util:
    @staticmethod
    def ambiguous_equals(s: str, comparison: str) -> bool:
        return s.lower().replace(" ", "") == comparison.lower().replace(" ", "")
