# What was done and where it is located

Our project studies a European flights network collected for the period **16–22.02.2026**.  
The work is organized into three main notebooks:

- **`1_eu_flights_data_collection.ipynb`**  
  Data collection and preprocessing, construction of the flights dataset, preparation of node and edge tables, and export of the graph data used in the rest of the project.

- **`2_eu_flights_graph_basic_statistics_distribution_network_models_comparing_centralities.ipynb`**  
  Core structural analysis of the graph: basic statistics, degree distribution analysis, comparison with classical network models, and centrality analysis.

- **`3_eu_flights_graph_visualisation_communities_similarity_ml.ipynb`**  
  Graph visualization, community detection, node similarity / assortative mixing analysis, and ML experiments.

Overall, much part of the code was written in .py files and located in the [private github project](https://github.com/sblenlkj/eu_flights/tree/main). To run the code you must clone the repo, otherwise all the imports of custom classes and functions will fail.

## AI use in the project

I, Dima, write code in Vs Code and rely a lot on Windsurf autocompletion and and refactor  - I do not write prompts. I used chatgpt/google ai serach / perplexity several times in the project and placed prompts under `./data/raw/prompts` folder. While writing py files I used gemini CLI / aider CLI to rename attributes and methods, this is also not "prompt-engineering" business.  

Chatgpt was used to write conclusions for my part with prompt "summarise and write a conclusion". By the way, this file was also generated with its help. 


