import math
import heapq

# Kích thước mỗi ô lưới: 0.002 độ (tương đương khoảng ~220m)
GRID_SIZE = 0.002

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Tính khoảng cách đường chim bay giữa hai tọa độ.
    Sử dụng làm Heuristic h(n) và chi phí di chuyển g(n) giữa các ô lưới.
    """
    R = 6371.0  # Bán kính trái đất (km)
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_grid_coords(lat, lon):
    """Chuyển đổi tọa độ địa lý sang tọa độ lưới (x, y)"""
    return (int(lat / GRID_SIZE), int(lon / GRID_SIZE))

class Node:
    """Đại diện cho một ô lưới trong đồ thị A*"""
    def __init__(self, x, y, g, h, parent=None):
        self.x = x
        self.y = y
        self.g = g          # Chi phí từ điểm bắt đầu đến node này
        self.h = h          # Heuristic: Ước lượng chi phí từ node này đến đích
        self.f = g + h      # Tổng chi phí (f = g + h)
        self.parent = parent
        
    def __lt__(self, other):
        if self.f == other.f:
            return self.g < other.g
        return self.f < other.f

def astar_grid_distance(start_lat, start_lon, end_lat, end_lon):
    """
    Thuật toán A* tìm đường đi ngắn nhất trên lưới ô vuông.
    
    Trả về: (khoảng_cách_lưới_km, số_ô_lưới_đã_duyệt)
    """
    start_x, start_y = get_grid_coords(start_lat, start_lon)
    end_x, end_y = get_grid_coords(end_lat, end_lon)
    
    # Nếu trạm và nạn nhân nằm trong cùng 1 ô lưới
    if start_x == end_x and start_y == end_y:
        return haversine_km(start_lat, start_lon, end_lat, end_lon), 1
        
    open_heap = []
    closed_set = set()
    
    # Tọa độ trung tâm của ô lưới xuất phát và đích
    start_center_lat = (start_x + 0.5) * GRID_SIZE
    start_center_lon = (start_y + 0.5) * GRID_SIZE
    end_center_lat = (end_x + 0.5) * GRID_SIZE
    end_center_lon = (end_y + 0.5) * GRID_SIZE
    
    h_start = haversine_km(start_center_lat, start_center_lon, end_center_lat, end_center_lon)
    start_node = Node(start_x, start_y, 0, h_start)
    
    heapq.heappush(open_heap, start_node)
    
    # Lưu g(n) tốt nhất hiện tại cho mỗi ô lưới
    g_scores = {(start_x, start_y): 0}
    
    # 8 hướng di chuyển: Bắc, Nam, Đông, Tây, và 4 đường chéo
    directions = [
        (0, 1), (1, 0), (0, -1), (-1, 0),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    
    MAX_ITER = 50000  # Chặn loop vô hạn
    iterations = 0
    
    while open_heap and iterations < MAX_ITER:
        iterations += 1
        current = heapq.heappop(open_heap)
        
        # Bỏ qua nếu đã nằm trong Closed Set
        if (current.x, current.y) in closed_set:
            continue
            
        closed_set.add((current.x, current.y))
        
        # Đã đến được ô lưới đích
        if current.x == end_x and current.y == end_y:
            return current.g, iterations
            
        # Mở rộng các hướng xung quanh
        for dx, dy in directions:
            nx, ny = current.x + dx, current.y + dy
            if (nx, ny) in closed_set:
                continue
                
            curr_lat = (current.x + 0.5) * GRID_SIZE
            curr_lon = (current.y + 0.5) * GRID_SIZE
            next_lat = (nx + 0.5) * GRID_SIZE
            next_lon = (ny + 0.5) * GRID_SIZE
            
            # g(n): chi phí đi từ điểm hiện tại sang ô kề cạnh
            step_cost = haversine_km(curr_lat, curr_lon, next_lat, next_lon)
            tentative_g = current.g + step_cost
            
            # Nếu tìm được đường đi tốt hơn đến ô (nx, ny)
            if (nx, ny) not in g_scores or tentative_g < g_scores[(nx, ny)]:
                g_scores[(nx, ny)] = tentative_g
                h = haversine_km(next_lat, next_lon, end_center_lat, end_center_lon)
                neighbor = Node(nx, ny, tentative_g, h, current)
                heapq.heappush(open_heap, neighbor)
                
    # Fallback nếu thuật toán không tìm được đường (VD: quá giới hạn lặp)
    fallback_dist = haversine_km(start_lat, start_lon, end_lat, end_lon)
    return fallback_dist, iterations
