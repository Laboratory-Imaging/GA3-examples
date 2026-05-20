# Population Fraction GA3 Recipe - Detailed Guide

## Overview

The Population Fraction Recipe is a flexible workflow for measuring how many objects (**Target Objects**) meet a defined condition  within a  population (**All Objects**).
The resulting measurements are transformed into interactive tables, graphs, dose-response analysis, and assay-quality metrics such as Z-factor.

This example workflow demonstrates **apoptosis analysis** using Caspase 3/7 Green signal detection.

This recipe is split into several sections that reflect a typical analysis workflow:

- **Detection** – identifies All Objects and detects Target Objects (e.g. apoptotic nuclei)
- **Measurements** – extracts features such as object counts and calculates a fraction
- **Outputs** – generates tables, graphs, thumbnails, and wellplate visualizations
- **Calculated outputs** – calculates derived metrics such as Z-factor and dose-response curves
- **Summary & Report** – combines all final figures into a single overview, defines the final layout and generates the HTML report

## Input files

Original ND2 image and analysis recipe can be downloaded from this repository:

- ND2 file [[Download file](https://lim-public-af010c85-0d3e-4156-9378-5adc1bbef7b3.s3.eu-central-1.amazonaws.com/GitHubAssets/GA3_Examples/NIS_v7.00/20-Population_fraction/Apoptosis_Pop_Fraction.nd2)]

- GA3 file [[Download file](https://lim-public-af010c85-0d3e-4156-9378-5adc1bbef7b3.s3.eu-central-1.amazonaws.com/GitHubAssets/GA3_Examples/NIS_v7.00/20-Population_fraction/Population_Fraction_recipe.ga3)]

The GA3 recipe used in this analysis is also available as an interactive HTML file [[View Online](https://laboratory-imaging.github.io/GA3-examples/NIS_v7.00/20-Population_Fraction/recipe.html)]

![image](images/overview.png "Image 1 - Recipe overview")

## Scope and Limitations

### Supported

This workflow is suitable for assays that measure the **fraction of objects meeting a defined condition** within a population.  It assumes that **Target Objects are a subset of All Objects**.

The workflow is primarily count-based but can be extended to other metrics (e.g. intensity, area) if consistently applied to both populations.

### Not Supported

- analyses where Target Objects are not part of All Objects population
- workflows comparing separate object populations
- parent–child or tracking workflows
- region-based intensity measurements (e.g., nucleus vs cytoplasm)
- multinucleated cells or workflows where one nucleus does not represent one cell
- analyses without a defined reference population

### Compatible Assay Types

- live/dead and apoptosis assays (dead or apoptotic cells are measured as a fraction of all detected cells)
- proliferation assays (where marker-positive cells such as EdU or Ki67 are quantified)
- transfection and infection assays (where reporter-positive/infected cells are measured relative to the total cell population)
- marker-based assays, e.g. protein expression, reporter signal, differentiation markers
- DNA damage assays, e.g. γH2AX, 53BP1
- senescence assays, e.g. SA-β-gal, p21/p16
- morphology-based classification assays
- quality-control assays, e.g. valid objects

## Workflow Step-by-step

To better understand the workflow, let’s look at a few sections and how they are constructed:

### Detection

The workflow detects two object groups:

- **All Objects**
- **Target Objects** = Objects associated with the target signal (e.g. Caspase 3/7 Green)

![image](images/detection_example.png "Image 2 - Detection example")

First, all nuclei are segmented using *Segment Objects.ai*. Objects touching the image border are removed using *Remove Border*:

![image](images/border.png "Image 3 - Segment Objects and Remove Border")

The target signal is then detected using *Threshold*. Threshold settings may require optimization depending on signal intensity and background levels:

- low thresholds may include background signal and overestimate the target population
- high thresholds may exclude weak signals and underestimate the target population

Finally, the *Having* binary operation identifies nuclei overlapping with the detected target signal, resulting in the final Target Object subset:

![image](images/detection.png "Image 4 - Threshold")

### Measurements

Now we need to obtain cell counts – the *Object Count* node generates new columns for **All objects** and **Target objects**.

In addition, the **Target Object Fraction** is calculated to quantify the proportion of cells classified as Target Objects. The Target Object Fraction is calculated using the following formula:
`All_objects != 0 ? (Target_objects / All_objects) : 0` - this condition prevents division by zero when no objects are detected:

![image](images/measurements.png "Image 5 - Calculated fraction")

To combine data from all wells into a single table, we use the *Accumulate Records* node, which gathers results from all wells into one output table:

![image](images/accumulate.png "Image 6 - Table with all wells")

### Interactive results table

This forms the basis of the interactive results table. Wells are first sorted in ascending order using the *Sort Records* node. The *Modify Columns* node is then used to adjust column order and visibility for the final table layout:

![image](images/int_table.png "Image 7 - Interactive Results Table")

The table will look like this:

![image](images/table.png "Image 8 - Interactive Results Table")

### Graphs

To retrieve additional image information, we use the *Wellplate Metadata* node connected to All channels. The *Wellplate Metadata* node is also connected to the All Objects and Target Objects binaries:

![image](images/WP_metadata.png "Image 9 - Wellplate Metadata")

The metadata output is then used directly in several wellplate graph nodes:

- WP Labeling
- WP Image
- WP Dosing

![image](images/WP_image.png "Image 10 - WP Dosing, WP Image, WP Labeling")

Other wellplate graph nodes additionally require measurement results. For these cases, the **metadata are merged with the original results table** using the *Join Records* node:

![image](images/join_records.png "Image 11 - Metadata merged with the measured results")

Because some wells may be empty, we use the *Filter Records* node to remove wells without detected objects, resulting in a table containing only non-empty wells:

![image](images/filter.png "Image 12 - Filter out empty wells")

This combined table can now be passed directly to:

- WP Heatmap
- WP Bars

![image](images/WPbars.png "Image 13 -  WP Heatmap, WP Bars")

- Interactive bar chart -  creates an interactive bar chart showing measurements for the selected well
- Dose response analysis - calculates dose-response curves and displays the results as a Fit Plot

![image](images/dosing.png "Image 14 - Barchart and Dose response")

### Z-factor

The same table can also be used for Z-factor calculation to evaluate assay quality. To do this, the data must first be grouped using the *Group Records* node. Z-factor is not calculated from individual wells, but from **two groups of data**:

- negative controls
- positive controls

The *Group Records* node defines which wells belong to each control group before the Z-factor calculation is performed:

![image](images/group.png "Image 15 - Z-factor grouping")

*Filter Groups* is used to remove groups that do not contain any control wells. Only groups with a Control count greater than 0 are passed to the *Z-Factor* node:

![image](images/filter2.png "Image 16 - Filtering empty control wells")

The filtered groups are then passed to the *Z-Factor* node, where the Z-factor is calculated:

![image](images/factor.png "Image 17 - Z-factor")

The resulting table will look like this:

![image](images/table2.png "Image 18 - Z-factor results")

The calculated Z-factor value is repeated across all table rows; however, this can be adjusted later in the workflow.

### Thumbnails for report

To obtain **representative images for the positive and negative controls** in the HTML report, we first use *Filter Records* to keep only the positive and negative control records:

![image](images/thumbnails.png "Image 19 - Filtering positive and negative controls")

The *Render Frame* node generates a representative thumbnail for the report. The node uses several inputs:

- Channel – connected to *All Channels* to access the original image
- Filter – connected to the *Filter Records* node to keep only positive or negative controls
- Binary – connected to the segmented objects

![image](images/render.png "Image 20 - Rendering negative and positive controls")

 Finally, we accumulate all records for the positive and negative controls using *Accumulate Records*:

![image](images/accum.png "Image 21 - Accumulate rendered records")

### Summary

The summary provides an overview of the data. If you would like your summary to follow the same format, you will need to use the following outputs:

- **Global metadata** (e.g. whole-file metadata such as Assay Name, Date Acquired, Experimenter, etc.)
- **Well plate metadata** (Number of detected wells, Number of all wells, Number of wells with no cells)
- **Z-factor** (Z′-factor of the target object fraction)

Global Metadata node is connected directly to All channels, and allows you to select which information you would like to show:

![image](images/global.png "Image 22 - Summary - Global Metadata")

We have already obtained the **Wellplate Metadata** for our graphs — we use this node, pass the data to *Reduce Records*, and aggregate selected columns:

![image](images/reduce2.png "Image 23 - Summary - WP Metadata")

The *Z-factor node* outputs multiple rows containing the same **Z′-factor value**. We use *Reduce Records* with the First aggregation to reduce the table to a single representative row and display the Z′-factor in the summary:

![image](images/zfactor.png "Image 24 - Summary - Z-factor")

The table will look like this:

![image](images/reduce3.png "Image 25 - Summary - Z-factor table")

Now we can join these three tables together using *Append Columns*, resulting in the following table with a single row:

![image](images/join.png "Image 26 - Summary Table")

Finally, we pass the table to the *Summary* node, which creates an overview like this:

![image](images/append.png "Image 27 - Summary node")

## Layout & Display


Now that we have completed our analysis, we need to display the results. To do this, we use the layout nodes *Display, Horizontal*, and *Stacked*. Display nodes also contain labels that help visualize how the results will be arranged. If you would like to reproduce the same result format, follow the layout and display configuration shown below:

![image](images/layout_example.png "Image 28 - Results example") 

![image](images/layout.png "Image 29 - Layout diagram")

### Left Pane

First, connect the *Summary* and *Interactive Table* nodes to a *Stacked* node.

![image](images/stacked.png "Image 30 - Left Pane")

Then connect this *Stacked* node to pane A of a *Horizontal Layout* node. Pane B should be connected to a *FitPlot* node:

![image](images/stacked2.png "Image 31 - Left Pane - Horizontal Layout")

 Finally, connect the *Horizontal Layout* node to the Left pane in the *Display* node:

![image](images/stacked3.png "Image 32 - Left Pane - Display")

### Right Pane

Simply pass Barchart to *Stacked* node and then *Stacked* node can be passed directly to the right pane in the *Display* node:

![image](images/barchart2.png "Image 33 - Right Pane")

### Side Pane

Connect all your wellplate graphs to a *Stacked* node, and then pass the *Stacked* node to the Side Pane in the *Display* node:

![image](images/stacked4.png "Image 34 - Side Pane 1")

![image](images/display.png "Image 35 - Side Pane 2")

### HTML Report

The HTML Report provides a summary of your results. To keep the same report format and ensure it displays correctly, keep the nodes connected as shown and **do not change their order**, as each section in the report corresponds to a specific node in the workflow:

![image](images/html.png "Image 36 - HTML Report")

### Final Notes

The workflow can be adjusted for different assay types by changing the object detection settings, target signal detection, or measurement outputs. Additional graphs, tables, and visualizations can also be added depending on the experiment requirements.
