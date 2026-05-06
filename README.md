# GA3 Examples

Examples are organized into folders based on NIS Elements version which they were made with. They are ordered from basic examples to more advanced ones. Every example is accompanied with an nd2 file and a GA3 recipe that reproduces the example. There is a link to the interactive HTML recipe which can be inspected online.

> [!NOTE]
>
> All the examples for older versions should work in the newest versions.

## NIS-Elements version 7.01 and NIS-Express version 2.01 (coming soon)

There is a new [online documentation for NIS-Express](https://nis-express-help.laboratory-imaging.com).
As the [GA3](https://nis-express-help.laboratory-imaging.com/docs/guide/ga3/) functionality is exactly the same as in NIS-Elements
it can be used for both softwares. Changes made in this release render some of previous workflows obsolete or deprecated:

- Improved generic [Python node](https://nis-express-help.laboratory-imaging.com/ref/nodes/nd-processing-conversions/#czlimga3nodepygenericnode)
    - support for Mamba/Conda [Environments](https://nis-express-help.laboratory-imaging.com/ref/nodes/nd-processing-conversions/#python-interpreter)
    (deprecation of extending built-in python)
    - lowering the minimum Python version to 3.10 for external python
    - user parameters and hiding the Python code
    - support for debugging in VS Code
- Integration of popular community based modules
    - [Cellpose3](https://nis-express-help.laboratory-imaging.com/ref/nodes/segmentation/#czlimga3nodepycellpose3node),
    [Cellpose4](https://nis-express-help.laboratory-imaging.com/ref/nodes/segmentation/#czlimga3nodepycellpose4node) in 2D and 3D
    - [Stardist](https://nis-express-help.laboratory-imaging.com/ref/nodes/segmentation/#czlimga3nodepystardist)
    - [Instanseg](https://nis-express-help.laboratory-imaging.com/ref/nodes/segmentation/#czlimga3nodepyinstanseg)
    - [EfficientV2 UNet](https://nis-express-help.laboratory-imaging.com/ref/nodes/segmentation/#czlimga3nodepyefficientv2unet)
    - [UMAP](https://nis-express-help.laboratory-imaging.com/ref/nodes/data-manipulation/#czlimga3nodedataumap)
- Dedicated python nodes for specific tasks
    - [Python Create column](https://nis-express-help.laboratory-imaging.com/ref/nodes/data-manipulation/#czlimga3nodedatapycreatecolumn)
    - [Python Create table](https://nis-express-help.laboratory-imaging.com/ref/nodes/data-manipulation/#czlimga3nodedatapycreatetable)
    - [Matplotlib](https://nis-express-help.laboratory-imaging.com/ref/nodes/results-graphs/#czlimga3nodedatapymplgraph)
- [Basic workflows](https://nis-express-help.laboratory-imaging.com/workflows/) implemented using GA3
- Use LLMs to get the Python code done, see
    - the [movie showing LLM doing PCA](https://lim-public-af010c85-0d3e-4156-9378-5adc1bbef7b3.s3.eu-central-1.amazonaws.com/NISExpress/StaticAssetsForHelp/ref/nodes/data-manipulation/py-create-column-llm-light.mp4) in the in Python Create column node and
    - the [movie extending the above example by making a scatterplot with confidence ellipse](https://lim-public-af010c85-0d3e-4156-9378-5adc1bbef7b3.s3.eu-central-1.amazonaws.com/NISExpress/StaticAssetsForHelp/ref/nodes/results-graphs/py-matplotlib-llm-light.mp4) in the Python Matplotlib node
- Use LLMs to cerate [HTML reports](https://nis-express-help.laboratory-imaging.com/ref/nodes/results-graphs/#ai-assisted-template-generation)

<a id="examples-for-nis-smart-experiment"></a>

### Examples for NIS Smart Experiment - Custom Acquisition

The examples below are intended for use with datasets acquired with NIS Smart Experiment - Custom Acquisition:

- [How to import GA3 recipes](./NIS_v7.00/10-Import_GA3/)
- Recipes similar to Nuclear Translocation
    - [Nuclear Translocation GA3 Recipe](./NIS_v7.00/40-Nuclear_Translocation/)
    - [Nuclear Translocation GA3 Recipe - Detailed Guide](./NIS_v7.00/40-Nuclear_Translocation_Detailed_Guide/)
- more GA3 recipes coming soon...

### Other examples

- coming soon...

## Fixes and examples for NIS-Elements version 6.20 (current)

- [Fixing issues with Python](./NIS_v6.20/00-Fixing_Python_Issues/)
    - Required out-of-process Python version lowered to 3.10
    - Modified table data will not come back from out-of-process Python
    - Adding `Library\bin` to PATH silently
- [Getting started with Python](./NIS_v6.20/50-Python_Getting_Started/)
- [Running cellpose in GA3](./NIS_v6.20/52-Python_cellpose/)
- [Running stardist in GA3](./NIS_v6.20/53-Python_stardist/) (provided by VIB Bioimaging core Leuven)

## Examples for NIS-Elements version 6.10

- [Cell size analysis](./NIS_v6.10/10-Cell_Size_Analysis/)
- [Cell's circle/ring ratio](./NIS_v6.10/11-Circle_Ring_Ratio/)
- [Child-parent relation](./NIS_v6.10/12-Child_Parent_Relation/)
- [Children node example](./NIS_v6.10/13-Children_Node/)
- [Cell-nucleus pairing](./NIS_v6.10/14-Cell_Nucleus_Pairing/)
- [Table statistics](./NIS_v6.10/15-Table_Stats/)
- [Spot location analysis](./NIS_v6.10/26-Spot_Location/)
- [Sholl analysis](./NIS_v6.10/28-Sholl_Analysis/)
- [Tracking algorithms](./NIS_v6.10/30-Tracking_Algorithms/)
- [The NEMO Dots Assembly: Single-Particle Tracking and Analysis](./NIS_v6.10/31-Tracking_NEMO_Dots/)
- [Tracking cells moving between chambers](./NIS_v6.10/32-Tracking_cells_moving_between_chambers/)
