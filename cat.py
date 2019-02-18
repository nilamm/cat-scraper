class Cat:
    def __init__(self):
        # profile
        self.image = None
        self.pet_name = None
        self.description = None
        self.static_url = None

        # physical characteristics
        self.breed = None
        self.pet_size = None
        self.color = None
        self.age = None
        self.sex = None
        self.hair_length = None

        # adoption info
        self.adoption_status = None
        self.adoption_center = {
            'name': None,
            'address': None,
            'city': None,
            'state': None,
            'zip': None,
            'contact_info': None
        }

        # misc boolean qualities
        self.is_declawed = None
        self.is_good_with_birds = None
        self.is_good_with_cats = None
        self.is_good_with_dogs = None
        self.is_good_with_kids = None
        self.is_good_with_small_animals = None
        self.is_house_trained = None
        self.is_microchipped = None
        self.has_shots = None
        self.is_spayed_neutered = None

    def print(self):
        """
            Print method for debugging.
        """
        print("Cat: {}".format(self.pet_name))
        for k in self.__dict__.keys():
            if k == "pet_name":
                continue
            print("-- {}: {}".format(k, getattr(self, k)))
