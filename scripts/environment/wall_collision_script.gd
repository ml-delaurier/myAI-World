extends CollisionShape3D

func _ready():
	# Get the mesh from the MeshInstance3D sibling node
	var mesh_instance = get_parent().get_node("WallMesh")
	if not mesh_instance:
		push_error("WallMesh node not found")
		return
		
	var cylinder_mesh = mesh_instance.mesh
	if not cylinder_mesh:
		push_error("No mesh found in WallMesh")
		return
	
	# Get the mesh surface arrays
	var arrays = cylinder_mesh.get_mesh_arrays()
	var vertices = arrays[Mesh.ARRAY_VERTEX]
	var indices = arrays[Mesh.ARRAY_INDEX]
	
	# Create triangles for the side walls only (exclude top and bottom faces)
	var wall_triangles = PackedVector3Array()
	
	# Process only the side wall triangles
	for i in range(0, indices.size(), 3):
		var v1 = vertices[indices[i]]
		var v2 = vertices[indices[i + 1]]
		var v3 = vertices[indices[i + 2]]
		
		# Check if this triangle is part of the side wall (not top or bottom)
		# We do this by checking if the triangle has a significant height difference
		var height_diff = max(abs(v1.y - v2.y), max(abs(v2.y - v3.y), abs(v3.y - v1.y)))
		if height_diff > cylinder_mesh.height * 0.1:  # If height difference is significant
			wall_triangles.push_back(v1)
			wall_triangles.push_back(v2)
			wall_triangles.push_back(v3)
	
	# Set the collision shape data
	var concave_shape = shape as ConcavePolygonShape3D
	if concave_shape:
		concave_shape.data = wall_triangles
	else:
		push_error("Shape is not a ConcavePolygonShape3D")
