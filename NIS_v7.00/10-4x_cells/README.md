# Cell Segmentation on Brightfield Images – 4× Objective

The pretrained **4x_cells.oai** brightfield segmentation model was trained on **HeLa cells** in a 96-well plate. This guide shows which cell lines and applications the model can be used for.

## Image Acquisition Conditions

The model was evaluated using:

- Imaging modality: **Brightfield**
- Objective: **4×** 
- Condenser Aperture: **Opened (NA 0.09)**

This AI classifier was evaluated for:

- **Confluence / Coverage** – segmentation adequately represents the area occupied by cells.
- **Cell Count** – individual cells are reliably separated and represented as individual objects.
- **Single-cell Morphology** – object boundaries are sufficiently accurate for morphology measurements.

## Compatible Cell Lines and Applications

| Cell line | Confluence / Coverage | Cell Count | Single-cell Morphology | Notes |
| --------- | --------------------- | ---------- | ---------------------- | ----- |
| HeLa | 🟢 | 🟢 | 🟢 | Reference cell line used for model training. |
| CHO-K1 | 🟢 | 🟢* | 🟢* | Generally reliable. Occasional merging of cells in close contact may cause slight undercounting and affect morphology measurements of the merged objects. |
| A431 | 🟢 | 🔴 | 🔴 | Suitable for confluence/coverage estimation, but individual cells are not segmented reliably enough for count or morphology analysis. |
| Neuro-2a | 🟢 | 🔴 | 🔴 | Suitable for confluence/coverage estimation only. |
| COS | 🟢 | 🔴 | 🔴 | Suitable for confluence/coverage estimation only. |
| HepG2 | 🟢 | 🔴 | 🔴 | Suitable for confluence/coverage estimation only. |
| HT29 | 🔴 | 🔴 | 🔴 | Segmentation is not sufficiently reliable even for confluence/coverage estimation. |
| 3T3 | 🔴 | 🔴 | 🔴 | Segmentation is not sufficiently reliable even for confluence/coverage estimation. |

## Recommended Use

- **Confluence / Coverage** – compatible with **HeLa, CHO-K1, A431, Neuro-2a, COS, and HepG2**.
- **Cell Count and Single-cell Morphology** – compatible with **HeLa and CHO-K1**. Occasional merging of closely contacting CHO-K1 cells may affect cell count and morphology measurements of the affected objects.
- **Image quality** – low or uneven contrast, imaging artifacts, or other structures similar to cells may affect segmentation.
- **Local Contrast** – may improve segmentation in images with low or uneven contrast
- **Other cell lines or acquisition conditions** – performance has not been evaluated and should be verified before quantitative use.