extends Node

var log_file: FileAccess
const LOG_FILE_PATH = "res://log/ml-world.log"

func _ready() -> void:
    # Create log directory if it doesn't exist
    var dir = DirAccess.open("res://")
    if dir:
        dir.make_dir_recursive("log")
    # Open log file in write mode
    log_file = FileAccess.open(LOG_FILE_PATH, FileAccess.WRITE)
    if log_file:
        log_info("Global Logger Initialized")
        # Log engine version and initialization
        log_info("Godot Engine v%s.%s.%s" % [
            Engine.get_version_info()["major"],
            Engine.get_version_info()["minor"],
            Engine.get_version_info()["patch"]
        ])

func log_info(message: String) -> void:
    var formatted_message = "[%s][INFO] %s" % [Time.get_datetime_string_from_system(), message]
    print(formatted_message)  # Also print to console
    if log_file:
        log_file.store_string(formatted_message + "\n")
        log_file.flush()  # Ensure it's written immediately

func log_error(message: String) -> void:
    var formatted_message = "[%s][ERROR] %s" % [Time.get_datetime_string_from_system(), message]
    printerr(formatted_message)  # Print to console as error
    if log_file:
        log_file.store_string(formatted_message + "\n")
        log_file.flush()

func log_debug(message: String) -> void:
    var formatted_message = "[%s][DEBUG] %s" % [Time.get_datetime_string_from_system(), message]
    print(formatted_message)
    if log_file:
        log_file.store_string(formatted_message + "\n")
        log_file.flush()

func _notification(what: int) -> void:
    if what == NOTIFICATION_PREDELETE:
        # Log any missing audio files
        var audio_files = [
            "res://assets/audio/ui/key_press.wav",
            "res://assets/audio/ui/command_complete.wav",
            "res://assets/audio/ui/error_beep.wav",
            "res://assets/audio/ui/boot_sequence.wav",
            "res://assets/audio/ui/success_chime.wav"
        ]
        for file in audio_files:
            if not FileAccess.file_exists(file):
                log_error("Resource file not found: %s (expected type: AudioStream)" % file)

func _exit_tree() -> void:
    if log_file:
        log_file.close()
