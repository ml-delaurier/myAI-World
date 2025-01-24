extends State

func enter() -> void:
	var player = get_parent().get_parent()
	player.velocity.y = player.JUMP_VELOCITY

func physics_update(delta: float) -> void:
	var player = get_parent().get_parent()
	
	# Get input direction for air control
	var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var direction = (player.transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	# Apply air movement (slightly reduced control)
	var speed = player.SPEED_SPRINT if Input.is_action_pressed("sprint") else player.SPEED_WALK
	speed *= 0.8  # Reduce air control
	
	if direction:
		player.velocity.x = direction.x * speed
		player.velocity.z = direction.z * speed
	
	# Apply gravity
	player.velocity.y -= player.gravity * delta
	
	# Check for landing
	if player.is_on_floor():
		if input_dir == Vector2.ZERO:
			state_machine.change_state("idle")
		elif Input.is_action_pressed("sprint"):
			state_machine.change_state("sprint")
		else:
			state_machine.change_state("walk") 