""" 
implement selection sort algorithm.
Selection sort is a algoorithm find the minimum value in the list and swap with the first index, then fined the next minimum value and swap with the second index, and so on until the list is sorted.

input: list of integers
output: sorted list of integers

example: [5, 2, 8, 1, 3]
expected output: [1, 2, 3, 5, 8]

pseudocode:
FUNCTION selection_sort(arr):
    arr_length = LENGTH(arr)
    
    FOR compare_index = 0 to arr_length - 1:
        minimum_value_index = compare_index
    
        FOR compere_index2 = (compare_index + 1) to arr_length:
            IF arr[minimum_value_index] > arr[compare_index2]:
                minimum_value_index = compere_index2
                
        SWAP arr[minimum_value_index] with arr[compare_index]
        
    RETURN arr
            
"""

def selection_sort(arr:int) -> list:
    """
    sort list by using selection sort

    Args:
        arr (int): list of integer

    Returns:
        list: sorted list of intedger
    """
    arr_length = len(arr)
    for compare_index in range(0, arr_length - 1):
        minimum_value_index = compare_index
        for compare_index2 in range(compare_index+1, arr_length):
            if arr[minimum_value_index] > arr[compare_index2]:
                minimum_value_index = compare_index2
                print(f"compare_index : {arr[compare_index]}, compare_index2 {arr[compare_index2]}")
        arr[minimum_value_index], arr[compare_index] = arr[compare_index], arr[minimum_value_index]
    return arr


if __name__ == "__main__":
    input_list = [5, 2, 8, 1, 3]
    sorted_list = selection_sort(input_list)
    print(sorted_list)  # Output: [1, 2, 3, 5, 8]
    
    
