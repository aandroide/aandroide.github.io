
class ThegrooveRegexes:

    def __init__(self, **kwargs):
        self.name = ""
        self.params = []

        self.__dict__.update(**kwargs)

    @staticmethod
    def convert_to_dict(obj):
        """
        A function takes in a custom object and returns a dictionary representation of the object.
        This dict representation includes meta data such as the object's module and class names.
        """

        #  Populate the dictionary with object meta data
        obj_dict = {
            "__class__": obj.__class__.__name__,
            "__module__": obj.__module__
        }

        #  Populate the dictionary with object properties
        obj_dict.update(obj.__dict__)

        return obj_dict

    @staticmethod
    def dict_to_obj(obj_dict):

        """
        Function that takes in a dict and returns a custom object associated with the dict.
        This function makes use of the "__module__" and "__class__" metadata in the dictionary
        to know which object type to create.
        """
        if "__class__" in obj_dict:
            # Pop ensures we remove metadata from the dict to leave only the instance arguments
            obj_dict.pop("__class__")

            # Get the module name from the dict and import it
            obj_dict.pop("__module__")

            # Use dictionary unpacking to initialize the object
            obj = ThegrooveRegexes(**obj_dict)
        else:
            obj = ThegrooveRegexes(**obj_dict)
        return obj
