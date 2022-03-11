# Spatial Tools and Utilities

### The United Kingdom postcodes to British National Grid References:

> CSV and Parquet files can be generated using `postcode_to_british_national_grid.ipynb` notebook.

Output has the following structure:

| Postcode   |     lat |       lon | 100km_grid   | 50km_grid   | 20km_grid   | 10km_grid   | 5km_grid   | 1km_grid   |
|:-----------|--------:|----------:|:-------------|:------------|:------------|:------------|:-----------|:-----------|
| XX0 1XX    | 50.1234 | -0.123456 | XX           | XXXX        | XX00        | XX00        | XX00NW     | XX1234     |
| XX012XX    | 50.1234 |  0.789456 | XX           | XXXX        | XX00        | XX00        | XX00NE     | XX1234     |


## License

Required data to run scripts and notebooks are subject to the following licenses:

- Contains OS data © Crown copyright and database right 2019-2022
- Contains Royal Mail data © Royal Mail copyright and database right 2019-2022
- Source: Office for National Statistics licensed under the Open Government Licence v.3.0

Shared code and notebooks licensed under MIT License.

© 2022 - Bubo.AI