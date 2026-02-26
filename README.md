# EU flights 
I have collected graph flights in EU for one week (16-22.02.2026). I will add more data for edges (airplane type, company) that will be used for edge embedings and will map target - gpd - to the municipality (ps our node) later. Now the graph is ready for 70% of the project - you can load from csv and experiment. I have agregated it into 3 csv - nodes, edges, flights - they are located in `data/graph_csv`. You can load with pandas, convert to graph with networkx. 

The graph can be loaded from json as well. It is located in `data/flights_week_graph.json`. Domain model for graph is called Graph :). I have written some adapters for it, but matrix and message passing adapters are not ready yet. 

How the data was collected can be seen from `eu_flights_data_collection.ipynb`


## How to load python dependencies 
- clone to your mac with git 
- open in vs code 
- create venv 
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- select it as virtual enviroment in vs code