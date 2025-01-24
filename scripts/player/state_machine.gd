extends Node

var current_state: State
var states: Dictionary = {}

func _ready():
	for child in get_children():
		if child is State:
			states[child.name.to_lower()] = child
			child.state_machine = self
	
	if states.has("idle"):
		change_state("idle")

func _physics_process(delta):
	if current_state:
		current_state.physics_update(delta)

func _unhandled_input(event):
	if current_state:
		current_state.handle_input(event)

func change_state(state_name: String) -> void:
	if current_state:
		current_state.exit()
	
	if states.has(state_name.to_lower()):
		current_state = states[state_name.to_lower()]
		current_state.enter()
	else:
		push_warning("State " + state_name + " not found") 