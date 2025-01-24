extends Node3D

@onready var animation_player = $AnimationPlayer

func _ready():
	if animation_player:
		# Play the animation when the scene is ready
		animation_player.play("lid_animation")  # Replace "lid_animation" with your actual animation name
	else:
		print("Animation player not found!")
