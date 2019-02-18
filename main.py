import sys
from scrapers import scrape_all_sites
from writer import write_cats_to_file


def main():
    if len(sys.argv) == 1:
        print("Must include the desired zip code as a command line argument.\n"
              "Example: `python main.py 10023`")
        return

    zip_code = sys.argv[1]
    if len(zip_code) != 5:
        print("Invalid zip code. Must be of format #####.")
        return

    fname = "records.tsv"

    cats = scrape_all_sites(zip_code)
    write_cats_to_file(cats, fname)
    print("Finished writing {} cats to {}.".format(len(cats), fname))


if __name__ == "__main__":
    main()
