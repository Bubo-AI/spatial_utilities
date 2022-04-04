import pandas as pd  # type: ignore
import numpy as np
import numpy.typing as npt
from typing import Any, Dict, Tuple


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


# 500KM Grids: https://digimap.edina.ac.uk/help/assets/img/help/500kmsq.png
# 100KM Grids: https://digimap.edina.ac.uk/help/assets/img/help/100kmsq.png
# 10 / 5 / 1KM Grids: https://digimap.edina.ac.uk/help/assets/img/help/skexample.png
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


def get_grid_patterns() -> Dict[str, npt.NDArray[Any]]:
    """Return all the grid patterns for British national grid references.

    Returns:
        Dict[str, npt.NDArray[Any]]: Dict of grid patterns indexed by the following:
        grid-lettters: Letters used in the British National Grid
        letters: 5x5 letter matrix, i.e. 500KM grid matrix
        10: 10x10 matrix to divide 100KM grids into 10km grids
        quadrants: 4x4 matrix to divide 10KM grids into 5km grids
        5: 20x20 matrix to divide 100KM grids into 5km grids
    """
    grid_patterns = dict()  # type: Dict[str, npt.NDArray[Any]]

    grid_patterns["grid-letters"] = np.array(
        [
            *map(
                chr,
                (
                    list(range(ord("A"), ord("I")))
                    + list(range(ord("I") + 1, ord("Z") + 1))
                ),
            )
        ]
    )
    # letter grid pattern
    grid_patterns["letters"] = np.array(grid_patterns["grid-letters"]).reshape(5, 5)
    # repeating pattern for 10km grids
    grid_patterns["10"] = np.array(
        [(str(j) + str(i)) for i in range(9, -1, -1) for j in range(10)]
    ).reshape(10, 10)

    # divide 10km grids by 4 to get 5km grids
    grid_patterns["quadrants"] = np.array([["NW", "NE"], ["SW", "SE"]])

    # repeating pattern for 5km grids
    grid_patterns["5"] = (
        np.array(
            [
                str(ten_col) + quadrant_col
                for ten_row in grid_patterns["10"]
                for ten_col in ten_row
                for quadrant_row in grid_patterns["quadrants"]
                for quadrant_col in quadrant_row
            ],
        )
        .reshape(10, 10, 2, 2)
        .swapaxes(1, 2)
        .reshape(20, 20)
    )
    return grid_patterns


def get_grid_matrix() -> Dict[str, npt.NDArray[Any]]:
    """Return British National Grid Reference Matrixes.

    Returns:
        Dict[str, npt.NDArray[Any]]: Dictionary of grid matrices, indexed by 500, 100,
        5.
    """
    grid_matrix = dict()  # type: Dict[str, npt.NDArray[Any]]
    grid_patterns = get_grid_patterns()
    # 500km grids
    grid_matrix["500"] = grid_patterns["letters"]

    # 100km grids
    grid_matrix["100"] = (
        np.array(
            [
                g1 + g2
                for g1 in grid_patterns["grid-letters"]
                for g2 in grid_patterns["grid-letters"]
            ]
        )
        .reshape(5, 5, 5, 5)
        .swapaxes(1, 2)
        .reshape(25, 25)
    )

    grid_matrix["5"] = (
        np.array(
            [
                str(letters) + str(quadrant)
                for letters_row in grid_matrix["100"]  # [AA-EE]-[VV-ZZ]
                for quadrants_row in grid_patterns["5"]  # [09NW-99NE]-[00SW-90SE]
                for letters in letters_row  # AA-EE
                for quadrant in quadrants_row  # 09NW-99NE
            ]
        )
        .reshape(25, 20, 25, 20)
        .reshape(25 * 20, 25 * 20)
    )
    return grid_matrix


def get_five_km_index(ref: str) -> Tuple[int, int]:
    """Calculate row and column index of 5km grid reference for 5km grid matrix.

    Args:
        ref (str): 5KM grid reference.

    Returns:
        Tuple[int, int]: row, column index of 5km grid reference matrix.
    """
    "Convert 5km grid reference to row and column"
    first_letter_offset = ord(ref[0]) - ord("A")
    # no I in matrix
    if first_letter_offset > (ord("I") - ord("A")):
        first_letter_offset -= 1
    second_letter_offset = ord(ref[1]) - ord("A")
    # no I in matrix
    if second_letter_offset > (ord("I") - ord("A")):
        second_letter_offset -= 1

    row = (
        (first_letter_offset // 5) * 100  # first letter index
        + (second_letter_offset // 5) * 20  # second letter index
        + (9 - int(ref[3])) * 2  # easting
        + (0 if ref[4] == "N" else 1)  # quadrant
    )
    col = (
        (first_letter_offset % 5) * 100  # first letter index
        + (second_letter_offset % 5) * 20  # second letter index
        + int(ref[2]) * 2  # northing
        + (0 if ref[5] == "W" else 1)  # quadrant
    )
    return row, col


def get_uk_5km_grid_matrix() -> npt.NDArray[Any]:
    """Return a subset of British National Grid Matrix, covering the entire UK
    with 5KM grid references.

    Returns:
        npt.NDArray[Any]: Matrix of UK 5KM grid references
    """
    # Entire UK can be covered with 5km grids stretching between the following points:
    # North East = HL09NW North East = JM99NE
    # South East = SV00SW South West = TW90SE
    north_east_5km = "HL09NW"
    south_west_5km = "TW90SE"

    row_slice = slice(
        get_five_km_index(north_east_5km)[0], get_five_km_index(south_west_5km)[0] + 1
    )
    col_slice = slice(
        get_five_km_index(north_east_5km)[1], get_five_km_index(south_west_5km)[1] + 1
    )

    five_km_grid_matrix = get_grid_matrix()["5"]
    uk_five_km_grid_matrix = five_km_grid_matrix[
        row_slice, col_slice
    ]  # type: npt.NDArray[Any]
    return uk_five_km_grid_matrix
