# Master's Thesis at Technical University of Munich (TUM)

## Networks and Co-Occurrences of Health Interests in Online Health Platforms

This repository contains scripts and supplementary data files used in this thesis, including data scraped from the HealthUnlocked platform. It also includes Jupyter notebooks for data preprocessing, tag clustering, network construction, and network analysis.

### Abstract
This thesis investigates co-occurrence patterns of health-related tags on HealthUnlocked, a large online peer-support platform. It identifies common patterns of tag co-occurrence in user profiles — both globally and within condition-focused communities — and analyzes how these patterns vary across demographic groups (country, age, ethnicity, and gender). Co-occurrence networks were constructed using user-cluster bipartite graphs and projected onto cluster-cluster unipartite networks. The results highlight central health concerns and differences between demographic groups, with potential applications in personalized support.

### Dataset
The dataset for the general patterns analysis includes 8,554 user profiles with health-related tags, collected via 305 health-related keywords using the platform’s global search. For the community-specific analysis, profiles of 15,757 members from 324 condition-dedicated communities were collected. In total, 2,965 unique tags were gathered and clustered into 23 meaningful categories to facilitate the analysis.

### 📁 Repository Structure
```
tum-thesis/
├── data/                                 # All input/output data (processed and raw)
│   ├── bipartite_network/                # Projection of user-cluster bipartite networks onto cluster-cluster networks
│   │   ├── community-specific_patterns/  # Community-level co-occurrence networks and analysis
│   │   │   ├── network_analysis/         # Network metrics and bipartite graph visualization
│   │   │   └── cluster_co-occurrence_edges_by_comm/  # Edges of unipartite cluster-cluster networks for each community
│   │   └── general_patterns/             # General profiles-based co-occurrence networks
│   │       ├── demographics/             # Edges of cluster-cluster networks by demographic subgroup
│   │       │   ├── age/                  # Age group-specific networks
│   │       │   ├── country/              # Country-specific networks
│   │       │   ├── ethnicity/            # Ethnicity-specific networks
│   │       │   ├── gender/               # Gender-specific networks
|   |       |   └── network_analysis/     # Demographic-specific network metrics
│   │       ├── network_analysis/         # Global network metrics
│   │       └── cluster_co-occurrence_edges.json  # Edges of unipartite cluster-cluster (global) network
│   │
│   ├── data_cleaned/                     # Pre-processed data (e.g. standardized "gender" and "ethnicity" entries)
│   ├── scraped_data/                     # Raw scraped data from HealthUnlocked
│   ├── tag_clustering/                   # Clustering experiments and results
│   └── keywords_generated.csv            # Final tag list with assigned clusters
│
├── jupyter notebooks/                    # Notebooks for data pre-processing, clustering, network construction, and analysis
│
├── config.py                             # Centralized configuration (e.g., paths, constants, CSS selectors)
├── helpers.py                            # Utility functions (e.g., login, scraping pagination, loading JSON)
├── keywords_handler.py                   # Extends the list of original keywords by adding lemmas
├── keywords_initializer.py               # Initializes the list of original keywords
├── main.py                               # Entry point for the web scraping pipeline
└── scrapers.py                           # Web scraping and data collection logic```