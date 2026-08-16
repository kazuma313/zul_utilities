"""
implement bubble sort algorithm.
Bubble sort is a algorithm that compare value with his neighbor and swap if condition align with the output with needed.

input: list of integers
output: sorted list of integers

example: [5, 2, 8, 1, 3]
expected output: [1, 2, 3, 5, 8]

pseudocode:
FUNCTION bubble_sort(arr):
    arr_length = LENGTH(arr)
    set swapped = True
    REPEAT until no swaps are made:
        swapped = False
        arr_length = arr_length - 1
        FOR i = 0 to arr_length:
            IF arr[i] > arr[i + 1]:
                SWAP arr[i] and arr[i + 1]
                set swapped = True
    RETURN arr
"""

def bubble_sort(arr)-> list:
    """
    Sorts a list of integers using the bubble sort algorithm.

    Args:
        arr (list): A list of integers to be sorted.

    Returns:
        list: The sorted list of integers.
    """
    arr_length = len(arr)
    swapped= True
    while swapped:
        swapped= False
        arr_length -= 1
        for index in range(arr_length):
            if arr[index] > arr[index + 1]:
                arr[index], arr[index + 1] = arr[index + 1], arr[index]
                swapped = True
        if swapped == False:
            break
    return arr


if __name__ == "__main__":
    input_list = [5, 2, 8, 1, 3]
    sorted_list = bubble_sort(input_list)
    print(sorted_list)  # Output: [1, 2, 3, 5, 8]
    
    