import csv


def write_cats_to_file(cats, fname):
    """
        Writes a list of Cat objects to a TSV file.
    """

    columns = [
        "image",
        "pet_name",
        "description",
        "static_url",
        "breed",
        "pet_size",
        "color",
        "age",
        "sex",
        "hair_length",
        "adoption_status",
        "adoption_center_name",
        "adoption_center_address",
        "adoption_center_city",
        "adoption_center_state",
        "adoption_center_zip",
        "adoption_center_contact_info",
        "is_declawed",
        "is_good_with_birds",
        "is_good_with_cats",
        "is_good_with_dogs",
        "is_good_with_kids",
        "is_good_with_small_animals",
        "is_house_trained",
        "is_microchipped",
        "has_shots",
        "is_spayed_neutered"
    ]

    with open(fname, 'w') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t', lineterminator='\n')
        writer.writerow(columns)
        for cat in cats:
            writer.writerow([cat.image, cat.pet_name, cat.description,
                             cat.static_url, cat.breed, cat.pet_size,
                             cat.color, cat.age, cat.sex, cat.hair_length,
                             cat.adoption_status, cat.adoption_center["name"],
                             cat.adoption_center["address"],
                             cat.adoption_center["city"],
                             cat.adoption_center["state"],
                             cat.adoption_center["zip"],
                             cat.adoption_center["contact_info"],
                             cat.is_declawed, cat.is_good_with_birds,
                             cat.is_good_with_cats, cat.is_good_with_dogs,
                             cat.is_good_with_kids,
                             cat.is_good_with_small_animals,
                             cat.is_house_trained, cat.is_microchipped,
                             cat.has_shots, cat.is_spayed_neutered])
