extends Node

func _ready():
	# Set physics values for the current runtime only
	ProjectSettings.set_setting("physics/3d/default_gravity", 9.8)
	ProjectSettings.set_setting("physics/common/physics_fps", 60)
	ProjectSettings.set_setting("physics/common/physics_ticks_per_second", 60)
	
	# Debug output
	print("Physics settings applied for this session:")
	print("Default gravity: ", ProjectSettings.get_setting("physics/3d/default_gravity"))
	print("Physics FPS: ", ProjectSettings.get_setting("physics/common/physics_fps"))
	print("Physics ticks per second: ", ProjectSettings.get_setting("physics/common/physics_ticks_per_second"))
