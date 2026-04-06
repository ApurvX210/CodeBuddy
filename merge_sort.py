def merge_sort(arr):
    """
    Sorts an array using the merge sort algorithm.
    
    Parameters:
        arr (list): The list of elements to sort
        
    Returns:
        list: A new sorted list (merge sort is stable)
    """
    if len(arr) <= 1:
        return arr
    
    # Divide the array into two halves
    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]
    
    # Recursively sort both halves
    left_sorted = merge_sort(left)
    right_sorted = merge_sort(right)
    
    # Merge the sorted halves
    return merge(left_sorted, right_sorted)


def merge(left, right):
    """
    Merges two sorted lists into a single sorted list.
    
    Parameters:
        left (list): First sorted list
        right (list): Second sorted list
        
    Returns:
        list: Merged sorted list
    """
    result = []
    i = j = 0
    
    # Compare elements from both lists and merge
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Append remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result


if __name__ == "__main__":
    # Example usage
    test_array = [38, 27, 43, 3, 9, 82, 10]
    print("Original array:", test_array)
    sorted_array = merge_sort(test_array)
    print("Sorted array:", sorted_array)