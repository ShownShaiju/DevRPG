import math

# --- THE TRANSLATION MAP ---
# This maps your database categories to the 5 radar chart UI categories.
CATEGORY_MAPPING = {
    "Programming Language": "backend",
    "Data & Databases": "backend",
    "Web Framework": "backend",
    
    "Systems & Operations": "cloud",
    "Containerization": "cloud",
    "Container Orchestration": "cloud",
    
    "Version Control": "tools",
    "Collaboration & DevOps": "tools",
    
    # Future-proofing in case you add these to the DB later:
    "Frontend Framework": "frontend",
    "Mobile Development": "mobile",
    "Design": "frontend"
}

def calculate_radar_stats(user_skills):
    """
    Calculates the max level per category and generates SVG pentagon coordinates.
    """
    stats = {
        'frontend': 0, 'backend': 0, 'cloud': 0, 
        'mobile': 0, 'tools': 0
    }
    
    # 1. Aggregate max levels using the Translation Map
    for us in user_skills:
        raw_category = us.skill.category
        
        # Translate the DB category to the Radar category. 
        # If it doesn't exist in the map, default it to 'tools'.
        mapped_category = CATEGORY_MAPPING.get(raw_category, "tools")
        
        if mapped_category in stats:
            stats[mapped_category] = max(stats[mapped_category], us.level)

    # 2. Pentagon Math (5 points, starting at 12 o'clock and moving clockwise)
    angles = [
        -math.pi / 2,                      # Frontend (Top)
        -math.pi / 2 + (2 * math.pi / 5),  # Backend (Top-Right)
        -math.pi / 2 + (4 * math.pi / 5),  # Cloud (Bottom-Right)
        -math.pi / 2 + (6 * math.pi / 5),  # Mobile (Bottom-Left)
        -math.pi / 2 + (8 * math.pi / 5)   # Tools (Top-Left)
    ]
    
    categories = ['frontend', 'backend', 'cloud', 'mobile', 'tools']
    points = []
    
    # 3. Calculate X,Y coordinates
    for i, cat in enumerate(categories):
        # We enforce a minimum display score of 1 so the graph doesn't collapse to a single dot
        display_score = max(1, stats[cat]) 
        radius = (display_score / 10.0) * 40 # Max radius is 40
        x = 50 + radius * math.cos(angles[i])
        y = 50 + radius * math.sin(angles[i])
        points.append(f"{x:.2f},{y:.2f}")

    return {
        'stats': stats,
        'polygon_points': " ".join(points)
    }