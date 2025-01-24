extends Node3D

@onready var base_color: Color = Color(1.0, 1.0, 0.9, 1.0)  # Warm white starlight
@onready var neon_color: Color = Color(0.0, 1.0, 1.0, 1.0)  # Cyan neon
@onready var mesh_instance = get_node(".")  # Gets the current node

var twinkle_speed: float = 2.0
var color_transition_speed: float = 0.5
var brightness: float = 3.0  # Increased brightness
var glow_intensity: float = 2.5  # Controls the glow effect
var fog_density: float = 0.8  # Controls the fog density
var time: float = 0.0

func _ready():
	# Create a new StandardMaterial3D for the stars with enhanced glow
	var material = StandardMaterial3D.new()
	
	# Enable transparency and alpha blending for the fog effect
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	
	# Enable emission for the glow
	material.emission_enabled = true
	material.emission = base_color
	material.emission_energy = brightness
	material.emission_operator = BaseMaterial3D.EMISSION_OP_ADD
	
	# Add rim effect for extra glow
	material.rim_enabled = true
	material.rim = 1.0
	material.rim_tint = 0.8
	
	# Add fog/haze effect using vertex color alpha
	material.vertex_color_use_as_albedo = true
	material.albedo_color = Color(1, 1, 1, fog_density)
	
	# Apply the material to all meshes in the star cluster
	_apply_material_to_children(self, material)
	
	# Set up environment glow if not already configured
	var environment = get_viewport().get_camera_3d().get_environment()
	if environment:
		environment.glow_enabled = true
		environment.glow_intensity = glow_intensity
		environment.glow_bloom = 0.3
		environment.glow_blend_mode = 1  # 1 = Additive, 0 = Screen, 2 = Softlight, 3 = Replace
		environment.glow_hdr_threshold = 0.7

func _process(delta):
	time += delta
	
	# Calculate twinkle and color transition effects with enhanced variation
	var twinkle = (sin(time * twinkle_speed) * 0.5 + 0.5) * brightness
	var color_mix = sin(time * color_transition_speed) * 0.5 + 0.5
	
	# Add subtle variation to fog density
	var fog_variation = sin(time * 0.5) * 0.1 + fog_density
	
	# Interpolate between base and neon colors
	var current_color = base_color.lerp(neon_color, color_mix)
	
	# Update material for all meshes
	_update_materials(self, current_color, twinkle, fog_variation)

func _apply_material_to_children(node: Node, material: Material):
	if node is MeshInstance3D:
		node.material_override = material
	
	for child in node.get_children():
		_apply_material_to_children(child, material)

func _update_materials(node: Node, color: Color, intensity: float, fog: float):
	if node is MeshInstance3D and node.material_override:
		node.material_override.emission = color
		node.material_override.emission_energy = intensity
		node.material_override.albedo_color.a = fog
	
	for child in node.get_children():
		_update_materials(child, color, intensity, fog)
