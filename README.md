# EU flights 
I have collected flights across EU countries in a graph during one week (16-22.02.2026). What can we do:
- Create a network. There should be some attributes of nodes (**done**): cities (they are called municipalities) are our nodes and existing flight routes are edges. The graph is directional, edges have weights (number of flights), nodes have also weights (in-flights and out-flights number). For other attributes look at the data. Right now nodes=513, edges=10236; we can also add extra countries like Switzerland and Norway.
- Describe what does it contain (what are nodes and edges, which attributes) 
- Visualize network - we can visualise with html map / networks. 
- Give basic characteristics (number of nodes, number of edges, clustering coef., see Lecture 1)
- Analyze degree distribution (Compare with power law, binominal, compute hyperparameters – find parameters of the distributions)
- Compare with network models (ER, BA, WS)
- Compute centralities, PageRank/HITS for directed graphs
- Investigate node similarity, assortative mixing
- Find communities using different algorithms

All above can be done right now. The graph is stored both in json and csv formats; 3 csv - nodes, edges, flights - are located in `data/graph_csv`. You can load with pandas, convert to graph with networkx. For more, look at `eu_flights_data_collection.ipynb`. If you do sm, pleasee, create a new ipynb file. 

- I also created embedings for edges: airplane models based on icao code, you can find them in `data/embedings_from_icao.json`, airplane company based on callsign code (`data/embedings_from_callsign.json`).  The domain model now supports attaching an embedding vector per edge; call `graph.create_edge_embeddings(...)` with your embedding schemas and pass `assign_to_edges=True` to populate each edge and have the pandas adapter expose the values as separate columns.  Column names are kept in `Graph.edge_embedding_columns`.

How the data was collected can be seen from `eu_flights_data_collection.ipynb`

PS The python folder contains some code that is usefull to save/load the graph, convert it from one implementation to another (for example, adjacency matrix, networkx, pandas df). I operate on graph domain model for graph that is called Graph :) I have some adapters for it, but matrix and message passing adapters are not ready yet.

## ML Task
Describe and solve ML task (node classification/link prediction/etc., check several models/approaches). 

We can predict gpd per inhabitants based on flight activity. 
We can also predict the number of flights (our edges) between cities and their attributes (what company operates the flight, what airplane model is used, etc.). This information is included at embeddings. 

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
