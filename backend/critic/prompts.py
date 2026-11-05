# Prompt templates for CAD generation and visual critique
from __future__ import annotations

from schemas import CodeType

CODEGEN_SYSTEM = (
    "Write {lang} source for the described mechanical part. Use practical dimensions "
    "and make one watertight, manifold solid with walls at least 1 mm thick. Add "
    "mounting features when the description calls for them. Return only the source "
    "inside one fenced code block."
)

CODEGEN_USER = "Description: {prompt}\n\nTarget dimensions (mm, if any): {dims}\n\nWrite the {lang} code."

CRITIC_SYSTEM = (
    "Review this mechanical part as a design engineer. The attached Muybridge plate is "
    "a 4x3 grid "
    "of wireframe views at varying azimuth/elevation, with a dashed bounding box and "
    "dimension labels; 4 frames also show cross-sectional slices. You also receive the "
    "automated trimesh assertions and the current source code.\n\n"
    "Look for spatial defects the geometric checks may miss: floating/disconnected "
    "geometry, self-intersecting bodies, blocked or un-drilled screw holes, walls "
    "that are too thin in a specific region, features in the wrong place relative to "
    "the bounding box, parts that would not print, and dimension mismatches.\n\n"
    "Mark the part approved only when the evidence supports it. If it fails, return a "
    "corrected full source file. Respond with JSON only, with no prose, in a "
    "single fenced ```json block with this shape:\n"
    "{{\n"
    "  \"approved\": true|false,\n"
    "  \"errors\": [\"short string per defect\"],\n"
    "  \"critique\": \"one or two sentences of spatial reasoning\",\n"
    "  \"suggested_code\": \"full revised {lang} source that compiles to the fixed part\"\n"
    "}}\n"
    "When approved is true, suggested_code may be empty. Keep the code self-contained "
    "and assignable to the top-level name `part` (build123d) or a top-level model "
    "(OpenSCAD)."
)

CRITIC_USER = (
    "Current {lang} code:\n```{lang}\n{code}\n```\n\n"
    "Automated assertions:\n{assertions}\n\n"
    "Dimensions in mm: {dims}\n"
    "Inspect the attached 12-frame Muybridge plate and respond with the JSON object."
)
