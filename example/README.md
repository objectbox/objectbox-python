# ObjectBox-Python Examples

This directory contains a couple of examples that demonstrate capabilities of ObjectBox using the Python API.

```shell
cd example # assuming you are in project root dir 
python3 -m venv venv
source venv/bin/activate
pip install objectbox
```

The following examples are available from this directory:

- `tasks`: CRUD Example (see below for details)
- `vectorsearch-cities`: VectorSearch Example (see below for details)
- `ollama`: LLM + VectorSearch Embeddings Script Example (See [ollama/README.md](./ollama/README.md) for details)


## Example: Tasks

This is our classic Tasks application using a CLI.

```
cd tasks
$ python main.py

Welcome to the ObjectBox tasks-list app example. Type help or ? for a list of commands.
> new buy oat
> new buy yeast
> new bake bread
> ls
 ID  Created                        Finished                       Text
  1  Mon Apr 22 11:02:27 2024                                      buy oat
  2  Mon Apr 22 11:02:30 2024                                      buy yeast
  3  Mon Apr 22 11:02:34 2024                                      bake bread
> done 1
> done 2
> ls
> ls
 ID  Created                        Finished                       Text
  1  Mon Apr 22 11:02:27 2024       Mon Apr 22 11:03:02 2024       buy oat
  2  Mon Apr 22 11:02:30 2024       Mon Apr 22 11:03:18 2024       buy yeast
  3  Mon Apr 22 11:02:34 2024                                      bake bread
> exit
```

## Example: Vector-Search 

This example application starts with a pre-defined set of capital cities and their geo coordinates. 
It allows to search for nearest neighbors of a city (`city_neighbors`) or by coordinates (`neighbors`) as well as adding more locations (`add`).

```
cd vector-search-cities
$ python main.py

Welcome to the ObjectBox vectorsearch-cities example. Type help or ? for a list of commands.
> ls
ID   Name                        Latitude  Longitude
  1  Abuja                           9.08       7.40
  2  Accra                           5.60      -0.19
[..]
212  Yerevan                        40.19      44.52
213  Zagreb                         45.81      15.98
> ls Ber
ID   Name                        Latitude  Longitude
 28  Berlin                         52.52      13.40
 29  Bern                           46.95       7.45
> city_neighbors Berlin
ID   Name                        Latitude  Longitude  Score
147  Prague                         50.08      14.44   7.04
 49  Copenhagen                     55.68      12.57  10.66
200  Vienna                         48.21      16.37  27.41
 34  Bratislava                     48.15      17.11  32.82
 89  Ljubljana                      46.06      14.51  42.98
> neighbors 6,52.52,13.405
ID   Name                        Latitude  Longitude  Score
 28  Berlin                         52.52      13.40   0.00
147  Prague                         50.08      14.44   7.04
 49  Copenhagen                     55.68      12.57  10.66
200  Vienna                         48.21      16.37  27.41
 34  Bratislava                     48.15      17.11  32.82
 89  Ljubljana                      46.06      14.51  42.98
 > add Area51, 37.23, -115.81
 > city_neighbors Area51
ID   Name                        Latitude  Longitude  Score
107  Mexico City                    19.43     -99.13  594.86
 27  Belmopan                       17.25     -88.76  1130.92
 64  Guatemala City                 14.63     -90.51  1150.79
164  San Salvador                   13.69     -89.22  1261.12
 67  Havana                         23.11     -82.37  1317.73
```
