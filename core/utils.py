# Create this new file: core/utils.py
import math

def calculate_radar_stats(user_skills):
    """
    Calculates the max level per category and generates SVG pentagon coordinates.
    """
    stats = {
        'frontend': 0, 'backend': 0, 'cloud': 0, 
        'mobile': 0, 'tools': 0
    }
    
    # 1. Aggregate max levels
    for us in user_skills:
        cat = us.skill.category
        if cat in stats:
            stats[cat] = max(stats[cat], us.level)

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
        display_score = max(1, stats[cat]) 
        radius = (display_score / 10.0) * 40 # Max radius is 40
        x = 50 + radius * math.cos(angles[i])
        y = 50 + radius * math.sin(angles[i])
        points.append(f"{x:.2f},{y:.2f}")

    return {
        'stats': stats,
        'polygon_points': " ".join(points)
    }