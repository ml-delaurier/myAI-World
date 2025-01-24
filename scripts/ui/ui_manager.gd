extends Node

# Preload UI scenes
var logging_terminal_ui = preload("res://scenes/ui/logging_terminal_ui.tscn")
var huggingface_terminal_ui = preload("res://scenes/ui/huggingface_terminal_ui.tscn")

var current_ui = null
var is_transitioning := false

func show_terminal_ui(terminal_type: String) -> void:
	if is_transitioning:
		return
		
	if current_ui:
		hide_terminal_ui()
		await get_tree().create_timer(0.3).timeout
	
	var ui_instance = null
	match terminal_type:
		"logging":
			ui_instance = logging_terminal_ui.instantiate()
		"huggingface":
			ui_instance = huggingface_terminal_ui.instantiate()
		_:
			push_error("Unknown terminal type: " + terminal_type)
			return
	
	get_tree().root.add_child(ui_instance)
	current_ui = ui_instance
	ui_instance.show_terminal()

func hide_terminal_ui() -> void:
	if not current_ui or is_transitioning:
		return
		
	is_transitioning = true
	await current_ui.hide_terminal()
	current_ui.queue_free()
	current_ui = null
	is_transitioning = false

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if current_ui:
			current_ui.queue_free()
		get_tree().quit()
