# IMPORTANT: 'limnode' must be imported like this (not from nor as)
import limnode
import numpy as np

def init_state_of_model(
    model, #Sam3VideoInferenceWithInstanceInteractivity
    images: list[np.ndarray],
):
    orig_height, orig_width = images[0].shape[:2]

    inference_state = {}
    inference_state["image_size"] = model.image_size
    inference_state["num_frames"] = len(images)
    inference_state["orig_height"] = orig_height
    inference_state["orig_width"] = orig_width
    inference_state["constants"] = {}
    
    import torch
    
    t = torch.from_numpy(np.stack(images, axis=0)).permute(0, 3, 1, 2)
    t = t.to("cuda", non_blocking=True).to(torch.float32)
    t_min, t_max = t.min(), t.max()
    t = (t - t_min) / (t_max - t_min)
    t = torch.nn.functional.interpolate(t, size=(model.image_size, model.image_size), mode="bilinear", align_corners=False)
    
    model._construct_initial_input_batch(inference_state, t)
    
    # initialize extra states
    inference_state["tracker_inference_states"] = []
    inference_state["tracker_metadata"] = {}
    inference_state["feature_cache"] = {}
    inference_state["cached_frame_outputs"] = {}
    inference_state["action_history"] = []  # for logging user actions
    inference_state["is_image_only"] = False
    return inference_state

def new_init_state(
        self,
        resource_path,
        offload_video_to_cpu=False,
        async_loading_frames=False,
        video_loader_type="cv2",
    ):
    return init_state_of_model(self, resource_path)

# defines output parameter properties
def output(inp: limnode.InDefTuple, out: limnode.OutDefTuple, par: limnode.UserParTuple) -> None:
    out[0].makeNew("SAM_video", "#ff0000").makeInt32()

# return Program for dimension reduction or two-pass processing
def build(par: limnode.UserParTuple, loops: limnode.LoopDefs) -> limnode.Program|None:
    return limnode.TwoPassProgram(loops).overAll()

src_imgs = []
dst_imgs = {}
predictor = None
session_id = None

# called for each frame/volume
def run(inp: limnode.InDataTuple, out: limnode.OutDataTuple, par: limnode.UserParTuple, ctx: limnode.RunContext) -> None:
    global src_imgs, dst_imgs, predictor, session_id

    if not isinstance(inp[0], limnode.InputChannelData):
        raise Exception("inp[0] is not limnode.InputChannelData")

    if not isinstance(out[0], limnode.OutputBinaryData):
        raise Exception("out[0] is not limnode.OutputChannelData")

    if predictor is None:
        from sam3.model_builder import build_sam3_video_predictor
        predictor = build_sam3_video_predictor()

        import types
        predictor.model.init_state = types.MethodType(new_init_state, predictor.model)

    if ctx.programPass == 1 and ctx.programIndex == 0:
        if session_id is not None:
            predictor.close_session(session_id)
        src_imgs = []
        dst_imgs = {}

    if ctx.programPass == 1:
        src = inp[0].data[0, :]
        if src.ndim == 3 and src.shape[2] == 1:
            src = np.repeat(src, 3, axis=2)
        src_imgs.append(np.array(src, copy=True))
        
    elif ctx.programPass == 2:
        if ctx.programIndex == 0:
            response = predictor.handle_request(request=dict(
                type="start_session", 
                resource_path=src_imgs
            ))
            session_id = response["session_id"]
            response = predictor.handle_request(request=dict(
                type="add_prompt",
                session_id=session_id,
                frame_index=0,
                text="people",
            )) 
            for response in predictor.handle_stream_request(request=dict(
                type="propagate_in_video",
                session_id=session_id,
            )):
                outputs = response["outputs"]
                obj_ids = outputs["out_obj_ids"]
                masks = outputs["out_binary_masks"]
                dst = np.zeros((out[0].data.shape[1:3]), dtype=out[0].data.dtype)
                for i in range(len(obj_ids)):
                    dst[masks[i].astype(bool)] = obj_ids[i] + 1
                dst_imgs[response["frame_index"]] = dst

        out[0].data[0, :, :, 0] = dst_imgs[ctx.programIndex]  

# child process initialization (when outproc is set)
if __name__ == '__main__':
    from limnode import print
    limnode.child_main(run, output, build)
