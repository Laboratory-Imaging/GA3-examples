# IMPORTANT: 'limnode' must be imported like this (not from nor as)
import limnode
import numpy as np

model = None
processor = None

# defines output parameter properties
def output(inp: limnode.InDefTuple, out: limnode.OutDefTuple, par: limnode.UserParTuple) -> None:
    out[0].makeNew("SAM_image", "#00ff00").makeInt32()

# return Program for dimension reduction or two-pass processing
def build(par: limnode.UserParTuple, loops: limnode.LoopDefs) -> limnode.Program|None:
    pass

# called for each frame/volume
def run(inp: limnode.InDataTuple, out: limnode.OutDataTuple, par: limnode.UserParTuple, ctx: limnode.RunContext) -> None:
    global model, processor
    if model is None or processor is None:
        from sam3.model_builder import build_sam3_image_model
        from sam3.model.sam3_image_processor import Sam3Processor
        model = build_sam3_image_model()
        processor = Sam3Processor(model)

    import torch

    src = inp[0].data[0, :]
    if src.ndim == 3 and src.shape[2] == 1:
        src = np.repeat(src, 3, axis=2)

    src = torch.from_numpy(src)
    src = src.permute(2, 0, 1)
    src = src.contiguous()
    src = src.float()
    src_min, src_max = src.min(), src.max()
    src = (src - src_min) / (src_max - src_min)

    with torch.autocast("cuda", dtype=torch.bfloat16):
        inference_state = processor.set_image(src)
        inference_state = processor.set_text_prompt(state=inference_state, prompt="people")
    nb_objects = len(inference_state["scores"])

    for i in range(nb_objects):
        m = inference_state["masks"][i].squeeze(0).cpu().numpy()
        out[0].data[0, :, :, 0][m] = i + 1

# child process initialization (when outproc is set)
if __name__ == '__main__':
    from limnode import print
    limnode.child_main(run, output, build)
