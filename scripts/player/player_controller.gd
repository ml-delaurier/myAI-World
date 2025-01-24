extends CharacterBody3D

@onready var camera_mount = $CameraMount
@onready var camera = $CameraMount/Camera3D
@onready var state_machine = $StateMachine

const MOUSE_SENSITIVITY = 0.002
const SPEED_WALK = 3.0
const SPEED_SPRINT = 5.0
const JUMP_VELOCITY = 4.0
const MAX_RADIUS = 7.5  # Slightly less than floor radius for safety
const FALL_RESET_Y = -10.0  # Y position at which to reset player

var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")
var was_on_floor = false
var initial_position = Vector3(0, 1, 0)  # Store initial spawn position

func _ready():
	# Store initial position for reset
	initial_position = global_position
	
	# Set up collision and physics properties
	collision_layer = 0  # Player doesn't need a collision layer
	collision_mask = 3   # Player collides with both wall (layer 1) and floor (layer 2)
	floor_max_angle = 0.785398  # 45 degrees
	floor_snap_length = 0.2     # Increased snap distance for better floor detection
	up_direction = Vector3.UP   # Ensure we're using the correct up direction
	floor_stop_on_slope = true  # Stop the player from sliding down slopes
	floor_block_on_wall = true  # Prevent sliding up walls
	floor_constant_speed = true # Maintain constant speed on slopes
	
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event):
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
		camera_mount.rotate_x(-event.relative.y * MOUSE_SENSITIVITY)
		camera_mount.rotation.x = clamp(camera_mount.rotation.x, -PI/2, PI/2)

	if event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED

func enforce_boundary():
	var distance_from_center = Vector2(global_position.x, global_position.z).length()
	if distance_from_center > MAX_RADIUS:
		# Calculate normalized direction from center to player
		var dir_from_center = Vector2(global_position.x, global_position.z).normalized()
		# Move position back to boundary
		global_position.x = dir_from_center.x * MAX_RADIUS
		global_position.z = dir_from_center.y * MAX_RADIUS
		# Stop horizontal movement
		velocity.x = 0
		velocity.z = 0
		return true
	return false

func check_fall_reset():
	if global_position.y < FALL_RESET_Y:
		global_position = initial_position
		velocity = Vector3.ZERO
		return true
	return false

func _physics_process(delta):
	# Check for falling
	if check_fall_reset():
		return
		
	# Apply gravity when in air
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		# Reset vertical velocity when on floor
		velocity.y = 0
		
	# Handle movement input
	var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	var speed = SPEED_SPRINT if Input.is_action_pressed("sprint") else SPEED_WALK
	
	if direction:
		velocity.x = direction.x * speed
		velocity.z = direction.z * speed
	else:
		velocity.x = move_toward(velocity.x, 0, speed)
		velocity.z = move_toward(velocity.z, 0, speed)
	
	# Move the player
	move_and_slide()
	
	# Check and enforce boundary after movement
	if enforce_boundary():
		# If we hit the boundary, do one more move_and_slide to ensure proper collision resolution
		move_and_slide()
	
	# Debug floor state changes
	if is_on_floor() != was_on_floor:
		if is_on_floor():
			print("Landed on floor at position: ", global_position)
		else:
			print("Left floor at position: ", global_position)
		was_on_floor = is_on_floor()
