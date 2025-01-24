extends State

func enter() -> void:
	# Reset velocity when entering idle state
	var player = get_parent().get_parent()
	player.velocity.x = 0
	player.velocity.z = 0

func physics_update(_delta: float) -> void:
	var player = get_parent().get_parent()
	
	# Check for movement input
	var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	if input_dir != Vector2.ZERO:
		state_machine.change_state("walk")
	
	# Check for jump input
	if Input.is_action_just_pressed("jump") and player.is_on_floor():
		state_machine.change_state("jump") 