"""
Two Sum Problem

Given an array of integers nums and an integer target, return indices of the 
two numbers such that they add up to target.

Constraints:
- Each input has exactly one solution
- You may not use the same element twice
- You can return the answer in any order
"""

def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Optimal Solution using Hash Map - O(n) time, O(n) space
    
    Algorithm:
    1. Create a hash map to store each number and its index
    2. For each number, calculate its complement (target - num)
    3. Check if the complement exists in the hash map
    4. If yes, return the indices; if no, add current number to hash map
    """
    num_to_index = {}  # Maps number -> index
    
    for i, num in enumerate(nums):
        complement = target - num
        
        # Check if complement exists in our map
        if complement in num_to_index:
            return [num_to_index[complement], i]
        
        # Store current number and its index
        num_to_index[num] = i
    
    return []  # No solution found (shouldn't happen per problem constraints)


def two_sum_brute_force(nums: list[int], target: int) -> list[int]:
    """
    Brute Force Solution - O(n²) time, O(1) space
    
    Check every pair of numbers.
    """
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []


# Test cases
if __name__ == "__main__":
    # Test Case 1
    nums1 = [2, 7, 11, 15]
    target1 = 9
    result1 = two_sum(nums1, target1)
    print(f"Test 1: nums={nums1}, target={target1}")
    print(f"  Result: {result1}")  # Expected: [0, 1] because nums[0] + nums[1] = 2 + 7 = 9
    print(f"  Verification: {nums1[result1[0]]} + {nums1[result1[1]]} = {nums1[result1[0]] + nums1[result1[1]]}")
    print()
    
    # Test Case 2
    nums2 = [3, 2, 4]
    target2 = 6
    result2 = two_sum(nums2, target2)
    print(f"Test 2: nums={nums2}, target={target2}")
    print(f"  Result: {result2}")  # Expected: [1, 2] because nums[1] + nums[2] = 2 + 4 = 6
    print(f"  Verification: {nums2[result2[0]]} + {nums2[result2[1]]} = {nums2[result2[0]] + nums2[result2[1]]}")
    print()
    
    # Test Case 3
    nums3 = [3, 3]
    target3 = 6
    result3 = two_sum(nums3, target3)
    print(f"Test 3: nums={nums3}, target={target3}")
    print(f"  Result: {result3}")  # Expected: [0, 1] because nums[0] + nums[1] = 3 + 3 = 6
    print(f"  Verification: {nums3[result3[0]]} + {nums3[result3[1]]} = {nums3[result3[0]] + nums3[result3[1]]}")
    print()
    
    # Test Case 4: Negative numbers
    nums4 = [-1, -2, -3, -4, -5]
    target4 = -8
    result4 = two_sum(nums4, target4)
    print(f"Test 4: nums={nums4}, target={target4}")
    print(f"  Result: {result4}")  # Expected: [2, 4] because nums[2] + nums[4] = -3 + -5 = -8
    print(f"  Verification: {nums4[result4[0]]} + {nums4[result4[1]]} = {nums4[result4[0]] + nums4[result4[1]]}")
