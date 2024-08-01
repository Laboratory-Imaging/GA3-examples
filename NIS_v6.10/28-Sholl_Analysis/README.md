# Sholl analysis

Sholl analysis is a method of quantitative analysis used in neural studies to compare and characterize the morphology of different types of neurons, in this analysis we will:

- highlight the neuron and find it's center
- create spherical shell around the neuron center
- find intersections of the neuron and the drawn circles
- count intersections and show their distance from the center, plot a graph line chart for this information

## Input files

Original ND2 image and analysis recipe can be downloaded from this repository:

- ND2 file [[View on GitHub](./GA3_Sholl_Analysis_example.nd2)] [[Download file](https://laboratory-imaging.github.io/GA3-examples/NIS_v6.10/28-Sholl_Analysis/GA3_Sholl_Analysis_example.nd2)]

- GA3 file [[View on GitHub](./GA3_Sholl_Analysis_example.ga3)] [[Download file](https://laboratory-imaging.github.io/GA3-examples/NIS_v6.10/28-Sholl_Analysis/GA3_Sholl_Analysis_example.ga3)]

### The source image data

Original image shows a neuron:

![image](images/00_input.png "Image 1 - input image")

### Complete recipe

The GA3 recipe used in this analysis is also available as an interactive HTML file [[View on GitHub](./recipe.html)] [[View Online](https://laboratory-imaging.github.io/GA3-examples/NIS_v6.10/28-Sholl_Analysis/recipe.html)]

![image](images/01_recipe.png "Image 2 - GA3 recipe")

## Result

This analysis will find center of the neuron, draw circles around the center and count number of intersections between the neuron and drawn circles:

![image](images/02_result.png "Image 3 - Result")

We will also plot line chart for the number of intersections of the neuron witch each drawn circle.

![image](images/03_result_chart.png "Image 4 - Result chart")

## Analysis

As we can see in the recipe, the analysis is done in 5 parts:

1) [Preprocessing of the input image](#1-preprocessing)
2) [Detecting whole neuron](#2-neuron-detection)
3) [Find center of neuron and create spherical shells](#3-find-center-of-the-neuron-and-create-spherical-shells)
4) [Highlight intersections of neuron branches and the spherical shells](#4-highlight-intersections-of-neuron-branches-and-the-spherical-shells)
5) [Plot the results in a graph](#5-plot-the-results-in-a-graph)

### 1. Preprocessing

Preprocessing is done using a single node to enhance the neuron in the image.

**LocalContrast** node enhances contrast in both bright and dark areas of the image, it has following settings:

![image](./images/10_local_contrast.png "Image 5 - Local contrast settings")

### 2. Neuron detection

Detecting neuron in the image will be done with following nodes:

![image](./images/20_neuron_detection.png "Image 6 - Neuron detection nodes")

**Threshold** node will select pixels over specific brightness, this node has following settings:

![image](./images/21_threshold_settings.png "Image 7 - Threshold settings")

**Close** node is then used to fill small holes in the binary, is has following settings:

![image](./images/22_close_settings.png "Image 8 - Close settings")

**SelLargestObject** will select biggest object from selected binary layer, in this case this selects only the object with the neuron.

After step 2, we have highlighted the neuron in the image:

![image](./images/23_result.png "Image 9 - Highlighted neuron")

### 3. Find center of the neuron and create spherical shells

We will use following nodes to find center of the neuron and to draw circles around it:

![image](./images/30_circles_nodes.png "Image 10 - Nodes to draw circles")

**InscribedCircles** node will find the biggest circle that fits into the neuron binary, essentially finding it's centre as shown here:

![image](./images/31_found_circle.png "Image 11 - Center circle in neuron")

**Centroids** node will then select center of this inscribed circle, we will use this point as the center for spherical cells.

**CircleStepPx** node simply sets value 40 to a variable, this variable will be used as spacing between spherical shells.

**ObjectMeas** node will be used to get X and Y coordinates for the centroid in the middle of the neuron, it has following settings:

![image](./images/32_object_meas_settings.png "Image 12 - ObjectMeas node settings")

**FieldMeas** node will get X and Y size of the entire frame, here are the settings for this node:

![image](./images/33_field_meas_settings.png "Image 13 - FieldMeas node settings")

**JsCreateTable** node will use frame size, X and Y coordinates of the neuron center and the distance between between circles to generate coordinates and radiuses for spherical circles, those are the settings for this node:

![image](./images/34_js_create_table_settings.png "Image 14 - JsCreateTable node settings")

This is the body of the JavaScript function:

```js
let n = [];
let x = [];
let y = [];
let r = [];
let i = 1;
let r_step = a[0][0];
let r_ = r_step;
const frame_size = c[_c2][0];
let x_ = b && b[0].length ? b[_b2][0] : frame_size;
let y_ = b && b[0].length ? b[_b3][0] : frame_size;

while (r_ < frame_size) {
  n.push(i);
  x.push(x_);
  y.push(y_);
  r.push(r_);
  r_ += r_step;
  i++;
}

return [ n, x, y, r ];
```

And this is the resulting table:

![image](./images/35_circles_table.png "Image 15 - JsCreateTable node result")

**Circles** node will use the previous table to draw circles on the image, this node has following settings:

![image](./images/36_circles_settings.png "Image 16 - Circles node settings")

**DilateCount** node is a simple variable holding a value, in this case we set how many times to dilate circles in Dilate node below, this variable is set to 1.

**Dilate** node will expand drawn circles which so far are only 1 pixel thick, it uses following settings:

![image](./images/37_dilate_settings.png "Image 17 - Dilate settings")

After this node we can see spherical shell centered around neuron centre 40 pixels apart:

![image](./images/38_dilate_result.png "Image 18 - Dilate result")

As we can see in the image, some circles go over the edge of the image, which splits the circle into several segments, each such segment has it's own ID, however we can check the distance of each segment to the original neuron center to later bin circle segments back together.

**Children** node will be used to match each circle or circle segment back with the center, we will also check distance between circle or circle segment with the neuron center. This node hs following settings:

![image](./images/39_children_node_setting.png "Image 19 - Children setting")

And here is the output of the node:

![image](./images/39.1_children_result.png "Image 20 - Children result")

As we can see in highlighted rows 6 and 7, those 2 circle objects have roughly the same distance from the center, which means they make up the same circle that was just split into multiple segments by the edge of the image.

### 4. Highlight intersections of neuron branches and the spherical shells

Neuron and spherical shells intersections will be found using following nodes:

![image](./images/40_intersection_nodes.png "Image 21 - Intersection nodes")

**And** node will simply create intersection between neuron highlighted in step 2 and circles made in step 3.

**Centroids2** node will find a center for each intersection.

**Dilate2** node will make each center bigger and more visible, just like we did with circles before.

After this node we can see intersections of neuron and circles as a red dot:

![image](./images/41_intersection_result.png "Image 22 - Intersections")

### 5. Plot the results in a graph

At this point, we have segmented the neuron, we have found its center and drew spherical shells around it (and we prepared those for binning in case of segmentation) and we have found intersections of the neuron with circle of circle segments.

We will now count number of intersections in each circle or circle segment, bin circle segments if needed and sum number of intersections for circle segments in the same bin, then we will plot a line chart with number of intersections at each circle.

This will be done with following nodes:

![image](./images/50_graph_result_nodes.png "Image 23 - Graph nodes")

**Parent** node will pair up a parent (circle or circle segment) with all children (intersection blips from step 4), this node will count number of intersection per each circle or circle segment, those are the settings for this node:

![image](./images/51_parent_settings.png "Image 24 - Parent node settings")

**JoinRecords** node with simply link each circle / circle segment and number of intersections step Parent node with data about distance to center from children node in step 3, this is the output table:

![image](./images/52_joined_tables.png "Image 25 - Joined tables")

As we can see, for each circle / circle segment we have found number of intersections on them (CirclesIntersectionCount) and the distance to center (CellCirclesDistance), which we will use to bin circle segments with similar distance from center together.

**JsCreateTable2** node will simply create variables used for binning circle segments with similar distance from neuron center, these are the settings for this node:

![image](./images/53_js_table_settings.png "Image 26 - JSCreateTable settings")

This is the body of the JavaScript function:

```js
let step = a[0][0];
let size = 2 * Math.max(b[0][0], b[1][0])
let count = Math.ceil(size / step)

return [[0], [step * count], [count]];
```

This node will calculate following values used for binning later:

- min = 0
- max = 2080
- count = 52

**BinningSimple** node will bin circle segments with similar distance from center into same bin, this binning will be shown as new column with a value based on starting point of each bin, those are the settings of this node:

![image](./images/54_binning_settings.png "Image 37 - Binning node settings")

As we identified in step 3, circles with ids 6 and 7 had similar distance to center, which meant both were circle segments of the same circle, in the result table below we can see that those 2 circles segments were placed into the same bin in column Class:

![image](./images/55_binning_result.png "Image 38 - Binning result")

**SortRecords** node simply sorts rows based on the binning result - based on the Class column added in previous node.

**ReduceRecords** node will finally add counts of intersections for circle segments in the same bin by grouping the table by Class column, those are the settings for this node:

![image](./images/56_reduce_records_settings.png "Image 39 - ReduceRecords settings")

And here is the result table:

![image](./images/57_reduce_records_result.png "Image 40 - ReduceRecords results")

Here we can see how many intersections there is on each circle (SumCircleIntersectionCount), distance of the circle from center (MeanCellCirclesDistance), attribute used for binning (Class) and count of how many segments was the original circle split into (CountOfCirclesId).

**LineChart** node will use the number of intersections of the neuron with each circle and the distance from the center to create a line chart, these are the settings for this node:

![image](./images/58_linechart_settings.png "Image 41 - LineChart settings")

And as we saw in the results section, this is the output chart:

![image](images/03_result_chart.png "Image 42 - Result chart")

## Conclusion

In this analysis we have detected neuron, found its center, drew spherical shells around it and summarized number of intersections between the circle and the neuron, we also plotted the sums as a line chart.
