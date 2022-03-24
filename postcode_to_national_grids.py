import pandas as pd  # type: ignore


def get_north_neighbour(northing: pd.Series) -> pd.Series:
    """Return British national grid's northing letter of the northern neighbour.
    British national grid references do not contain letter 'I', for more information,
    see: https://digimap.edina.ac.uk/help/our-maps-and-data/bng/

    Args:
        northing (pd.Series): Series of northing letters.

    Returns:
        pd.Series: Series of northern neighbour letters.
    """
    assert (northing.str.len() == 1).all(), "Northing must be a letter"
    # 5x5 grid, starting from A on the north west to Z on the south east
    # letters increase towards south
    return northing.str.upper().apply(
        lambda s: chr(ord(s) - 5) if s < "I" else chr(ord(s) - 1 - 5)
    )


def get_east_neighbour(easting: pd.Series) -> pd.Series:
    """Return British national grid's easting letter of the eastern neighbour.
    British national grid references do not contain letter 'I', for more information,
    see: https://digimap.edina.ac.uk/help/our-maps-and-data/bng/

    Args:
        easting (pd.Series): Series of easting letters.

    Returns:
        pd.Series: Series of northern neighbour letters.
    """
    # 5x5 grid, starting from A on the north west to Z on the south east
    # letters increase towards east
    assert (easting.str.len() == 1).all(), "Easting must be a letter"
    return easting.str.upper().apply(
        lambda s: chr(ord(s) + 1) if s < "I" else chr(ord(s) + 1 + 1)
    )


def get_2km_grids(grid_ref_1km: pd.Series) -> pd.Series:
    """Calculate 2km grid references from 1km grid references.
    *2km grid references are not standard and need to be calculated from 1km grid
    references. They are formed by merging 2 consecutive 1km grid references
    horizontally and vertically. Grids will follow the same naming convention with 1km
    grids but easting and northing numbers will always be odd number.

    Args:
        pc2ng (pd.DataFrame): Series of 1km grid references

    Returns:
        pd.DataFrame: Series of 2km grid references
    """
    # northings
    northing_letter = grid_ref_1km.str[0]
    northing = pd.to_numeric(grid_ref_1km.str[2:4])
    northing_offset = (northing + 1) % 2
    northing_2km = northing + northing_offset
    # find out if the 2km grid falls to the north of the current grid
    overflow_northing = northing_2km > 99
    # move the 2km grid to the north if it falls in to the north neighbour
    overflow_northing[overflow_northing] = 0
    northing_letter[overflow_northing] = northing_letter[overflow_northing].apply(
        get_north_neighbour
    )

    # eastings
    easting_letter = grid_ref_1km.str[1]
    easting = pd.to_numeric(grid_ref_1km.str[4:6])
    easting_offset = (easting + 1) % 2
    easting_2km = easting + easting_offset
    # find out if the 2km grid falls to the east of the current grid
    overflow_easting = easting_2km > 99
    # move the 2km grid to the east if it falls in to the east neighbour
    overflow_easting[overflow_easting] = 0
    easting_letter[overflow_easting] = easting_letter[overflow_easting].apply(
        get_east_neighbour
    )

    return pd.Series(
        northing_letter
        + easting_letter
        + northing_2km.astype(str).str.zfill(2)
        + easting_2km.astype(str).str.zfill(2),
        index=grid_ref_1km.index,
    )


def get_grid_references(
    postcode: pd.Series, pc2ng_path: str, with_2km_refs: bool = False
) -> pd.DataFrame:
    """Return all the British national grid references (1,2*,5,19,20,50,100km) and
    coordinates (lat,lon) for given postcodes.
    * 2km grid references are not standard and including them is optional, see
    `with_2km_refs`. 2km grid references need to be calculated from 1km grid
    references. They are formed by merging 2 consecutive 1km grid references
    horizontally and vertically. Grid references follow the same naming convention with
    1km grid references but eastings and northings will always be odd number.

    Args:
        postcode (pd.Series): Series of postcodes. Invalid postcodes will be eliminated
        and postcodes will be standardised.
        pc2ng_path (str): Path to the parquet file of British national grid references
        indexed by postcodes. This file is generated via
        `postcode_to_british_national_grid.ipynb` file from:
        https://github.com/Bubo-AI/spatial_utilities/

    Returns:
        pd.DataFrame: Dataframe of all grid references with the same index of given
        series for compatibility with original dataframe. You can concat the returned
        dataframe with the original dataframe.
    """
    # normalise postcodes on national grid file
    pc2ng = pd.read_parquet(pc2ng_path)
    pc2ng.index = (
        pc2ng.index.str.replace(r"\s+", "", regex=True).str.upper().str.strip()
    )

    if with_2km_refs:
        pc2ng["2km_grid"] = get_2km_grids(pc2ng["1km_grid"])
        # re-order columns to preserve larger to smaller grid references
        other_cols = [*filter(lambda x: "km_grid" not in x, pc2ng.columns)]
        # drop the km_grid text from column names, sort in reversed order as integer
        grid_cols = sorted(
            [*filter(lambda x: "km_grid" in x, pc2ng.columns)],
            reverse=True,
            key=lambda x: int(x.replace("km_grid", "")),
        )
        # reorder columns
        pc2ng = pc2ng[other_cols + grid_cols]

    # normalise postcodes on input
    postcode = postcode.str.replace(r"\s", "", regex=True).str.upper().str.strip()
    index = postcode.index
    return pd.merge(
        left=postcode,
        right=pc2ng,
        left_on=postcode.name,
        right_on="Postcode",
        how="left",
        validate="m:1",
    ).set_index(
        index
    )  # ensure index is preserved
