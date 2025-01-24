extends State

func physics_update(delta: float) -> void:
	var player = get_parent().get_parent()
	
	# Get input direction
	var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	if input_dir == Vector2.ZERO:
		state_machine.change_state("idle")
		return
	
	# Check if sprint key is released
	if not Input.is_action_pressed("sprint"):
		state_machine.change_state("walk")
		return
	
	# Check for jump input
	if Input.is_action_just_pressed("jump") and player.is_on_floor():
		state_machine.change_state("jump")
		return
	
	# Apply movement at sprint speed
	var direction = (player.transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	player.velocity.x = direction.x * player.SPEED_SPRINT
	player.velocity.z = direction.z * player.SPEED_SPRINT
	
	# Apply gravity
	if not player.is_on_floor():
		player.velocity.y -= player.gravity * delta 