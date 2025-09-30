from klibs.KLStructure import FactorSet


# Initialize names and levels of experiment factors

exp_factors = FactorSet({
    "animate_time": [500, 1000, 1500, 2000, 2500],
    "figure_name": ["random", "template_31"],
    "feedback_type": ["none"],
})


# Define custom block types for each type of feedback

exp_factors_vr = exp_factors.override({
    "feedback_type": ["all"]
})

exp_factors_vx = exp_factors.override({
    "feedback_type": ["live_tracing"]
})

exp_factors_xr = exp_factors.override({
    "feedback_type": ["results"]
})

exp_factors_xs = exp_factors.override({
    "feedback_type": ["shape_only"]
})


# Define map of different block types

block_types = {
    "VR": exp_factors_vr,
    "VX": exp_factors_vx,
    "XR": exp_factors_xr,
    "XS": exp_factors_xs,
    "XX": exp_factors,
}
