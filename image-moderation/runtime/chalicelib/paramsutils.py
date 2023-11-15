import distutils

class Strings(object):
    @staticmethod
    def get_list_from_string(string_list, defualt_list=[]):
        if string_list is None or len(string_list) == 0:
            return defualt_list

        splits = string_list.split(sep=',', maxsplit=-1)

        results = []
        for token in splits:
            if token != '':
                results.append(token.strip())

        return results

    @staticmethod
    def get_int_from_string(string_value, default_value=0):
        if string_value is None or len(string_value) == 0:
            return default_value

        return int(string_value)

    @staticmethod
    def get_bool_from_string(string_value, default_value=False):
        if string_value is None or len(string_value) == 0:
            return default_value

        return distutils.util.strtobool(string_value)

    @staticmethod
    def get_float_from_string(string_value, default_value=0):
        if string_value is None or len(string_value) == 0:
            return default_value

        return float(string_value)
