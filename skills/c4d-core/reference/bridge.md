# C4D bridge — справочник команд

Сгенерировано из докстрингов `cinema4d_mcp_bridge/bridge/handlers/` (C4D 2024.2). Протокол: TCP 127.0.0.1:18710, JSON-строка `{"id","command","params"}` + `\n`.

## ping  `[basics]`

_нет докстринга_

## undo  `[basics]`

Pop up to ``steps`` entries off the active document's undo stack.

Stops early if the undo stack is exhausted. Returns the number of steps
actually performed so callers can detect the stack-empty case.

## render  `[basics]`

Render the active document using its currently-active render data.

Width / height / renderer etc. come from the active RenderData — adjust
it via ``create_render_data`` + ``set_params`` beforehand if needed.

## preview_render  `[preview_render]`

Independent verification render using the Viewport renderer.

Designed for agent verification loops: fast, sketch-style, returns the
PNG inline (base64) without touching the user's active RenderData.

params:
  width, height:  output size in pixels (default 1024 x 1024, capped 4096).
  view:           "current" (default — uses active BaseDraw camera),
                  "top" | "bottom" | "left" | "right" | "front" | "back"
                  (creates a temp camera looking at the scene bounds).
  camera:         optional object name; overrides ``view`` and renders
                  from that scene camera. Mutually exclusive with a
                  non-"current" view.
  frame:          optional integer frame; defaults to current time.
  take:           optional take name; defaults to current take.
  save_path:      optional absolute PNG path. When set, the rendered
                  image is also written to disk (parent dir must exist)
                  in addition to being returned inline as base64.

## reset_scene  `[basics]`

Swap in a fresh empty document, dropping the previous doc entirely.

Cheap way for test suites and agent workflows to get a clean slate
without routing through ``exec_python`` (opt-in) or dozens of
``remove_entity`` RPCs. Optionally prefix-filtered: when ``prefix`` is
supplied, we only clear objects / materials / render data whose name
starts with that prefix and leave the rest of the scene alone.

params:
  prefix:        optional name prefix. When set, only matching top-level
                 objects / materials / non-active render data are
                 removed. When omitted, the current document is replaced
                 with a brand-new empty BaseDocument.
  keep_active_rd: bool (default True). Only honoured in prefix mode —
                 protects the currently-active render data from deletion
                 regardless of its name.

## exec_python  `[script]`

Run arbitrary Python on C4D's main thread.

Globals provided: ``c4d``, ``documents``, ``doc`` (active document),
``op`` (first selected object). Assign to ``result`` inside the code to
return a value. Both ``stdout`` and ``stderr`` are captured.

## list_entities  `[entities]`

_нет докстринга_

## describe  `[entities]`

_нет докстринга_

## get_params  `[entities]`

Read parameters by id or DescID path.

params:
  handle: target
  ids:    list of path entries. Each entry is one of:
            - int                 (top-level id)
            - [int, int, ...]     (chained DescID; dtypes inferred)
            - ["x"|"y"|"z", ...]  (vector sub-component string)
            - [[id, "dtype"], …]  (explicit dtype overrides: real/long/bool/vector)

Returns ``{values: [{path, value}, ...]}`` in the same order as ``ids``.

## set_params  `[entities]`

Write parameters by id or DescID path, wrapped in a single undo group.

params:
  handle: target
  values: list of ``{path, value}`` entries — ``path`` accepts the same
          forms as ``get_params.ids``. Lists of 3 numbers auto-coerce
          into ``c4d.Vector`` for vector-typed destinations.

Returns ``{applied: [{path, value}], errors: [{path, error}]}``.

## get_container  `[entities]`

_нет докстринга_

## dump_shader  `[entities]`

Recursively dump a shader tree into JSON.

Captures ``type_id`` / ``type_name`` / ``name`` per node; promotes
``c4d.Xbitmap`` paths to a ``file`` field; heuristically surfaces
image-like strings stored in other shader BaseContainers as
``file_candidates``; and expands shader links stored inside the container
as ``linked_shaders`` — the shape used by Redshift / Fusion / Colorizer
whose internals don't appear via ``GetDown``.

## create_entity  `[entities]`

Create an object / tag / material / shader and link it to its parent.

params:
  kind:     "object" | "tag" | "material" | "shader"
  type_id:  plugin id of the thing to create — int, alias ("cube"/"null"/…
            for objects) or numeric string
  name:     optional
  parent:   handle of parent (required for tag/shader; optional for object)
  params:   {param_id: value} to set after allocation
  position: [x, y, z] for objects (relative to parent)
  slots:    list of container slot IDs to assign the created shader to
            (e.g. [3740, 3741] for Octane AOV dual-slot)

## set_keyframe  `[animation]`

Add or update a keyframe on the resolved entity's parameter.

Supports scalar (REAL/LONG/BOOL) and vector (x/y/z) parameters. The dtype
is inferred from the object's description; pass ``dtype`` explicitly to
override (e.g. ``"long"`` for enum-backed params).

params:
  handle:    target
  param_id:  top-level description id (int)
  component: "x" | "y" | "z" | null   (sub-component for vector params)
  frame:     frame number (int)
  value:     new value (number or bool)
  fps:       optional override for time base (default: doc fps)
  interp:    "linear" | "spline" | "step"  (default "spline")
  dtype:     optional override: "real" | "long" | "bool" | "vector"

## remove_entity  `[entities]`

_нет докстринга_

## set_document  `[document_io]`

Update document-level settings.

Supported keys: fps, frame_start, frame_end, current_frame, active_camera (name).
Also mirrors fps + frame range to the active render data.

## batch  `[script]`

Execute a list of operations in one RPC, wrapped in a single undo group.

params:
  ops: [{op: "<handler_name>", args: {...}}, ...]
  stop_on_error: bool (default False). When False, individual failures
    are recorded in the per-op result but the batch keeps running.

Returns: {"results": [{index, op, result? | error?}, ...]}

## call_command  `[script]`

Invoke a Cinema 4D command by plugin id (``c4d.CallCommand``).

CallCommand runs synchronously in many cases (e.g. Render to Picture
Viewer). Long-running commands may exceed the default 30s tool timeout —
pass a larger ``timeout_ms`` via exec_python if needed.

## list_plugins  `[script]`

List plugins of any ``PLUGINTYPE`` (command, material, shader, ...).

Unified plugin discovery for commands, objects, materials, shaders, video
posts, scene loaders etc. Entries include ``plugin`` (parent folder of the
binary) and ``plugin_file`` (basename) so plugins with generic display
names like "Convert Materials" can be attributed to their host plugin.

## import_scene  `[document_io]`

Merge an external scene file (abc/fbx/obj/c4d/...) into the active document.

params:
  path:    absolute file path
  filter:  "objects" | "materials" | "all" (default "all")
  parent:  optional parent handle — newly-imported top-level objects are
           moved under this object after import
  rename:  optional new name for the first imported top-level object

Returns:
  {"imported": [{name, type_id, type_name}, ...], "count": N}

## create_render_data  `[render_data]`

Create (or update-if-exists) a RenderData with common options.

params:
  name:              string (required)
  parent:            string — parent RenderData name (default: top level).
                     Lets you build nested render-preset trees.
  width, height:     int (pixels)
  renderer:          int (plugin id) or alias:
                     "octane"/"standard"/"physical"/"redshift"/"cycles"/"viewport"
  fps:               int (also sets Use Project Frame Rate off)
  frame_start:       int
  frame_end:         int
  frame_sequence:    "manual"/"current"/"all"/"preview"/"custom"
                     (default "manual" when frame_start/end given)
  make_active:       bool
  update_if_exists:  bool
  params:            extra {param_id: value} to set after allocation

## create_take  `[takes]`

Create or update a Take, optionally linking camera and render data.

params:
  name:             string (required)
  parent:           string — parent take name (default: main take)
  camera:           string — object name for the take's camera override
  render_data:      string — render data name to link
  checked:          bool (default true on create)
  make_active:      bool
  update_if_exists: bool
  clear_camera:     bool — explicitly unset the camera override
  clear_render_data: bool — explicitly unset the render data override

## take_override  `[takes]`

Write per-Take parameter overrides onto a target node.

A Take override records that a specific parameter on a specific node
differs in this take vs. its parent. The C4D flow is:
  override = take.FindOverride(td, node) or take.OverrideNode(td, node)
  override.UpdateSceneNode(td, descid)    # register this param
  override[descid] = value                # write the override value

params:
  take:    take name (required)
  target:  handle of the node to override (object / tag / material /
           render_data / video_post / shader). Required.
  values:  list of {path, value} — same path syntax as set_params.
           (paths go through _path_to_desc_id, so int / [int,...] /
           vector sub-keys 'x'/'y'/'z' all work.)
  clear:   list of paths to drop from the override (optional)
  remove_all: bool — drop the entire override for this node
  params:  shorthand {pid: value} for flat writes (applied after `values`)

Returns:
  {applied:[{path,value}], errors:[{path,error}],
   cleared:[path,...], removed_all:bool, take, target}

## create_marker  `[markers]`

Create a timeline marker at a given frame/time with name, colour, length.

params:
  frame:         int — frame position (mutually exclusive with time_seconds)
  time_seconds:  float — position in seconds (alternative to frame)
  name:          string — marker label (default "")
  color:         [r, g, b] floats 0..1 (optional)
  length_frames: int — marker length in frames (optional, default 0)

Returns the created marker's info (see ``list_markers``).

## list_markers  `[markers]`

Enumerate every timeline marker with its frame, name, colour and length.

Returns ``{markers: [...], count: N}``. Each entry carries the ``index``
handle used by ``set_marker`` / ``remove_marker``.

## set_marker  `[markers]`

Edit an existing marker: rename, recolour, move, or resize it.

Target (exactly one):
  index: int — position in the marker chain (see ``list_markers``)
  frame: int — match the marker at this frame (errors on ambiguity)
  name:  str — match by name (errors on ambiguity)

Updates (any subset; at least one required):
  new_name:         string
  color:            [r, g, b] floats 0..1
  new_frame:        int — move to this frame
  new_time_seconds: float — move to this time in seconds (mutually
                    exclusive with new_frame)
  length_frames:    int — marker length in frames

Returns the updated marker's info.

## remove_marker  `[markers]`

Delete one timeline marker, or all of them.

params:
  all:   bool — remove every marker (ignores the selectors below)
  index: int — position in the marker chain (see ``list_markers``)
  frame: int — match the marker at this frame (errors on ambiguity)
  name:  str — match by name (errors on ambiguity)

Pass ``all:true`` or exactly one of index / frame / name.
Returns ``{removed: N}``.

## sample_transform  `[transform]`

Evaluate the scene at each requested frame and sample an object's transform.

params:
  handle:  object handle (required) — must resolve to a BaseObject
  frames:  list[int] of frames to sample (required, 1..500)
  fps:     optional override (default: doc fps)
  space:   "global" (default) | "local"
  format:  "off_rot" (default) — returns pos+rot(HPB radians)
           "matrix"           — returns 4x3 matrix rows
  restore_time: bool (default true)

## get_selection  `[selection]`

_нет докстринга_

## set_selection  `[selection]`

Update the document's active selection.

params:
  objects:  list of object handles (first = active, rest selected)
  tag:      tag handle for the active tag
  material: material handle for the active material
  mode:     "replace" (default) | "add" — applies to ``objects``
  clear:    bool — if True, deselect everything first (and skip other fields)

## move_entity  `[hierarchy]`

Reparent or reorder a node in the scene, take, or render_data hierarchy.

Exactly one destination field must be provided:
  parent:  handle — insert as the last child of this node
  before:  handle — place immediately before this sibling
  after:   handle — place immediately after this sibling
  to_root: bool   — promote to the top of the hierarchy
                    (objects: doc root; takes: under Main; render_data: top level)

The handle's kind decides the hierarchy:
  object       — c4d.BaseObject parent/sibling required
  take         — c4d.BaseTake parent/sibling required; Main cannot be moved
  render_data  — c4d.documents.RenderData parent/sibling required

params:
  handle:  target node

## clone_entity  `[hierarchy]`

Duplicate an entity.

Supported kinds:
  object / tag / material / shader — via GetClone + parent insert
  render_data                      — via GetClone + doc.InsertRenderData
  video_post                       — via GetClone + rd.InsertVideoPost
  take                             — via TakeData.AddTake(cloneFrom=src),
                                     which also copies existing overrides

params:
  handle:  source entity
  name:    optional new name for the clone
  parent:  object clone: destination parent (defaults to source sibling)
           tag / shader clone: required owner
           video_post clone: optional target render_data (defaults to source's)
           take clone: optional parent take (defaults to source's parent)
           render_data clone: optional parent render_data (defaults to top level)

## modeling_command  `[modeling]`

Run ``c4d.utils.SendModelingCommand`` on the resolved targets.

params:
  command: alias (see _COMMAND_ALIASES) or raw MCOMMAND_* int
  targets: list of object handles
  mode:    "all" (default) | "edge" | "point" | "poly"
  params:  optional {param_id: value} BaseContainer passed as ``bc``

## get_mesh  `[mesh]`

Read points and polygons (or spline segments) from an editable object.

params:
  handle:      target
  max_points:  optional int cap (default 50_000)
  max_polys:   optional int cap (default 50_000)
  include:     optional list — subset of
               ["normals", "selections"]; points+polygons/segments are
               always returned. "selections" adds ``point_selection``,
               ``poly_selection``, ``edge_selection`` as sorted index
               lists drawn from the BaseSelect components of the mesh.

## set_mesh  `[mesh]`

Overwrite the points (and optionally polygons) of an editable object.

params:
  handle:   target PointObject / PolygonObject
  points:   list of [x,y,z]
  polygons: list of [a,b,c,d] or [a,b,c] (triangles are expanded to quads)

If ``polygons`` is omitted, only points are rewritten (count must match).

## set_mesh_selection  `[mesh]`

Overwrite point / polygon / edge selection on an editable mesh.

params:
  handle:    target (PointObject / PolygonObject)
  kind:      "point" | "polygon" | "edge"
  indices:   list[int] to select. Existing selection is fully replaced.

## save_document  `[document_io]`

Save the active document to disk.

params:
  path:   absolute output path
  format: "c4d" (default) | "abc" | "fbx" | "obj" | "stl" | "ply" | "usd" | "gltf"
  copy:   bool (default False) — when True, the document's internal name/
          path is **not** updated after saving (mirrors Save-As-Copy).

## open_document  `[document_io]`

Load a scene file and optionally make it the active document.

params:
  path:        absolute path to a loadable C4D scene file
  make_active: bool (default True)

## new_document  `[document_io]`

Insert a fresh empty BaseDocument and optionally make it active.

params:
  name:        optional document display name
  make_active: bool (default True)

## list_documents  `[document_io]`

Enumerate the open documents so a caller can pick one to switch to.

Returns one entry per open document with its list ``index`` (the handle
accepted by ``set_active_document``), name, path and whether it is active.
``get_document_state`` only reports the active document; this fills the gap.

## set_active_document  `[document_io]`

Switch focus to an already-open document, identified by index or name.

params:
  index: 0-based position in the document list (see ``list_documents``)
  name:  document name; errors if it matches zero or several documents

Exactly one of ``index`` / ``name`` must be given. Loading a file from disk
is ``open_document``; this only switches between documents already open.

## close_document  `[document_io]`

Close an open document, identified by index or name.

params:
  index: 0-based position in the document list (see ``list_documents``)
  name:  document name; errors if it matches zero or several documents
  force: bool (default False) — required to close a document with unsaved
         changes, since ``KillDocument`` discards them without a prompt

Exactly one of ``index`` / ``name`` must be given. C4D always keeps at least
one document, so closing the last one leaves a fresh empty document active.

## list_graph_nodes  `[node_materials]`

Traverse a node graph (material or scene-nodes) and return nodes.

params:
  handle:     material handle (required unless scope='document')
  scope:      'document' → target scene-nodes graph on the active doc
  node_space: alias ("standard"/"redshift"/"scenenodes") or maxon.Id.
              Default "standard" for materials, "scenenodes" for docs.

## list_graph_node_assets  `[node_materials]`

Enumerate registered node-template assets for a node space.

LLMs need these ids to know what ``$type`` values ``apply_graph_description``
will accept. We enumerate the Maxon ``NodeTemplate`` assets (reading ids only,
to stay cheap and crash-safe) and, for the neutron / Scene Nodes space, filter
to the families that are actually addable there.

params:
  node_space: alias ('standard'/'redshift'/'scenenodes') or maxon.Id.
              Default 'standard'.

## get_graph_info  `[node_materials]`

Inspect which node spaces a material exposes and which is active.

params:
  handle: material handle

## apply_graph_description  `[node_materials]`

Apply a ``maxon.GraphDescription`` to a node material's graph.

The ``description`` argument mirrors the declarative dict accepted by
``GraphDescription.ApplyDescription`` (see Maxon's docs for the $type /
$id / '->' connection syntax).

params:
  handle:      material handle
  description: nested dict (see maxon.GraphDescription)
  node_space:  alias or maxon.Id (default 'standard')
  create_graph: bool — when True, create the graph if missing (default True)

## set_graph_port  `[node_materials]`

Set a single port's constant value on a node addressable by id.

Wraps ``GraphDescription.ApplyDescription`` with a ``$query`` targeting
the requested node id — keeps the surface simple for one-port edits.

params:
  handle:     material handle
  node_space: alias / maxon.Id (default 'standard')
  node_id:    the $id of the node to mutate
  port:       port path (e.g. 'Base/Metalness')
  value:      new value (number / bool / string / [x,y,z] for vectors)

## remove_graph_node  `[node_materials]`

Remove a node by id from a material's graph.

Uses the low-level ``graph.RemoveNode`` when available; otherwise falls
back to ``GraphDescription`` with a delete directive.

params:
  handle:     material handle
  node_space: alias or maxon.Id (default 'standard')
  node_id:    the id of the node to remove

## assign_material  `[tags]`

Link a material to an object by creating (or updating) a Texture tag.

params:
  object:     object handle (required)
  material:   material handle (required)
  projection: alias (see _PROJECTION_ALIASES) — default preserves existing
  uv_offset:  [u,v] — sets TEXTURETAG_OFFSETX/Y when provided
  uv_tiles:   [u,v] — sets TEXTURETAG_TILESX/Y when provided
  restrict_to_selection: string — polygon selection tag name this texture tag applies to
  update_if_exists: bool (default False). When True and a Texture tag
              already exists, its material link is updated in place
              instead of appending a second tag.
  name:       optional display name for the created/updated tag

## set_transform  `[transform]`

Set an object's transform.

params:
  handle: object handle
  pos:    [x, y, z]                (optional)
  rot:    [h, p, b]  radians       (optional)
  scale:  [sx, sy, sz]             (optional)
  matrix: [[off], [v1], [v2], [v3]]  4x3 list (exclusive with pos/rot/scale)
  space:  "local" (default) | "global"

## add_user_data  `[user_data]`

Add a User Data slot to the target.

params:
  handle:  target (any BaseList2D that supports AddUserData)
  name:    display name (required)
  dtype:   'real' | 'long' | 'bool' | 'vector' | 'string' | 'color' |
           'filename' | 'time' | 'link'
  value:   optional initial value (auto-coerced for vectors)
  default: optional default (stored on the UD descriptor)
  min, max, step: numeric bounds (optional, real/long only)

## list_user_data  `[user_data]`

Enumerate user-data slots on the target.

## remove_user_data  `[user_data]`

Delete a user-data slot by its DescID path (as returned by list_user_data).

## list_mograph_clones  `[mograph]`

Return per-clone transforms from a MoGraph generator.

params:
  handle:    cloner / matrix / whatever feeds GeGetMoData
  max_count: cap on the number of clones returned (default 2048)
  include_matrix: when True (default), include the full 4x3 matrix per clone

## list_tracks  `[animation]`

Enumerate CTracks on the resolved entity.

params:
  handle: target (BaseList2D that supports GetCTracks)

## get_keyframes  `[animation]`

Read keys from a specific CTrack.

params:
  handle:       target
  param_id:     top-level description id
  component:    "x"/"y"/"z"/null
  start_frame:  inclusive lower bound (optional)
  end_frame:    inclusive upper bound (optional)
  fps:          override for BaseTime conversion (default: doc fps)

## delete_keyframe  `[animation]`

Delete keys on a CTrack.

params:
  handle:       target
  param_id:     top-level id
  component:    "x"/"y"/"z"/null
  frame:        single frame to delete (exclusive with start/end)
  start_frame, end_frame: inclusive range to delete
  fps:          override for BaseTime → frame conversion

## delete_track  `[animation]`

Remove an entire CTrack from a target.

params:
  handle:    target
  param_id:  top-level id
  component: "x"/"y"/"z"/null

## list_layers  `[layers]`

_нет докстринга_

## create_layer  `[layers]`

Create (or update-if-exists) a LayerObject.

params:
  name:           string (required)
  color:          [r,g,b] in 0..1 range
  flags:          optional {solo?, view?, render?, manager?, locked?, ...}
  update_if_exists: bool

## assign_to_layer  `[layers]`

Assign an object (or tag/material) to a layer, or clear when layer=null.

params:
  target: handle of object / tag / material
  layer:  layer name, or null to clear

## get_object_layer  `[layers]`

Return the layer currently assigned to the target, or null.

## set_layer_flags  `[layers]`

Toggle visibility / render / lock flags on a layer.

params:
  layer:   layer name (required)
  <flag>:  bool for any of solo/view/render/manager/locked/generators/
           deformers/expressions/animation/xref
  color:   optional [r,g,b] update

## get_document_state  `[document_state]`

_нет докстринга_

## list_xpresso_nodes  `[xpresso]`

Walk an Xpresso tag's GvNodeMaster and return a flat node list.

params:
  handle: tag handle (Texpresso) or object handle (uses the object's
          first Texpresso tag; errors if none exists).

## apply_xpresso_graph  `[xpresso]`

Declarative builder for an Xpresso graph.

params:
  handle:                 tag or object handle for the Xpresso host
  create_tag_if_missing:  bool, default True. When ``handle`` is an
                          object handle and it has no Texpresso tag,
                          create one.
  nodes:   dict[str, {operator_id, name?, parent?, position?, params?,
                      in_ports?, out_ports?}]  — caller-chosen ids
  connect: list[{from: PortRef, to: PortRef}] — PortRefs reference
           caller ids (``{node, dir, index? main_id? name?}``) OR an
           existing node via its path id prefixed with ``"path:"``.

## set_xpresso_port  `[xpresso]`

Low-level port edit: add / remove / connect / disconnect / set_value.

params:
  node:     gv_node handle (or tag handle + id/name)
  action:   "add" | "remove" | "connect" | "disconnect" | "set_value"
  port:     PortRef for the acted-on port (required for remove, connect,
            disconnect, set_value)
  target:   PortRef on the peer node (required for connect)
  io:       "in" | "out" (required for add)
  port_id:  int (required for add — passed to GvNode.AddPort)
  value:    new default value for set_value

## remove_xpresso_node  `[xpresso]`

Delete a GvNode by handle.

params:
  handle: gv_node handle
