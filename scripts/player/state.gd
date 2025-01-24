extends Node
class_name State

var state_machine = null

# Virtual function to be overridden by child states
func enter() -> void:
	pass

# Virtual function to be overridden by child states
func exit() -> void:
	pass

# Virtual function to be overridden by child states
func handle_input(_event: InputEvent) -> void:
	pass

# Virtual function to be overridden by child states
func physics_update(_delta: float) -> void:
	pass 