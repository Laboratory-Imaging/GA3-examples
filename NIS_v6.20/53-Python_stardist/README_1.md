
# Stardist in NIS

This workflow was kindly provided by *Nikky Corthout* and *Benjamin Pavie* from
[VIB Bioimaging core Leuven, VIB Technologies, VIB Center for Brain and Disease research, KU Leuven Department of Neurosciences](https://bioimagingcore-leuven.sites.vib.be/en).

Updated in November, 2025 by LIM to benefit from improvements on NIS Elements side.

## Conda installation

> [!WARNING]
> In order for this workflow to work you **must apply the fix** described in [Fixing issues with Python](../00-Fixing_Python_Issues/).

> [!NOTE]
> TensorFlow 2.10 was the last TensorFlow release that supported GPU on native-Windows
> (see [tensorflow guide](https://www.tensorflow.org/install/pip#windows-native)).

### Install the conda/mamba environment

```yaml
name: stardist_gpu_3_10
channels:
    - conda-forge
dependencies:
    - python=3.10
    - cudatoolkit=11.2
    - cudnn=8.1.0
    - pip
    - pip:
        - tensorflow<2.11
        - stardist
        - numpy==1.26
```

You need the [environment_1.yml](https://github.com/Laboratory-Imaging/GA3-examples-private/blob/main/NIS_v6.20/53-Python_stardist/environment_1.yml) for
Conda:

```bash
conda env create -f environment_1.yml
conda activate stardist_gpu_3_10
```

or for micromamba

```bash
micromamba create --prefix "D:\testing_stardist" -f "environment_1.yaml" -y
```

replace the `D:\testing_stardist` with a folder of your choice.

## With NIS

- Start NIS, e.g. `NIS-Elements AR 6.20.00 64-bit`
- Start the Analysis Explorer `Image > Analysis Explorer`

### Open an image

Drag and drop an image into NIS-Elements

### Create a new recipe
- Create a new `Recipe > General Analysis 3`

### Adding the Nodes

- `Source & References > Channels` *if the channel node is not present already*
- `ND Processing  Conversion > Python scripting > Python`
- `Binary processing > Colors & Numbers > Color by Id`

### Edit the python script

Click on the `...` on the python3 node

```python
# IMPORTANT: 'limnode' must be imported like this (not from nor as)
import limnode

model = None

# defines output parameter properties
def output(inp: tuple[limnode.AnyInDef], out: tuple[limnode.AnyOutDef]) -> None:
    out[0].makeNew("nuclei", (0, 255, 255)).makeInt32()

# return Program for dimension reduction or two-pass processing
def build(loops: list[limnode.LoopDef]) -> limnode.Program|None:
    return None

# called for each frame/volume
def run(inp: tuple[limnode.AnyInData], out: tuple[limnode.AnyOutData], ctx: limnode.RunContext) -> None:
    global model

    import numpy
    from csbdeep.utils import normalize
    from stardist.models import StarDist2D

    # Check GPU
    # import tensorflow as tf
    # print(tf.config.list_physical_devices('GPU'))

    if model is None:
        model = StarDist2D.from_pretrained('2D_versatile_fluo')

    img = inp[0].data[0, :, :, 0]
    labels,_= model.predict_instances(normalize(img, 1, 99.8, axis=(0, 1)))

    separated = limnode.separateLabeledImage(labels)
    out[0].data[:, :, :, 0] = separated.astype(numpy.int32)

# child process initialization (when outproc is set)
if __name__ == '__main__':
    limnode.child_main(run, output, build)
```

The code differs slightly from the original:
1. Loading libraries is delayed until the run(...) function as it slightly improves the responsiveness of NIS.
2. Models download is handled automatically. You can still download custom models into the .keras folder.
3. There is a code to check if GPU is used. Uncomment it and go NIS logs (menu: Help → Open Log File... ) to see the output.

> [!NOTE]
> During the Recipe run the module (and all the libraries) is loaded only once for all frames.

## Select the python executable

Select the `D:\testing_stardist\pythonw.exe` file within the environment. Otherwise a python window will pop up during the process.

![image](images/02_Python_node_dialog.png)

## Connect the node
![image](images/03_Python_node_connected.png)

> [!NOTE]
> **OSError: [WinError 1314] A required privilege is not held ...**
>
> If this error happens the user has no right to create symbolic links.
>
> Th easiest solution on Windows 11 is to Enable Windows Developer Mode:
> Settings → System → For Developers → Developer Mode


## Preview
Click on preview to initialize the processing
