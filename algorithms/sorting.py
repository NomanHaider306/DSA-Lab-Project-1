

import time
import math
from typing import List, Dict, Any, Tuple, Optional
from models.filter_sort import SortResult


class MetricsTracker:
    
    __slots__ = ("comparisons", "swaps", "movements")

    def __init__(self):
        self.comparisons = 0
        self.swaps = 0
        self.movements = 0

    def reset(self):
        self.comparisons = 0
        self.swaps = 0
        self.movements = 0




def get_sort_key_value(record: Dict[str, Any], column: str) -> Any:
    
    val = record.get(column)
    if val is None or val == "":
        return None

    
    if column in ("rating", "price"):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    elif column in ("game_id", "rating_count", "metacritic_score"):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None
    elif column == "multiplayer":
        if isinstance(val, bool):
            return 1 if val else 0
        s = str(val).lower()
        if s in ("1", "true", "yes"):
            return 1
        elif s in ("0", "false", "no"):
            return 0
        return None
    elif column == "release_date":
        return str(val).strip()
    else:
        
        return str(val).casefold()


def compare_keys(val_a: Any, val_b: Any, reverse: bool, tracker: MetricsTracker) -> int:
    
    tracker.comparisons += 1

    if val_a is None and val_b is None:
        return 0
    if val_a is None:
        # None goes to the end
        return 1
    if val_b is None:
        return -1

    if val_a == val_b:
        return 0

    if not reverse:
        return -1 if val_a < val_b else 1
    else:
        return -1 if val_a > val_b else 1


def is_smaller_or_equal(val_a: Any, val_b: Any, reverse: bool, tracker: MetricsTracker) -> bool:
    
    return compare_keys(val_a, val_b, reverse, tracker) <= 0


def is_strictly_smaller(val_a: Any, val_b: Any, reverse: bool, tracker: MetricsTracker) -> bool:
   
    return compare_keys(val_a, val_b, reverse, tracker) < 0




def insertion_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
   
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    for i in range(1, n):
        key_item = arr[i]
        key_val = get_sort_key_value(key_item, column)
        j = i - 1

        
        while j >= 0:
            val_j = get_sort_key_value(arr[j], column)
            if is_strictly_smaller(key_val, val_j, reverse, tracker):
                arr[j + 1] = arr[j]
                tracker.movements += 1
                j -= 1
            else:
                break
        
        arr[j + 1] = key_item
        tracker.movements += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Insertion Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,
        swaps=tracker.swaps,
        movements=tracker.movements,
        stability="Stable",
        time_complexity_best="O(n)",
        time_complexity_avg="O(n²)",
        time_complexity_worst="O(n²)",
        space_complexity="O(1)",
        sorted_data=arr,
        is_compatible=True
    )




def selection_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
    
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    for i in range(n - 1):
        target_idx = i
        target_val = get_sort_key_value(arr[target_idx], column)

        for j in range(i + 1, n):
            val_j = get_sort_key_value(arr[j], column)
            if is_strictly_smaller(val_j, target_val, reverse, tracker):
                target_idx = j
                target_val = val_j

        if target_idx != i:
            arr[i], arr[target_idx] = arr[target_idx], arr[i]
            tracker.swaps += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Selection Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,
        swaps=tracker.swaps,
        movements=tracker.movements,
        stability="Unstable",
        time_complexity_best="O(n²)",
        time_complexity_avg="O(n²)",
        time_complexity_worst="O(n²)",
        space_complexity="O(1)",
        sorted_data=arr,
        is_compatible=True
    )




def merge_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
   
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    def _merge(left: int, mid: int, right: int, temp: List[Any]):
        i = left
        j = mid + 1
        k = left

        while i <= mid and j <= right:
            val_i = get_sort_key_value(arr[i], column)
            val_j = get_sort_key_value(arr[j], column)

            
            if is_smaller_or_equal(val_i, val_j, reverse, tracker):
                temp[k] = arr[i]
                tracker.movements += 1
                i += 1
            else:
                temp[k] = arr[j]
                tracker.movements += 1
                j += 1
            k += 1

        while i <= mid:
            temp[k] = arr[i]
            tracker.movements += 1
            i += 1
            k += 1

        while j <= right:
            temp[k] = arr[j]
            tracker.movements += 1
            j += 1
            k += 1

        for idx in range(left, right + 1):
            arr[idx] = temp[idx]
            tracker.movements += 1

    def _sort(left: int, right: int, temp: List[Any]):
        if left < right:
            mid = (left + right) // 2
            _sort(left, mid, temp)
            _sort(mid + 1, right, temp)
            _merge(left, mid, right, temp)

    if n > 1:
        temp_arr = [None] * n
        _sort(0, n - 1, temp_arr)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Merge Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,
        swaps=0, 
        movements=tracker.movements,
        stability="Stable",
        time_complexity_best="O(n log n)",
        time_complexity_avg="O(n log n)",
        time_complexity_worst="O(n log n)",
        space_complexity="O(n)",
        sorted_data=arr,
        is_compatible=True
    )




def bubble_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
    
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            val_a = get_sort_key_value(arr[j], column)
            val_b = get_sort_key_value(arr[j + 1], column)

            
            if is_strictly_smaller(val_b, val_a, reverse, tracker):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                tracker.swaps += 1
                swapped = True

        if not swapped:
            
            break

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Bubble Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,
        swaps=tracker.swaps,
        movements=tracker.movements,
        stability="Stable",
        time_complexity_best="O(n)",
        time_complexity_avg="O(n²)",
        time_complexity_worst="O(n²)",
        space_complexity="O(1)",
        sorted_data=arr,
        is_compatible=True
    )




def quick_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
    
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    def _median_of_three(low: int, high: int) -> int:
        mid = (low + high) // 2
        val_low = get_sort_key_value(arr[low], column)
        val_mid = get_sort_key_value(arr[mid], column)
        val_high = get_sort_key_value(arr[high], column)

        
        if is_strictly_smaller(val_mid, val_low, reverse, tracker):
            arr[low], arr[mid] = arr[mid], arr[low]
            tracker.swaps += 1
            val_low, val_mid = val_mid, val_low

        if is_strictly_smaller(val_high, val_low, reverse, tracker):
            arr[low], arr[high] = arr[high], arr[low]
            tracker.swaps += 1
            val_low, val_high = val_high, val_low

        if is_strictly_smaller(val_high, val_mid, reverse, tracker):
            arr[mid], arr[high] = arr[high], arr[mid]
            tracker.swaps += 1
            val_mid, val_high = val_high, val_mid

        return mid

    def _partition(low: int, high: int) -> int:
        pivot_idx = _median_of_three(low, high)
        
        arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
        tracker.swaps += 1
        pivot_val = get_sort_key_value(arr[high], column)

        i = low - 1
        for j in range(low, high):
            val_j = get_sort_key_value(arr[j], column)
            if is_smaller_or_equal(val_j, pivot_val, reverse, tracker):
                i += 1
                if i != j:
                    arr[i], arr[j] = arr[j], arr[i]
                    tracker.swaps += 1

        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        tracker.swaps += 1
        return i + 1

    
    if n > 1:
        stack = [(0, n - 1)]
        while stack:
            low, high = stack.pop()
            if low < high:
                p = _partition(low, high)
                
                if p - 1 - low < high - (p + 1):
                    stack.append((p + 1, high))
                    stack.append((low, p - 1))
                else:
                    stack.append((low, p - 1))
                    stack.append((p + 1, high))

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Quick Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,
        swaps=tracker.swaps,
        movements=tracker.movements,
        stability="Unstable",
        time_complexity_best="O(n log n)",
        time_complexity_avg="O(n log n)",
        time_complexity_worst="O(n²)",
        space_complexity="O(log n)",
        sorted_data=arr,
        is_compatible=True
    )




def counting_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
   
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    
    valid_records: List[Tuple[int, Dict[str, Any]]] = []
    null_records: List[Dict[str, Any]] = []

    for item in arr:
        raw_val = item.get(column)
        if raw_val is None or raw_val == "":
            null_records.append(item)
            continue
        try:
           
            if column == "price":
                int_val = int(round(float(raw_val) * 100))
            elif column == "rating":
                int_val = int(round(float(raw_val) * 10))
            else:
                int_val = int(float(raw_val))
            valid_records.append((int_val, item))
        except (ValueError, TypeError):
            null_records.append(item)

    if not valid_records:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SortResult(
            algorithm_name="Counting Sort",
            column=column,
            direction="desc" if reverse else "asc",
            dataset_size=n,
            elapsed_ms=elapsed_ms,
            comparisons=0,
            swaps=0,
            movements=0,
            stability="Stable",
            time_complexity_best="O(n + k)",
            time_complexity_avg="O(n + k)",
            time_complexity_worst="O(n + k)",
            space_complexity="O(n + k)",
            sorted_data=null_records,
            is_compatible=True
        )

    
    min_val = min(x[0] for x in valid_records)
    max_val = max(x[0] for x in valid_records)
    range_k = max_val - min_val + 1

    MAX_SAFE_K = 10_000_000 
    if range_k > MAX_SAFE_K:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SortResult(
            algorithm_name="Counting Sort",
            column=column,
            direction="desc" if reverse else "asc",
            dataset_size=n,
            elapsed_ms=elapsed_ms,
            comparisons=0,
            swaps=0,
            movements=0,
            stability="Stable",
            time_complexity_best="O(n + k)",
            time_complexity_avg="O(n + k)",
            time_complexity_worst="O(n + k)",
            space_complexity="O(n + k)",
            sorted_data=arr,
            is_compatible=False,
            error_message=f"Key range k={range_k:,} exceeds safe threshold for Counting Sort. Use Quick/Merge/Radix Sort."
        )

    count = [0] * range_k
    for val, _ in valid_records:
        count[val - min_val] += 1
        tracker.movements += 1

  
    if not reverse:
        for i in range(1, range_k):
            count[i] += count[i - 1]
    else:
        
        for i in range(range_k - 2, -1, -1):
            count[i] += count[i + 1]

    output = [None] * len(valid_records)
    
    for i in range(len(valid_records) - 1, -1, -1):
        val, record = valid_records[i]
        idx = val - min_val
        count[idx] -= 1
        output[count[idx]] = record
        tracker.movements += 1

    
    final_arr = output + null_records

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Counting Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,  
        swaps=0,
        movements=tracker.movements,
        stability="Stable",
        time_complexity_best="O(n + k)",
        time_complexity_avg="O(n + k)",
        time_complexity_worst="O(n + k)",
        space_complexity=f"O(n + k) [k={range_k}]",
        sorted_data=final_arr,
        is_compatible=True
    )




def bucket_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False, num_buckets: Optional[int] = None) -> SortResult:
    
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    valid_records: List[Tuple[float, Dict[str, Any]]] = []
    null_records: List[Dict[str, Any]] = []

    for item in arr:
        raw_val = item.get(column)
        if raw_val is None or raw_val == "":
            null_records.append(item)
            continue
        try:
            val = float(raw_val)
            valid_records.append((val, item))
        except (ValueError, TypeError):
            null_records.append(item)

    if not valid_records:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SortResult(
            algorithm_name="Bucket Sort",
            column=column,
            direction="desc" if reverse else "asc",
            dataset_size=n,
            elapsed_ms=elapsed_ms,
            comparisons=0,
            swaps=0,
            movements=0,
            stability="Stable",
            time_complexity_best="O(n + k)",
            time_complexity_avg="O(n + k)",
            time_complexity_worst="O(n²)",
            space_complexity="O(n + k)",
            sorted_data=null_records,
            is_compatible=True
        )

    min_val = min(x[0] for x in valid_records)
    max_val = max(x[0] for x in valid_records)

    
    k = num_buckets or max(10, min(100, int(math.isqrt(len(valid_records)))))
    buckets: List[List[Tuple[float, Dict[str, Any]]]] = [[] for _ in range(k)]

    val_range = max_val - min_val
    if val_range == 0.0:
        # All values identical
        for item in valid_records:
            buckets[0].append(item)
            tracker.movements += 1
    else:
        for val, rec in valid_records:
            
            b_idx = int(((val - min_val) / val_range) * (k - 1))
            b_idx = max(0, min(k - 1, b_idx))
            buckets[b_idx].append((val, rec))
            tracker.movements += 1

    
    sorted_valid: List[Dict[str, Any]] = []

    bucket_indices = range(k) if not reverse else range(k - 1, -1, -1)

    for b_idx in bucket_indices:
        b = buckets[b_idx]
        b_len = len(b)
        for i in range(1, b_len):
            key_entry = b[i]
            key_val = key_entry[0]
            j = i - 1
            while j >= 0:
                tracker.comparisons += 1
                condition = (key_val < b[j][0]) if not reverse else (key_val > b[j][0])
                if condition:
                    b[j + 1] = b[j]
                    tracker.movements += 1
                    j -= 1
                else:
                    break
            b[j + 1] = key_entry
            tracker.movements += 1

        for _, rec in b:
            sorted_valid.append(rec)
            tracker.movements += 1

    final_arr = sorted_valid + null_records

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Bucket Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=tracker.comparisons,
        swaps=0,
        movements=tracker.movements,
        stability="Stable",
        time_complexity_best="O(n + k)",
        time_complexity_avg="O(n + k)",
        time_complexity_worst="O(n²)",
        space_complexity=f"O(n + k) [k={k}]",
        sorted_data=final_arr,
        is_compatible=True
    )




def radix_sort(data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
    
    arr = [dict(item) for item in data]
    n = len(arr)
    tracker = MetricsTracker()
    start_time = time.perf_counter()

    valid_records: List[Tuple[int, Dict[str, Any]]] = []
    null_records: List[Dict[str, Any]] = []

    for item in arr:
        raw_val = item.get(column)
        if raw_val is None or raw_val == "":
            null_records.append(item)
            continue
        try:
            if column == "price":
                int_val = int(round(float(raw_val) * 100))
            elif column == "rating":
                int_val = int(round(float(raw_val) * 10))
            else:
                int_val = int(float(raw_val))
            valid_records.append((int_val, item))
        except (ValueError, TypeError):
            null_records.append(item)

    if not valid_records:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SortResult(
            algorithm_name="Radix Sort",
            column=column,
            direction="desc" if reverse else "asc",
            dataset_size=n,
            elapsed_ms=elapsed_ms,
            comparisons=0,
            swaps=0,
            movements=0,
            stability="Stable",
            time_complexity_best="O(d * (n + b))",
            time_complexity_avg="O(d * (n + b))",
            time_complexity_worst="O(d * (n + b))",
            space_complexity="O(n + b)",
            sorted_data=null_records,
            is_compatible=True
        )

    
    min_val = min(x[0] for x in valid_records)
    offset = -min_val if min_val < 0 else 0

    shifted_records = [(val + offset, rec) for val, rec in valid_records]
    max_shifted = max(x[0] for x in shifted_records)

    
    exp = 1
    RADIX = 10
    total_digits = 1 if max_shifted == 0 else int(math.log10(max_shifted)) + 1

    current_list = shifted_records
    while max_shifted // exp > 0:
        count = [0] * RADIX
        for val, _ in current_list:
            digit = (val // exp) % RADIX
            count[digit] += 1
            tracker.movements += 1

        for i in range(1, RADIX):
            count[i] += count[i - 1]

        output = [None] * len(current_list)
        for i in range(len(current_list) - 1, -1, -1):
            val, rec = current_list[i]
            digit = (val // exp) % RADIX
            count[digit] -= 1
            output[count[digit]] = (val, rec)
            tracker.movements += 1

        current_list = output
        exp *= RADIX

    
    if not reverse:
        sorted_valid = [rec for _, rec in current_list]
    else:
        
        sorted_valid = [current_list[i][1] for i in range(len(current_list) - 1, -1, -1)]

    final_arr = sorted_valid + null_records

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SortResult(
        algorithm_name="Radix Sort",
        column=column,
        direction="desc" if reverse else "asc",
        dataset_size=n,
        elapsed_ms=elapsed_ms,
        comparisons=0,
        swaps=0,
        movements=tracker.movements,
        stability="Stable",
        time_complexity_best=f"O(d*(n+b)) [d={total_digits}, b=10]",
        time_complexity_avg=f"O(d*(n+b)) [d={total_digits}, b=10]",
        time_complexity_worst=f"O(d*(n+b)) [d={total_digits}, b=10]",
        space_complexity="O(n + b)",
        sorted_data=final_arr,
        is_compatible=True
    )




SORTING_ALGORITHMS = {
    "Insertion Sort": insertion_sort,
    "Selection Sort": selection_sort,
    "Merge Sort": merge_sort,
    "Bubble Sort": bubble_sort,
    "Quick Sort": quick_sort,
    "Counting Sort": counting_sort,
    "Bucket Sort": bucket_sort,
    "Radix Sort": radix_sort,
}


COLUMN_COMPATIBILITY = {
    "Counting Sort": {"rating", "price", "rating_count", "metacritic_score", "game_id", "multiplayer"},
    "Bucket Sort": {"rating", "price", "rating_count", "metacritic_score", "game_id", "multiplayer"},
    "Radix Sort": {"rating", "price", "rating_count", "metacritic_score", "game_id", "multiplayer"},
}


def is_algorithm_compatible(algorithm_name: str, column: str) -> Tuple[bool, str]:
    
    if algorithm_name in COLUMN_COMPATIBILITY:
        allowed = COLUMN_COMPATIBILITY[algorithm_name]
        if column not in allowed:
            return False, f"{algorithm_name} requires numeric or integer keys. Column '{column}' contains text/dates."
    return True, "Compatible"


def execute_sort(algorithm_name: str, data: List[Dict[str, Any]], column: str, reverse: bool = False) -> SortResult:
    
    if algorithm_name not in SORTING_ALGORITHMS:
        raise ValueError(f"Unknown sorting algorithm: {algorithm_name}. Supported: {list(SORTING_ALGORITHMS.keys())}")

    compatible, reason = is_algorithm_compatible(algorithm_name, column)
    if not compatible:
        return SortResult(
            algorithm_name=algorithm_name,
            column=column,
            direction="desc" if reverse else "asc",
            dataset_size=len(data),
            elapsed_ms=0.0,
            comparisons=0,
            swaps=0,
            movements=0,
            stability="N/A",
            time_complexity_best="N/A",
            time_complexity_avg="N/A",
            time_complexity_worst="N/A",
            space_complexity="N/A",
            sorted_data=list(data),
            is_compatible=False,
            error_message=reason
        )

    algo_func = SORTING_ALGORITHMS[algorithm_name]
    return algo_func(data, column, reverse=reverse)

