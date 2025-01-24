extends Node

# Utility functions for the ML World game

static func format_timestamp() -> String:
	var datetime = Time.get_datetime_dict_from_system()
	return "%04d-%02d-%02d_%02d-%02d-%02d" % [
		datetime["year"],
		datetime["month"],
		datetime["day"],
		datetime["hour"],
		datetime["minute"],
		datetime["second"]
	]

func save_screenshot(path: String) -> void:
	var image = get_viewport().get_texture().get_image()
	var timestamp = format_timestamp()
	var filename = "screenshot_%s.png" % timestamp
	image.save_png(path.path_join(filename))
	
	# Save metadata
	var metadata = {
		"timestamp": timestamp,
		"filename": filename,
		"resolution": {
			"width": image.get_width(),
			"height": image.get_height()
		}
	}
	var metadata_file = FileAccess.open(path.path_join("screenshot_metadata.json"), FileAccess.WRITE)
	metadata_file.store_string(JSON.stringify(metadata, "\t"))
	metadata_file.close()
