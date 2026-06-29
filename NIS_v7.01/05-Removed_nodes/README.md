# Nodes removed

## Statistical Box (in Results & Graphs, Legacy Graphs)

Legacy graphs were phased out in the previous versions and replaced by
the new Interactive graphs. They have several shortcomings: old rendering,
cannot be connected to Layout nodes, HTML Report and future nodes to come.
Statistical Box was now removed as a last node from the Legacy Graphs group
because it didn't have a dedicated replacement.

The capabilities and versatility of the Matplotlib together availability
made possible by LLM make it a perfect replacement.

At the same time, Matplotlib integrates into GA3 workflows:
unlike `StatisticalBox`, it can be connected to
[Layouts](https://nis-express-help.laboratory-imaging.com/ref/nodes/results-graphs/#layout),
used in [HTML Report](https://nis-express-help.laboratory-imaging.com/ref/nodes/results-graphs/#czlimga3noderesultspyhtmldocumentv2) and
[Result to Image](https://nis-express-help.laboratory-imaging.com/ref/nodes/results-graphs/#czlimga3noderesultspyhtmldocumentv2).

For examples (with LLM prompts) see the Python workflows in the
[documentation](https://nis-express-help.laboratory-imaging.com/workflows/python/#matplotlib-statistical-boxplots).

## Load & Concatenate (in Input & output, Merge Tables)

Load & Concatenate node was removed and replaced by
[Concatenate HDF5](https://nis-express-help.laboratory-imaging.com/ref/nodes/input-output/#czlimga3noderesultsloadandconcatenate)

## JavaScript nodes

Following nodes

- JS Preprocess and JS Preprocess float (in Image Processing, JavaScript)
- JS Segmentation (in Segmentation, JavaScript)
- JS Postprocess (in Binary processing, JavaScript)
- JS Measure Field, JS Measure Objects (in Measurement, JavaScript)
- JS Scalar Expression (in Data manipulation, JavaScript)

were removed in favor of the
[Python](https://nis-express-help.laboratory-imaging.com/ref/nodes/nd-processing-conversions/#czlimga3nodepygenericnode) node
which is more capable, has better documentation and has LLM support.

## Save/Load Last Color/Binary/Table (in Input & output, Temporary)

Six nodes in Temporary group

- Save Last Color
- Load Last Color
- Save Last Binary
- Load Last Binary
- Save Last Table
- Load Last Table

were removed because of unclear use-case and minimal usage in favor of explicit
saving/loading into ordinary files using
[Python](https://nis-express-help.laboratory-imaging.com/ref/nodes/nd-processing-conversions/#czlimga3nodepygenericnode) node. Users adopted this technique naturally.