extends Node

signal screen_activated(screen_name: String)
signal screen_deactivated(screen_name: String)

var active_screens: Dictionary = {}
var screen_instances: Dictionary = {}

# Screen types and their corresponding scene paths
const SCREEN_TYPES = {}

func _ready() -> void:
    # Initialize screens (they start as inactive)
    for screen_type in SCREEN_TYPES:
        active_screens[screen_type] = false

func activate_screen(screen_type: String) -> void:
    if not SCREEN_TYPES.has(screen_type):
        push_error("Invalid screen type: " + screen_type)
        return
    
    if not screen_instances.has(screen_type):
        var screen_scene = load(SCREEN_TYPES[screen_type])
        if screen_scene:
            var screen_instance = screen_scene.instantiate()
            add_child(screen_instance)
            screen_instances[screen_type] = screen_instance
    
    if screen_instances.has(screen_type):
        var screen = screen_instances[screen_type]
        screen.visible = true
        active_screens[screen_type] = true
        emit_signal("screen_activated", screen_type)

func deactivate_screen(screen_type: String) -> void:
    if screen_instances.has(screen_type):
        var screen = screen_instances[screen_type]
        screen.visible = false
        active_screens[screen_type] = false
        emit_signal("screen_deactivated", screen_type)

func is_screen_active(screen_type: String) -> bool:
    return active_screens.get(screen_type, false)

func get_active_screens() -> Array:
    var active = []
    for screen in active_screens:
        if active_screens[screen]:
            active.append(screen)
    return active
