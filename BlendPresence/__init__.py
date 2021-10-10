import bpy, os, time, math
from .pypresence import Presence
from .pypresence import exceptions

bl_info = {
    "name": "BlendPresence",
    "description": "Discord Rich Presence for Blender 2.9x",
    "author": "Abrasic",
    "version": (1, 5, 2),
    "blender": (2, 90, 1),
    "category": "System",
}

def connectRPC():
    try:
        rpcClient.connect()
        print("[BP] Connected!")
        return True
    except ConnectionRefusedError:
        print("[BP] Unable to connect: ConnectionRefusedError")
        return False
    except (FileNotFoundError, AttributeError, exceptions.InvalidPipe, AssertionError):
        print("[BP] Unable to connect: Discord client not detected")
        return False
        
# RPC
rpcClient = Presence("766373631424200705")

# VARS
class bpi:
    startTime = None
    connected = False
    isRendering = False
    renderedFrames = 0
    timer = 5

# HANDLERS
@bpy.app.handlers.persistent
def startRenderJobHandler(*args):
    bpi.isRendering = True
    
    if bpy.context.preferences.addons[__name__].preferences.resetTimer:
        bpi.startTime = time.time()

@bpy.app.handlers.persistent
def endRenderJobHandler(*args):
    bpi.isRendering = False
    bpi.renderedFrames = 0
    
    if bpy.context.preferences.addons[__name__].preferences.resetTimer:
        bpi.startTime = time.time()

@bpy.app.handlers.persistent
def postRenderHandler(*args):
    bpi.renderedFrames += 1
    
# FUNCTIONS
def updatePresenceTimer():
    updatePresence()
    return bpi.timer
    
def evalCustomText(str):
    if len(str) > 1:
        return str
    else:
        return "  " 
        # Details cannot be empty or less than 2 chars but for some reason this works too

def getObjectCount():
    return f"{len(bpy.context.selectable_objects):,d} total objects"
    
def getPolyCount():
    count = 0
    for e in bpy.context.scene.objects:
        if e.type == "MESH":
            count += len(e.data.polygons)
    return f"{count:,d} total polys"

def getBoneCount():
    count = 0
    for e in bpy.context.scene.objects:
        if e.type == "ARMATURE":
            count += len(e.data.bones)
    return f"Working with {count:,d} bones"
    
def getMatCount():
    return f"{len(bpy.data.materials):,d} total materials"
    
def getFramesAnimated():
    if bpy.data.actions:
        ac = [action.frame_range for action in bpy.data.actions]
        k = (sorted(set([item for sublist in ac for item in sublist])))
        print(k)
        return f"{math.floor(k[-1]):,d} frames animated"
    else:
        return "  "
        
def getCurrentFrame():
    i = "Viewing frame"
    if bpy.context.screen.is_animation_playing:
       i = "Playing animation |"
       
    return f"{i} {bpy.context.scene.frame_current:,d}"   

def getFileName():
    name = bpy.path.display_name_from_filepath(bpy.data.filepath)
    if name == "":
        return None
    else:
        return name

def readsize(b):
    for u in [' bytes', ' KB', ' MB', ' GB', ' TB']:
        if b < 1024.0 or u == ' PB':
            break
        b /= 1024.0
    return f"{b:.2f} {u}"
    
def getFileSize():
    p = bpy.data.filepath
    if p:
        return readsize(os.path.getsize(p))
    else:
        return None
    
def getVersionStr():
    ver = bpy.app.version
    verC = bpy.app.version_char
    return f"{ver[0]}.{ver[1]}.{ver[2]}{verC}"

def getRenderEngineStr():
    i = bpy.context.engine
    unique = [ # Engines with unique names
        ["PRMAN_RENDER", "Renderman"],
        ["LUXCORE", "LuxCore"]
    ]

    for e in unique:
        if e[0] == i:
            return e[1]

    # If this function hasn't returned yet, use this generic string:
    iformat = i.replace("BLENDER_", "").replace("_", " ")
    return iformat.title()

def getFrameRange():
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    cursor = bpy.context.scene.frame_current
    return (cursor - start + 1, end - start + 1)
    
def getActiveObject():
    if bpy.context.active_object:
        return bpy.context.active_object.name
    else:
        return "  "

######## PRESENCE ########
def updatePresence():
    stateText = None
    detailsText = None
    smallIcon = None
    smallIconText = None
    largeIcon = 'blenderlogo'
    
    # Addon Preferences
    prefs = bpy.context.preferences.addons[__name__].preferences
    
    if prefs.generalEnable:
        bpi.timer = prefs.generalUpdate
        
        # LARGE ICON
        if prefs.displayVersion:
            if prefs.displayEngine:

                engines = ['Redshift', 'Renderman', 'LuxCore']
                current_engine = getRenderEngineStr()
                for e in engines:
                    if e == current_engine:
                        largeIcon = "blender_"+e.lower()
                        break

                largeIconText = getRenderEngineStr() + " Engine in " + getVersionStr()
            else:
                largeIconText = getVersionStr()
        else:
            if prefs.displayEngine:
                largeIconText = getRenderEngineStr()
            else:
                largeIconText = None

        # SMALL ICON
        if prefs.displayMode and bpy.context.mode:
        
            modes = {
                "OBJECT": ["Object Mode", "object"],
                "EDIT_": ["Edit Mode", "edit"],
                "POSE": ["Pose Mode", "pose"],
                "SCULPT": ["Sculpt Mode", "sculpt"],
                "PAINT_GPENCIL": ["Draw Mode", "paint_gpencil"],
                "PAINT_TEXTURE": ["Texture Paint Mode", "texture_paint"],
                "PAINT_VERTEX": ["Vertex Paint Mode", "vertex_paint"],
                "PAINT_WEIGHT": ["Weight Paint Mode", "weight_paint"],
                "PARTICLE": ["Particle Edit Mode", "particle_edit"],
            }
            
            activeMode = bpy.context.mode
            
            for i in modes:
                if i in activeMode:
                    smallIconText = modes[i][0]
                    smallIcon = modes[i][1]
                
        # DETAILS AND STATE
        if bpi.isRendering:
            smallIcon = "render"
            if prefs.displayRenderStats:
                smallIconText = f"Rendering... {bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}"
            else:
                smallIconText = None
                
            # Rendering Details
            if prefs.enableDetails:
                if prefs.detailsType == "literal":
                    if prefs.displayFileName and getFileName():
                        detailsText = f"Rendering {getFileName()}.blend"
                    else:
                        detailsText = f"Rendering a project"
                else:
                    detailsText = str(prefs.detailsCustomText)
                
            # Rendering State
            if bpi.renderedFrames > 0:
                frameRange = getFrameRange()
                if prefs.displayRenderStats:
                    smallIconText = f"Rendering... {bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}@{bpy.context.scene.render.fps}fps"
                else:
                    smallIconText = None
                if prefs.displayFrames:
                    percent=(frameRange[0]/frameRange[1])*100
                    stateText = f"Frame {frameRange[0]} of {frameRange[1]} ({'{:.2f}%'.format(percent)})"
            else:
                if prefs.enableState and prefs.displayFrames:
                    stateText = f"Frame {bpy.context.scene.frame_current}"
        else: # NOT RENDERING
            if prefs.enableDetails:
                if prefs.detailsType == "literal":
                    if prefs.displayFileName and getFileName():
                        detailsText = f"{getFileName()}.blend"
                    else:
                        detailsText = "Working on a project"
                else:
                    detailsText = evalCustomText(prefs.detailsCustomText)
            else:
                detailsText = "  "
            
            # Viewport State      
            displayTypes = {
                "custom" : evalCustomText,
                "obj" : getObjectCount,
                "poly" : getPolyCount,
                "bone" : getBoneCount,
                "mat" : getMatCount,
                "frame" : getCurrentFrame,
                "anim" : getFramesAnimated,
                "size" : getFileSize,
                "active" : getActiveObject,
            }
        
        if not bpi.isRendering: # Render state will always override this
            try:
                if prefs.stateType == "custom":
                    stateText = evalCustomText(prefs.stateCustomText)
                else:
                    stateText = displayTypes[prefs.stateType]()
            except KeyError as e:
                print("[BP] ERROR: " + e)

        # Time Elapsed
        if prefs.enableTime and not bpi.isRendering:
            fStartTime = bpi.startTime
        elif prefs.enableTime and bpi.isRendering:
            fStartTime = bpi.startTime
        else:
            fStartTime = None

        # Push to RPC
        if bpi.connected:
            try:
                rpcClient.update(
                    start=fStartTime,
                    state=stateText,
                    details=detailsText,
                    small_image=smallIcon,
                    small_text=smallIconText,
                    large_image=largeIcon,
                    large_text=largeIconText,
                )
            except exceptions.InvalidID or AssertionError:
                bpi.connected = False
                print("[BP] I lost connection to Discord RPC! Re-connecting...")
                bpi.connected = connectRPC()
        else:
            print("[BP] Retrying...")
            bpi.connected = connectRPC()
    else:
        rpcClient.clear()
        bpi.connected = False

# PREFERENCES
class blendPresence(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    # GENERAL SETTINGS
    generalEnable: bpy.props.BoolProperty(
        name = "Enabled",
        description = "Enable Discord Rich Presence",
        default = True,
    )
    
    generalUpdate: bpy.props.IntProperty(
        name = "Update Every",
        description = "How long the presence will update in seconds. Faster update rates may affect performance.",
        default = 5,
        min = 1,
        max = 60
    )
    
    # LARGE ICON TOOLTIP
    displayEngine: bpy.props.BoolProperty(
        name = "Render Engine",
        description = "Displays the active render engine logo (if supported) on the large icon, as well as in the large icon text",
        default = True,
    )

    displayVersion: bpy.props.BoolProperty(
        name = "Blender Version",
        description = "Displays the version of Blender software",
        default = True,
    )
    
    # SMALL ICON TOOLTIP
    displayMode: bpy.props.BoolProperty(
        name = "Active Mode",
        description = "Displays the current mode (Object, Edit, Pose, etc.) from the 3D Viewport",
        default = True,
    )
    
    displayRenderStats: bpy.props.BoolProperty(
        name = "Render Stats",
        description = "Displays render information such as camera resolution and FPS where applicable",
        default = True,
    )
    
    # DETAILS
    enableDetails: bpy.props.BoolProperty(
        name = "Enabled",
        description = "Enables 'details' property. This is the top-most piece of text shown in the presence",
        default = True,
    )
    
    detailsType: bpy.props.EnumProperty(
        name = "Display",
        items = (
            ("literal", "Literal", "Changes depending on what you're doing (ex. while rendering it will display 'Rendering a project'"),
            ("custom", "Custom", "A string that will display in the 'details' property. Two characters or longer"),
        ),
        default = "literal",
    )
    
    displayFileName: bpy.props.BoolProperty(
        name = "Display File Name",
        description = "Replace literal string to your .blend file name (ex. 'project.blend'). Your project must be saved to a file in order for this to work.",
        default = False,
    )
    
    detailsCustomText: bpy.props.StringProperty(
        name = "Custom",
        description = "Your custom text goes here. Two characters or longer",
        default = "",
    )
    
    displayFrames: bpy.props.BoolProperty(
        name = "Frame Range",
        description = "Displays range of currently rendering frames (ex. 'Frame 1 of 100')",
        default = True,
    )
    
    # STATE
    enableState: bpy.props.BoolProperty(
        name = "Enabled",
        description = "Enables 'state' property. This is the middle piece of text shown in the presence",
        default = True,
    )
    
    stateType: bpy.props.EnumProperty(
        name = "Display",
        items = (
            ("anim", "Frames Animated", "Displays the frame number that holds the last keyframe from all given actions."),
            ("poly", "Polygon Count", "Display the total amount of objects in the current scene"),
            ("bone", "Bone Count", "Display the total amount of armature bones in the current scene"),
            ("mat", "Material Count", "Display the total amount of materials in the current scene"),
            ("obj", "Object Count", "Display the total amount of objects in the current scene"),
            ("active", "Active Object", "Display the name of the curent active object selected. If none is seleced then this will return nothing."),
            ("frame", "Current Frame", "Display the current frame being viewed in the timeline. The text will also change if you are playing back an animation."),
            ("size", "File Size", "Displays the file size of your current project file. If your project is not saved, nothing will display."),
            ("custom", "Custom", "A string that will display in the 'details' property. Two characters or longer"),
        ),
        default = "custom",
    )

    stateCustomText: bpy.props.StringProperty(
        name = "Custom",
        description = "Your custom text goes here. Two characters or longer",
        default = "",
    )

    stateDisplayObjects: bpy.props.BoolProperty(
        name = "Object Count",
        description = "Displays the number of all objects in the scene",
        default = False,
    )
    
    # TIME ELAPSED
    enableTime: bpy.props.BoolProperty(
        name = "Enabled",
        description = "Displays the total amount of time elapsed since the plugin was enabled",
        default = True,
    )
    
    resetTimer: bpy.props.BoolProperty(
        name = "Reset On Render",
        description = "While enabled, the elapsed time will reset when a render begins",
        default = True,
    )

    # INTERFACE
    def draw(self, context):
        prefs = bpy.context.preferences.addons[__name__].preferences

        layoutTop = self.layout.row()
        layout = self.layout.row()
        colLeft = layout.column()
        colRight = layout.column()
        
        # Core
        layoutTop.prop(self, "generalEnable")
        
        if prefs.generalEnable:
            layoutTop.prop(self, "generalUpdate")
            
            # Large Icon Tooltip
            boxLrg = colLeft.box()
            boxLrg.label(text="Large Icon Tooltip", icon="BLENDER")
            boxLrg.prop(self, "displayEngine")
            boxLrg.prop(self, "displayVersion")

            # Small Icon Tooltip
            boxSml = boxLrg.box()
            boxSml.label(text="Small Icon", icon="PROP_CON")
            boxSmlView = boxSml.row().box()
            boxSmlView.label(text="Viewport", icon="VIEW3D")
            boxSmlView.prop(self, "displayMode")
            boxSmlRender = boxSml.row().box()
            boxSmlRender.label(text="Rendering", icon="RENDER_STILL")
            boxSmlRender.prop(self, "displayRenderStats")
            
            # Details Text (Top)
            boxDts = colRight.box()
            boxDts.label(text="Details", icon="ALIGN_TOP")
            boxDts.prop(self, "enableDetails")
            if prefs.enableDetails:
                boxDtsSettings = boxDts.row().box()
                boxDtsSettings.prop(self, "detailsType")
                if prefs.detailsType == "custom":
                    boxDtsSettings.prop(self, "detailsCustomText")
                if prefs.detailsType == "literal":
                    boxDtsSettings.prop(self, "displayFileName")
            
            # State Text (Middle)
            boxSt = colRight.box()
            boxSt.label(text="State", icon="ALIGN_MIDDLE")
            boxSt.prop(self, "enableState")
            
            if prefs.enableState:
                boxStViewSettings = boxSt.row().box()
                boxStViewSettings.label(text="Viewport", icon="VIEW3D")
                boxStViewSettings.prop(self, "stateType")
                
                if prefs.stateType == "custom":
                    boxStViewSettings.prop(self, "stateCustomText")

                boxStViewSettings = boxSt.row().box()
                boxStViewSettings.label(text="Rendering", icon="RENDER_STILL")
                boxStViewSettings.prop(self, "displayFrames")

            # Time Elapsed (Bottom)
            boxTm = colRight.box()
            boxTm.label(text="Time Elapsed", icon="ALIGN_BOTTOM")
            boxTm.prop(self, "enableTime")

            if prefs.enableTime:
                boxTmSettings = boxTm.column()
                boxTmSettings.prop(self, "resetTimer")

# REGISTRATION     
def register():
    bpy.utils.register_class(blendPresence)
    bpi.startTime = time.time()
    bpi.connected = connectRPC()
    bpy.app.timers.register(updatePresenceTimer, first_interval=1.0, persistent=True)
    
    bpy.app.handlers.render_init.append(startRenderJobHandler)
    bpy.app.handlers.render_complete.append(endRenderJobHandler)
    bpy.app.handlers.render_cancel.append(endRenderJobHandler)
    bpy.app.handlers.render_post.append(postRenderHandler)

def unregister():
    bpi.startTime = time.time()
    rpcClient.close()
    bpy.app.timers.unregister(updatePresenceTimer)
    bpy.utils.unregister_class(blendPresence)
    
    bpy.app.handlers.render_init.remove(startRenderJobHandler)
    bpy.app.handlers.render_complete.remove(endRenderJobHandler)
    bpy.app.handlers.render_cancel.remove(endRenderJobHandler)
    bpy.app.handlers.render_post.remove(postRenderHandler)
