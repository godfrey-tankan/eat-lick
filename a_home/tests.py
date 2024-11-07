def linear_search(arr,target):
    target_indexes = []
    for i in range(len(arr)):
        if arr[i] == target:
            target_indexes.append(i)
    if len(target_indexes)>0:
        return target_indexes
    else:
        return -1

arr = [2,4,6,8,8,10]
target =8
result = linear_search(arr,target)

if result !=-1:
    print(f"Element found at index {result}")
else:
    print("Element not found in the array")